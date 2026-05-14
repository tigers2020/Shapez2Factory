"""
Frozen dataclass DTOs (CANON ``03_data_schema_dto.md`` §19.1, §E, §16.3).

No solver behaviour; no v1 imports.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, NewType

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BBox,
    BlueprintCell,
    Coord,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    CommitReason,
    PlacementCommitState,
    RecoveryTrigger,
    RejectedReason,
    RollbackReason,
    SolverTerminationTier,
    SourceKind,
    TransportKind,
)

PlacementId = NewType("PlacementId", str)


@dataclass(frozen=True, slots=True)
class GridMask:
    """Immutable blueprint cell set (passable / blocked / occupied masks)."""

    cells: frozenset[BlueprintCell]

    @classmethod
    def from_coords(cls, coords: tuple[Coord, ...]) -> GridMask:
        return cls(frozenset(c.as_tuple() for c in coords))


@dataclass(frozen=True, slots=True)
class SolverRunLimits:
    max_reclaim_iterations: int = 0
    max_post_reclaim_pass3_reruns: int = 0
    max_total_recovery_attempts: int = 0
    max_validation_recovery_attempts: int = 0
    max_cascade_corrective_attempts: int = 0
    default_reclaim_gain_ratio_threshold: float = 0.0


@dataclass(frozen=True, slots=True)
class ReconstructionDTO:
    """STEP 1 outputs (mineable cells, shell, barriers)."""

    mineable_placement_cells: tuple[BlueprintCell, ...] = ()
    extraction_shell_cells: tuple[BlueprintCell, ...] = ()
    full_barrier_cells: tuple[BlueprintCell, ...] = ()


@dataclass(frozen=True, slots=True)
class RoutingStateSnapshot:
    """§19.1 ``routing_state`` slice (mutable orchestration mirrored as immutable DTO)."""

    trunk_seed_candidates: tuple[BlueprintCell, ...] = ()
    existing_trunk_cells_by_kind: dict[TransportKind, frozenset[BlueprintCell]] = field(
        default_factory=dict
    )
    fixed_output_stub_by_extractor: dict[str, BlueprintCell] = field(default_factory=dict)
    final_route_cells: tuple[BlueprintCell, ...] = ()
    hard_protected_corridors: tuple[BlueprintCell, ...] = ()
    soft_protected_corridors: tuple[BlueprintCell, ...] = ()


@dataclass(frozen=True, slots=True)
class MetricsSnapshot:
    internal_transport_count: int | None = None
    baseline_internal_transport_at_reclaim_entry: int | None = None
    optimization_baseline_internal_transport: int | None = None


@dataclass(frozen=True, slots=True)
class ExistingLayoutAnalysis:
    """STEP 0.5 read-only summary (§E); fields expand when analysis is implemented."""

    source_kind: SourceKind
    island_bbox: BBox
    issues: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class DecodedExistingLayoutContext:
    """Wrapper for decoded-island analysis (§E.10)."""

    analysis: ExistingLayoutAnalysis


@dataclass(frozen=True, slots=True)
class SolverRunContext:
    """Orchestration snapshot (§19.1)."""

    run_id: str
    reconstruction: ReconstructionDTO
    asteroid_signature: str | None = None
    limits: SolverRunLimits = field(default_factory=SolverRunLimits)
    routing_state: RoutingStateSnapshot = field(default_factory=RoutingStateSnapshot)
    metrics_snapshot: MetricsSnapshot = field(default_factory=MetricsSnapshot)
    placement_commit_by_id: dict[str, PlacementCommitState] = field(default_factory=dict)
    termination: SolverTerminationTier | None = None
    decoded_existing_layout: DecodedExistingLayoutContext | None = None


@dataclass(frozen=True, slots=True)
class OutputStub:
    """Extractor output stub cell (§3.1)."""

    extractor_placement_id: PlacementId
    cell: BlueprintCell
    transport_kind: TransportKind


@dataclass(frozen=True, slots=True)
class ExtractorPlacement:
    placement_id: PlacementId
    cell: BlueprintCell
    transport_kind: TransportKind


@dataclass(frozen=True, slots=True)
class ExtensionPlacement:
    placement_id: PlacementId
    anchor_extractor_id: PlacementId
    cell: BlueprintCell


@dataclass(frozen=True, slots=True)
class PlacementBundle:
    extractor: ExtractorPlacement
    extensions: tuple[ExtensionPlacement, ...]
    output_stub: OutputStub


@dataclass(frozen=True, slots=True)
class RoutePath:
    """Ordered route geometry for one logical path."""

    transport_kind: TransportKind
    cells: tuple[BlueprintCell, ...]


@dataclass(frozen=True, slots=True)
class RoutingFailure:
    """§19.1 ``routing_failures`` row (STEP 4)."""

    stub_cell: BlueprintCell
    extractor_id: str | None
    recovery_trigger: RecoveryTrigger | None
    attempt_count: int
    final_state: PlacementCommitState | str | None
    last_error: str | None = None


@dataclass(frozen=True, slots=True)
class TrunkLoadSummary:
    """§3.6 aggregate trace; kind-separated edge maps (keys are implementation-defined)."""

    belt_edge_totals: dict[str, float] = field(default_factory=dict)
    pipe_edge_totals: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Pass1Result:
    """STEP 2 Pass1 (§7)."""

    placements: tuple[PlacementBundle, ...] = ()
    occupied_cells: tuple[BlueprintCell, ...] = ()
    beam_trace: tuple[dict[str, Any], ...] | None = None


@dataclass(frozen=True, slots=True)
class Pass2Result:
    """STEP 3 Pass2 provisional placements (§8)."""

    provisional_placements: tuple[PlacementBundle, ...] = ()
    blocked_cells_delta: tuple[BlueprintCell, ...] = ()


@dataclass(frozen=True, slots=True)
class Step4RoutingResult:
    """STEP 4 routing (§9); replaces skeleton ``RoutingResult``."""

    routes_by_extractor: dict[str, RoutePath] = field(default_factory=dict)
    trunk_load: TrunkLoadSummary = field(default_factory=TrunkLoadSummary)
    routing_failures: tuple[RoutingFailure, ...] = ()


@dataclass(frozen=True, slots=True)
class FinalValidationReport:
    """STEP 9 assertion summary (§15); geometry + quarantine boundary."""

    geometry_ok: bool
    connectivity_ok: bool
    quarantined_count: int


@dataclass(frozen=True, slots=True)
class TraceEvent:
    """§16.3 trace_event decision slice + identifiers (full replay payload grows elsewhere)."""

    run_id: str
    phase: str
    step_index: int
    event_type: str
    committed: bool
    commit_reason: CommitReason | None
    rejected_reason: RejectedReason | None
    rollback_reason: RollbackReason | None = None
    recovery_trigger: RecoveryTrigger | None = None
    computation_cycle: int | None = None

    def __post_init__(self) -> None:
        from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import (
            trace_semantics,
        )

        trace_semantics.validate_trace_decision_semantics(
            committed=self.committed,
            commit_reason=self.commit_reason,
            rejected_reason=self.rejected_reason,
            rollback_reason=self.rollback_reason,
        )


# Back-compat alias for in-repo skeleton callers (prefer ``Step4RoutingResult``).
RoutingResult = Step4RoutingResult
