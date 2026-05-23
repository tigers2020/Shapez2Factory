"""Build RTTP replay descriptions and overlay snapshots at record time (3B-S-2).

Pure functions only — no replay reads, no solver branching.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    BundleCandidate,
    CandidateGenerationResult,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import CommitResult
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


@dataclass(frozen=True, slots=True)
class RttpReplayPayload:
    description: str
    cell_overlay_json: dict[str, Any]


def overlay_cells_from_coords(
    coords: tuple[Coord, ...] | frozenset[Coord],
    *,
    kind: str,
    transport: str = "",
) -> list[dict[str, Any]]:
    ordered = sorted(coords, key=lambda c: (c[1], c[0]))
    return [
        {
            "x": int(x),
            "y": int(y),
            "kind": kind,
            "transport": transport,
        }
        for x, y in ordered
    ]


def _cell_overlay(cells: list[dict[str, Any]]) -> dict[str, Any]:
    return {"cells": cells}


def _transport_wire(kind: TransportKind) -> str:
    return str(kind.value)


def build_pipeline_start_replay_payload(skeleton: RttpSkeleton) -> RttpReplayPayload:
    trunk_cells = overlay_cells_from_coords(
        skeleton.trunk_mask_cells,
        kind="route_domain.preferred",
    )
    lift_cells = overlay_cells_from_coords(
        frozenset(col.platform_coord for col in skeleton.lift_columns),
        kind="probe.start",
    )
    cells = trunk_cells + lift_cells
    description = "\n".join(
        [
            "RTTP route domain snapshot.",
            f"skeleton_id: {skeleton.skeleton_id}",
            f"trunk_mask_cell_count: {len(skeleton.trunk_mask_cells)}",
            f"lift_column_count: {len(skeleton.lift_columns)}",
            f"capacity_goals: {skeleton.capacity_goals}",
        ]
    )
    return RttpReplayPayload(description=description, cell_overlay_json=_cell_overlay(cells))


def build_candidates_replay_payload(generation: CandidateGenerationResult) -> RttpReplayPayload:
    normal = generation.normal_candidates
    rejected = generation.rejected_candidates
    cells: list[dict[str, Any]] = []
    for candidate in normal:
        cells.extend(
            overlay_cells_from_coords(
                candidate.occupied_cells,
                kind="candidate.bundle",
                transport=_transport_wire(candidate.transport_kind),
            )
        )
    for rej in rejected:
        cells.append(
            {
                "x": int(rej.anchor_coord[0]),
                "y": int(rej.anchor_coord[1]),
                "kind": "candidate.rejected",
                "transport": "",
            }
        )
    sample_ids = ", ".join(c.candidate_id for c in normal[:5])
    description = "\n".join(
        [
            "RTTP candidate pool snapshot.",
            f"normal_count: {len(normal)}",
            f"rejected_count: {len(rejected)}",
            f"sample_candidate_ids: {sample_ids or '—'}",
        ]
    )
    return RttpReplayPayload(description=description, cell_overlay_json=_cell_overlay(cells))


def build_selection_replay_payload(
    genome: PlacementGenome,
    normal_candidates: tuple[BundleCandidate, ...],
) -> RttpReplayPayload:
    by_id = {c.candidate_id: c for c in normal_candidates}
    cells: list[dict[str, Any]] = []
    for cid in genome.commit_order:
        candidate = by_id.get(cid)
        if candidate is None:
            continue
        cells.extend(
            overlay_cells_from_coords(
                candidate.occupied_cells,
                kind="genome.selected",
                transport=_transport_wire(candidate.transport_kind),
            )
        )
    order_text = ", ".join(genome.commit_order)
    description = "\n".join(
        [
            "RTTP genome selection snapshot.",
            f"commit_order: {order_text or '—'}",
            f"selected_count: {len(genome.commit_order)}",
        ]
    )
    return RttpReplayPayload(description=description, cell_overlay_json=_cell_overlay(cells))


def build_commit_replay_payload(
    commit_result: CommitResult,
    *,
    validation_passed: bool,
    normal_count: int,
    commit_order: tuple[str, ...],
) -> RttpReplayPayload:
    route_cells = overlay_cells_from_coords(
        commit_result.reserved_route_cells,
        kind="route.committed_path",
    )
    conflict_lines = [f"- {c.candidate_id}: {c.reason.value}" for c in commit_result.conflicts[:8]]
    description = "\n".join(
        [
            "RTTP commit domain snapshot.",
            f"committed_ids: {', '.join(commit_result.committed_ids) or '—'}",
            f"commit_order: {', '.join(commit_order) or '—'}",
            f"validation_passed: {validation_passed}",
            f"conflict_count: {len(commit_result.conflicts)}",
            f"normal_count: {normal_count}",
            f"domain_version: {commit_result.domain_version}",
            *(["blocked_by:"] + conflict_lines if conflict_lines else []),
        ]
    )
    return RttpReplayPayload(description=description, cell_overlay_json=_cell_overlay(route_cells))


__all__ = [
    "RttpReplayPayload",
    "build_candidates_replay_payload",
    "build_commit_replay_payload",
    "build_pipeline_start_replay_payload",
    "build_selection_replay_payload",
    "overlay_cells_from_coords",
]
