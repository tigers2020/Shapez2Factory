"""Unit tests for L3 replay pool logical windows and cell-budget sub-split."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.layer03_overlay_cells import overlay_cell_count_for_candidate
from django_apps.asteroid_lab.replay.layer03_pool_windowing import build_pool_probe_window_plans
from django_apps.asteroid_lab.replay.replay_limits import (
    LAYER03_REPLAY_MAX_POOL_PREVIEW_WINDOWS,
    MAX_LAB_REPLAY_TIMELINE_CELLS_PER_FRAME,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    succeeded_probe_at,
)


def _entry(cid: str, *, cell_count: int):
    i = int(cid)
    anchor = (i * 3, 0)
    mining = frozenset((anchor[0] + j, anchor[1]) for j in range(cell_count))
    stub = (anchor[0] + cell_count, anchor[1])
    goal = (stub[0] + 1, stub[1])
    return succeeded_probe_at(
        anchor,
        mining=mining,
        transport=frozenset({stub}),
        goal=goal,
    )


def test_overlay_cell_count_for_candidate_counts_miner_and_path() -> None:
    entry = _entry("0", cell_count=3)
    assert overlay_cell_count_for_candidate(entry) == 6


def test_build_pool_probe_window_plans_partitions_candidate_ids() -> None:
    pool = tuple(_entry(str(i), cell_count=1) for i in range(719))
    plans = build_pool_probe_window_plans(
        replay_pool_candidates=pool,
        max_logical_windows=LAYER03_REPLAY_MAX_POOL_PREVIEW_WINDOWS,
        max_cells_per_frame=MAX_LAB_REPLAY_TIMELINE_CELLS_PER_FRAME,
    )
    seen_ids: list[str] = []
    for plan in plans:
        assert plan.candidate_ids == tuple(e.candidate.candidate_id for e in plan.candidates)
        seen_ids.extend(plan.candidate_ids)
    expected_ids = [entry.candidate.candidate_id for entry in pool]
    assert seen_ids == expected_ids
    assert len(seen_ids) == len(set(seen_ids))


def test_build_pool_probe_window_plans_empty_pool() -> None:
    assert build_pool_probe_window_plans(replay_pool_candidates=()) == ()


def test_subsplit_when_logical_window_exceeds_cell_budget() -> None:
    heavy = tuple(_entry(str(i), cell_count=120) for i in range(5))
    plans = build_pool_probe_window_plans(
        replay_pool_candidates=heavy,
        max_logical_windows=1,
        max_cells_per_frame=200,
    )
    assert len(plans) > 1
    assert all(p.logical_window_index == 1 for p in plans)
    assert [cid for p in plans for cid in p.candidate_ids] == [
        e.candidate.candidate_id for e in heavy
    ]
