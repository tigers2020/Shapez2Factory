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
from django_apps.asteroid_lab.optimization.commit.incremental_macro_commit import MacroCommitResult
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.optimization.macros.macro_compiler import MacroGenerationResult
from django_apps.asteroid_lab.optimization.macros.macro_dtos import MacroBundleCandidate
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton
from django_apps.asteroid_lab.snapshots.grid_contract import neighbors4


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


def _coord_adjacent_to_inner(coord: Coord, inner_cells: frozenset[Coord]) -> bool:
    if not inner_cells:
        return False
    return any(neighbor in inner_cells for neighbor in neighbors4(coord))


def skeleton_lift_platform_coords(skeleton: RttpSkeleton) -> frozenset[Coord]:
    """Lift platforms on the mineable rim (4-neighbor of inner), excluding void outliers."""

    return frozenset(
        column.platform_coord
        for column in skeleton.lift_columns
        if column.platform_coord in skeleton.inner_cells
        or _coord_adjacent_to_inner(column.platform_coord, skeleton.inner_cells)
    )


def skeleton_route_visible_domain(skeleton: RttpSkeleton) -> frozenset[Coord]:
    """Mineable footprint cells where RTTP route-domain overlays may be drawn."""

    return frozenset(skeleton.inner_cells | skeleton_lift_platform_coords(skeleton))


def coords_in_route_visible_domain(
    coords: tuple[Coord, ...] | frozenset[Coord],
    skeleton: RttpSkeleton,
) -> frozenset[Coord]:
    visible = skeleton_route_visible_domain(skeleton)
    return frozenset(c for c in coords if c in visible)


def build_pipeline_start_replay_payload(skeleton: RttpSkeleton) -> RttpReplayPayload:
    trunk_coords = coords_in_route_visible_domain(skeleton.trunk_mask_cells, skeleton)
    lift_coords = skeleton_lift_platform_coords(skeleton)
    trunk_cells = overlay_cells_from_coords(
        trunk_coords,
        kind="route_domain.preferred",
    )
    lift_cells = overlay_cells_from_coords(
        lift_coords,
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


def build_candidates_replay_payload(
    generation: CandidateGenerationResult,
    *,
    macro_generation: MacroGenerationResult | None = None,
    macro_normal: tuple[MacroBundleCandidate, ...] | None = None,
    skeleton: RttpSkeleton | None = None,
) -> RttpReplayPayload:
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
    if macro_normal:
        for row in macro_normal:
            combined = row.macro.combined_occupied_cells
            shared_lift = row.macro.shared_lift_stub_plan.reserved_route_cells
            if skeleton is not None:
                combined = coords_in_route_visible_domain(combined, skeleton)
                shared_lift = coords_in_route_visible_domain(shared_lift, skeleton)
            cells.extend(
                overlay_cells_from_coords(
                    combined,
                    kind="macro.combined_footprint",
                )
            )
            cells.extend(
                overlay_cells_from_coords(
                    shared_lift,
                    kind="macro.shared_lift",
                )
            )
    sample_ids = ", ".join(c.candidate_id for c in normal[:5])
    lines = [
        "RTTP candidate pool snapshot.",
        f"normal_count: {len(normal)}",
        f"rejected_count: {len(rejected)}",
        f"sample_candidate_ids: {sample_ids or '—'}",
    ]
    if macro_generation is not None:
        lines.extend(
            [
                f"macro_normal_count: {len(macro_normal or ())}",
                f"macro_rejected_count: {len(macro_generation.macro_rejected)}",
                f"child_normal_count: {len(normal)}",
            ]
        )
    description = "\n".join(lines)
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


def build_macro_selection_replay_payload(
    genome: PlacementGenome,
    macro_normal: tuple[MacroBundleCandidate, ...],
) -> RttpReplayPayload:
    by_id = {row.macro_id: row for row in macro_normal}
    cells: list[dict[str, Any]] = []
    for macro_id in genome.commit_order:
        row = by_id.get(macro_id)
        if row is None:
            continue
        for child in row.macro.children:
            cells.append(
                {
                    "x": int(child.anchor_coord[0]),
                    "y": int(child.anchor_coord[1]),
                    "kind": "macro.child_anchor",
                    "transport": _transport_wire(child.transport_kind),
                }
            )
    order_text = ", ".join(genome.commit_order)
    description = "\n".join(
        [
            "RTTP macro genome selection snapshot.",
            f"commit_order: {order_text or '—'}",
            f"macro_count_selected: {len(genome.commit_order)}",
        ]
    )
    return RttpReplayPayload(description=description, cell_overlay_json=_cell_overlay(cells))


def build_macro_commit_replay_payload(
    macro_commit: MacroCommitResult,
    *,
    validation_passed: bool,
    normal_count: int,
    commit_order: tuple[str, ...],
    macro_normal: tuple[MacroBundleCandidate, ...],
) -> RttpReplayPayload:
    route_cells = overlay_cells_from_coords(
        macro_commit.reserved_route_cells,
        kind="route.committed_path",
    )
    for row in macro_normal:
        if row.macro_id not in macro_commit.committed_macro_ids:
            continue
        route_cells.extend(
            overlay_cells_from_coords(
                row.macro.shared_lift_stub_plan.reserved_route_cells,
                kind="macro.shared_lift",
            )
        )
    conflict_lines = [f"- {c.candidate_id}: {c.reason.value}" for c in macro_commit.conflicts[:8]]
    description = "\n".join(
        [
            "RTTP macro commit domain snapshot.",
            f"committed_macro_ids: {', '.join(macro_commit.committed_macro_ids) or '—'}",
            f"committed_child_ids: {', '.join(macro_commit.committed_child_ids) or '—'}",
            f"commit_order: {', '.join(commit_order) or '—'}",
            f"validation_passed: {validation_passed}",
            f"conflict_count: {len(macro_commit.conflicts)}",
            f"normal_count: {normal_count}",
            f"domain_version: {macro_commit.domain_version}",
            *(["blocked_by:"] + conflict_lines if conflict_lines else []),
        ]
    )
    return RttpReplayPayload(description=description, cell_overlay_json=_cell_overlay(route_cells))


__all__ = [
    "RttpReplayPayload",
    "build_candidates_replay_payload",
    "build_commit_replay_payload",
    "build_macro_commit_replay_payload",
    "build_macro_selection_replay_payload",
    "build_pipeline_start_replay_payload",
    "build_selection_replay_payload",
    "coords_in_route_visible_domain",
    "overlay_cells_from_coords",
    "skeleton_lift_platform_coords",
    "skeleton_route_visible_domain",
]
