"""Layer 04 rim bundle placement result contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from django_apps.asteroid_lab.layers.contracts.placement_state import PlacementCommitState
from django_apps.asteroid_lab.layers.contracts.provisional_overlay import ProvisionalLayoutOverlay
from django_apps.asteroid_lab.layers.contracts.transport_kind import ResourceKind, TransportKind
from django_apps.asteroid_lab.services.dto import ReplayFrameAppendDTO
from django_apps.asteroid_lab.snapshots.grid_contract import Coord


class RimPlacementRejectReason(StrEnum):
    PHYSICAL_OVERLAP = "PHYSICAL_OVERLAP"
    BUDGET_INTERRUPTED = "BUDGET_INTERRUPTED"
    NON_SUCCEEDED_PROBE = "NON_SUCCEEDED_PROBE"


@dataclass(frozen=True, slots=True)
class RimBundlePlacement:
    candidate_id: str
    placement_id: str
    equivalence_key: str
    gene_key: str
    anchor_coord: Coord
    transport_kind: TransportKind
    resource_kind: ResourceKind
    occupied_cells: frozenset[Coord]
    extractor_cells: frozenset[Coord]
    extension_cells: frozenset[Coord]
    output_stub_cells: frozenset[Coord]
    route_probe_goal_cells: frozenset[Coord]
    placement_state: PlacementCommitState
    intrinsic_priority_rank: int

    def __post_init__(self) -> None:
        if self.placement_state is not PlacementCommitState.PROVISIONAL_PLACED:
            msg = "Layer 04 placements must use PROVISIONAL_PLACED only"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class RimPlacementRejection:
    candidate_id: str
    equivalence_key: str
    reason: RimPlacementRejectReason
    conflicting_candidate_id: str | None = None
    conflicting_cells: frozenset[Coord] = frozenset()


@dataclass(frozen=True, slots=True)
class Layer04RimPlacementResult:
    """Runtime replay frames are built by ``replay.solver_runtime_assembler`` only."""

    selected_placements: tuple[RimBundlePlacement, ...]
    rejected_candidates: tuple[RimPlacementRejection, ...]
    selected_count: int
    rejected_overlap_count: int
    rejected_budget_count: int
    provisional_overlay: ProvisionalLayoutOverlay
    replay_frames: tuple[ReplayFrameAppendDTO, ...]  # deprecated v1: always () in production

    def __post_init__(self) -> None:
        if self.selected_count != len(self.selected_placements):
            msg = "selected_count must equal len(selected_placements)"
            raise ValueError(msg)
        overlap = sum(
            1
            for r in self.rejected_candidates
            if r.reason is RimPlacementRejectReason.PHYSICAL_OVERLAP
        )
        if self.rejected_overlap_count != overlap:
            msg = "rejected_overlap_count must match PHYSICAL_OVERLAP rejections"
            raise ValueError(msg)
        budget = sum(
            1
            for r in self.rejected_candidates
            if r.reason is RimPlacementRejectReason.BUDGET_INTERRUPTED
        )
        if self.rejected_budget_count != budget:
            msg = "rejected_budget_count must match BUDGET_INTERRUPTED rejections"
            raise ValueError(msg)


def build_layer04_rim_placement_result(
    *,
    selected_placements: tuple[RimBundlePlacement, ...],
    rejected_candidates: tuple[RimPlacementRejection, ...],
    provisional_overlay: ProvisionalLayoutOverlay,
    replay_frames: tuple[ReplayFrameAppendDTO, ...],
) -> Layer04RimPlacementResult:
    overlap = sum(
        1 for r in rejected_candidates if r.reason is RimPlacementRejectReason.PHYSICAL_OVERLAP
    )
    budget = sum(
        1 for r in rejected_candidates if r.reason is RimPlacementRejectReason.BUDGET_INTERRUPTED
    )
    return Layer04RimPlacementResult(
        selected_placements=selected_placements,
        rejected_candidates=rejected_candidates,
        selected_count=len(selected_placements),
        rejected_overlap_count=overlap,
        rejected_budget_count=budget,
        provisional_overlay=provisional_overlay,
        replay_frames=replay_frames,
    )


__all__ = [
    "Layer04RimPlacementResult",
    "RimBundlePlacement",
    "RimPlacementRejectReason",
    "RimPlacementRejection",
    "build_layer04_rim_placement_result",
]
