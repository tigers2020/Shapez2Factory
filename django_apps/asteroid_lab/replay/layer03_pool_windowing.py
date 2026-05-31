"""L3 replay pool logical windows and cell-budget physical sub-split (projection only)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from django_apps.asteroid_lab.replay.layer03_overlay_cells import overlay_cell_count_for_candidate
from django_apps.asteroid_lab.replay.replay_limits import (
    LAYER03_REPLAY_MAX_POOL_PREVIEW_WINDOWS,
    MAX_LAB_REPLAY_TIMELINE_CELLS_PER_FRAME,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    RouteProbedBundleCandidate,
)


@dataclass(frozen=True, slots=True)
class PoolProbeWindowPlan:
    logical_window_index: int
    logical_window_count: int
    physical_subwindow_index: int
    physical_subwindow_count: int
    candidate_start_index: int
    candidate_end_index: int
    chunk_size: int
    candidates: tuple[RouteProbedBundleCandidate, ...]
    candidate_ids: tuple[str, ...]


def build_pool_probe_window_plans(
    *,
    replay_pool_candidates: tuple[RouteProbedBundleCandidate, ...],
    max_logical_windows: int = LAYER03_REPLAY_MAX_POOL_PREVIEW_WINDOWS,
    max_cells_per_frame: int = MAX_LAB_REPLAY_TIMELINE_CELLS_PER_FRAME,
) -> tuple[PoolProbeWindowPlan, ...]:
    n = len(replay_pool_candidates)
    if n == 0:
        return ()
    logical_window_count = min(max_logical_windows, n)
    chunk_size = math.ceil(n / logical_window_count)
    plans: list[PoolProbeWindowPlan] = []
    for window_idx in range(logical_window_count):
        start = window_idx * chunk_size
        end = min(start + chunk_size, n)
        if start >= end:
            continue
        chunk = replay_pool_candidates[start:end]
        sub_chunks = _split_chunk_for_cell_budget(chunk, max_cells_per_frame=max_cells_per_frame)
        sub_count = len(sub_chunks)
        offset = start
        for sub_i, sub in enumerate(sub_chunks, start=1):
            sub_start_index = offset + 1
            sub_end_index = offset + len(sub)
            offset = sub_end_index
            plans.append(
                PoolProbeWindowPlan(
                    logical_window_index=window_idx + 1,
                    logical_window_count=logical_window_count,
                    physical_subwindow_index=sub_i,
                    physical_subwindow_count=sub_count,
                    candidate_start_index=sub_start_index,
                    candidate_end_index=sub_end_index,
                    chunk_size=chunk_size,
                    candidates=sub,
                    candidate_ids=tuple(entry.candidate.candidate_id for entry in sub),
                )
            )
    return tuple(plans)


def _split_chunk_for_cell_budget(
    chunk: tuple[RouteProbedBundleCandidate, ...],
    *,
    max_cells_per_frame: int,
) -> list[tuple[RouteProbedBundleCandidate, ...]]:
    if not chunk:
        return []
    batches: list[list[RouteProbedBundleCandidate]] = [[]]
    cell_totals = [0]
    for entry in chunk:
        need = overlay_cell_count_for_candidate(entry)
        if batches[-1] and cell_totals[-1] + need > max_cells_per_frame:
            batches.append([])
            cell_totals.append(0)
        batches[-1].append(entry)
        cell_totals[-1] += need
    return [tuple(batch) for batch in batches]


__all__ = [
    "PoolProbeWindowPlan",
    "build_pool_probe_window_plans",
]
