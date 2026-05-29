"""Layer 04 rim bundle placement result contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from django_apps.asteroid_lab.layers.contracts.candidates import BundlePlacement
from django_apps.asteroid_lab.layers.contracts.placement_state import PlacementCommitState
from django_apps.asteroid_lab.layers.contracts.provisional_overlay import ProvisionalLayoutOverlay
from django_apps.asteroid_lab.layers.contracts.transport_kind import ResourceKind, TransportKind
from django_apps.asteroid_lab.services.dto import ReplayFrameAppendDTO
from django_apps.asteroid_lab.snapshots.grid_contract import Coord


class RimPlacementRejectReason(StrEnum):
    PHYSICAL_OVERLAP = "PHYSICAL_OVERLAP"
    BUDGET_INTERRUPTED = "BUDGET_INTERRUPTED"
    NON_SUCCEEDED_PROBE = "NON_SUCCEEDED_PROBE"


class RimSelectionStrategy(StrEnum):
    EXACT_PACK = "EXACT_PACK"
    GREEDY_FALLBACK = "GREEDY_FALLBACK"


class RimPackingRejectionKind(StrEnum):
    PACKING_SET_LOSER = "PACKING_SET_LOSER"
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
    cell_placements: tuple[BundlePlacement, ...] = ()
    probed_route_path_cells: tuple[Coord, ...] = ()

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
    rejected_candidate_id: str = ""
    rejected_output_dir: str = ""
    rejected_mining_cell_count: int = 0
    conflicting_winner_candidate_id: str | None = None
    conflicting_winner_output_dir: str | None = None
    conflicting_winner_mining_cell_count: int | None = None
    winner_selected_due_to_higher_mining_gain: bool = False
    overlap_tiebreak_step: str | None = None
    packing_component_id: str | None = None
    packing_rejection_kind: RimPackingRejectionKind | None = None
    winner_selected_due_to_higher_set_score: bool | None = None

    def __post_init__(self) -> None:
        if not self.rejected_candidate_id:
            object.__setattr__(self, "rejected_candidate_id", self.candidate_id)
        if (
            self.conflicting_winner_candidate_id is not None
            and self.conflicting_candidate_id is not None
            and self.conflicting_winner_candidate_id != self.conflicting_candidate_id
        ):
            msg = "conflicting_winner_candidate_id must mirror conflicting_candidate_id"
            raise ValueError(msg)
        if (
            self.conflicting_winner_candidate_id is None
            and self.conflicting_candidate_id is not None
        ):
            object.__setattr__(
                self,
                "conflicting_winner_candidate_id",
                self.conflicting_candidate_id,
            )


@dataclass(frozen=True, slots=True)
class RimComponentSelectionRecord:
    component_id: str
    component_sort_key: tuple[int, int, str]
    node_count: int
    selection_strategy: RimSelectionStrategy
    selected_candidate_ids: tuple[str, ...]
    materialized_candidate_ids: tuple[str, ...]
    total_effective_mining_gain: int
    selected_count: int


@dataclass(frozen=True, slots=True)
class Layer04PackingObservability:
    greedy_baseline_total_gain: int | None
    selected_total_gain: int
    greedy_baseline_throughput_factor_sum: int | None = None
    selected_throughput_factor_sum: int | None = None
    greedy_baseline_skipped_reason: str | None = None
    budget_limited: bool = False
    budget_interrupted_component_id: str | None = None
    component_records: tuple[RimComponentSelectionRecord, ...] = ()


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
    packing_observability: Layer04PackingObservability | None = None

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
    packing_observability: Layer04PackingObservability | None = None,
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
        packing_observability=packing_observability,
    )


__all__ = [
    "Layer04PackingObservability",
    "Layer04RimPlacementResult",
    "RimBundlePlacement",
    "RimComponentSelectionRecord",
    "RimPackingRejectionKind",
    "RimPlacementRejectReason",
    "RimPlacementRejection",
    "RimSelectionStrategy",
    "build_layer04_rim_placement_result",
]
