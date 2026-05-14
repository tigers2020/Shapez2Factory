"""
Frozen dataclass DTOs (CANON ``03_data_schema_dto.md`` §19.1, §E, §16.3).

No solver behaviour; no v1 imports.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Literal, NewType

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BBox,
    BlueprintCell,
    Coord,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    CommitReason,
    EquipmentKind,
    ExistingLayoutIssueCode,
    ExistingLayoutIssueSeverity,
    MineableEmptyCause,
    PlacementCommitState,
    RecoveryTrigger,
    RejectedReason,
    RollbackReason,
    SolverTerminationTier,
    SourceKind,
    TransportComponentStatus,
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
    """STEP 1 outputs (§6): shell, barriers, transport split, inferred interior, mineable.

    ``mineable_placement_cells`` is the restored asteroid mining region for placement:
    extraction shell ∪ inferred interior **mining-region** cells (inside the closed
    shell, not arbitrary off-map void) ∪ existing extractor/miner footprint ∪ existing
    extension footprint, minus **permanent** obstacles (belt, pipe, platform, other solid
    layout kinds). ``extractor_cells`` / ``extension_cells`` keep blueprint snapshots;
    ``equipment_footprint_mineable_cells`` is their sorted union (prior mineable evidence).
    ``full_barrier_cells`` remains the union of all occupied blueprint coordinates (not
    equivalent to permanent mineable blockers).
    """

    mineable_placement_cells: tuple[BlueprintCell, ...] = ()
    extraction_shell_cells: tuple[BlueprintCell, ...] = ()
    full_barrier_cells: tuple[BlueprintCell, ...] = ()
    belt_cells: tuple[BlueprintCell, ...] = ()
    pipe_cells: tuple[BlueprintCell, ...] = ()
    extractor_cells: tuple[BlueprintCell, ...] = ()
    extension_cells: tuple[BlueprintCell, ...] = ()
    equipment_footprint_mineable_cells: tuple[BlueprintCell, ...] = ()
    interior_patch_cells: tuple[BlueprintCell, ...] = ()
    asteroid_bbox: BBox | None = None
    external_margin: int = 0
    external_margin_bbox_source: Literal["mineable", "shell", "none"] = "none"


# Alias for CANON §6 naming (``SolverRunContext.reconstruction`` keeps field type).
ReconstructionResult = ReconstructionDTO


@dataclass(frozen=True, slots=True)
class DuplicateCoordSampleDTO:
    """One coordinate with multiple blueprint entries (overlay / duplicate ``T`` rows)."""

    cell: BlueprintCell
    t_values: tuple[str | None, ...]
    has_shell: bool
    has_blocking: bool
    blocking_kinds: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReconstructionDiagnosisDTO:
    """Read-only STEP 1 reconstruction diagnostics; must not drive solver or placement input."""

    total_entries: int = 0
    unique_coord_count: int = 0
    duplicate_coord_count: int = 0

    extraction_shell_count: int = 0
    interior_patch_count: int = 0
    mineable_placement_count: int = 0

    belt_count: int = 0
    pipe_count: int = 0
    extractor_count: int = 0
    extension_count: int = 0
    platform_count: int = 0
    other_barrier_count: int = 0

    coords_with_shell_and_blocking_count: int = 0
    coords_with_shell_and_belt_count: int = 0
    coords_with_shell_and_pipe_count: int = 0
    coords_with_shell_and_extractor_count: int = 0
    coords_with_shell_and_extension_count: int = 0

    candidate_before_blocking_count: int = 0
    blocked_candidate_count: int = 0

    unrecognized_t_counts: tuple[tuple[str, int], ...] = ()
    asteroid_like_unrecognized_t_counts: tuple[tuple[str, int], ...] = ()

    duplicate_coord_samples: tuple[DuplicateCoordSampleDTO, ...] = ()

    preview_timeline_frame_count: int | None = None
    preview_timeline_frame_ids_sample: tuple[str, ...] = ()

    primary_cause: MineableEmptyCause = MineableEmptyCause.UNKNOWN
    note: str = ""


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
class DecodedBlueprintDocument:
    """Immutable handle to STEP 0 decoded JSON (shallow read-only view via ``MappingProxyType``)."""

    _root: dict[str, Any]

    @property
    def document(self) -> Mapping[str, Any]:
        return MappingProxyType(self._root)

    def as_mutable_dict(self) -> dict[str, Any]:
        """Shallow copy for callers that need a mutable ``dict``."""

        return dict(self._root)


@dataclass(frozen=True, slots=True)
class TransportComponentSummary:
    """One same-kind 4-neighbor transport component (§E.5)."""

    component_id: int
    kind: TransportKind
    cells: frozenset[Coord]
    cell_count: int
    bbox: BBox
    touches_external_margin: bool
    status: TransportComponentStatus


@dataclass(frozen=True, slots=True)
class ExistingTransportAnalysis:
    """Per-``TransportKind`` geometric components (§E.4); belt and pipe stay separate."""

    transport_kind: TransportKind
    component_count: int
    main_component_id: int | None
    components: tuple[TransportComponentSummary, ...]
    orphan_component_ids: tuple[int, ...]
    single_cell_artifacts: tuple[Coord, ...]


@dataclass(frozen=True, slots=True)
class EquipmentTransportAttachment:
    """Equipment cell ↔ adjacent transport (§E.7)."""

    equipment_coord: Coord
    equipment_kind: EquipmentKind
    adjacent_transport_coords: tuple[Coord, ...]
    adjacent_component_ids: tuple[int, ...]
    attached_to_main_component: bool


@dataclass(frozen=True, slots=True)
class ExistingEquipmentAnalysis:
    """Extractor/extension adjacency summary (§E.6)."""

    miner_count: int
    extension_count: int
    miners_without_adjacent_transport: tuple[Coord, ...]
    miners_attached_to_orphan_transport: tuple[Coord, ...]
    equipment_attachment: tuple[EquipmentTransportAttachment, ...]


@dataclass(frozen=True, slots=True)
class ExistingLayoutIssue:
    """STEP 0.5 issue row (§E.8); not interchangeable with STEP 9 validation rows."""

    code: ExistingLayoutIssueCode
    severity: ExistingLayoutIssueSeverity
    coords: tuple[Coord, ...]
    component_ids: tuple[int, ...]
    message: str


@dataclass(frozen=True, slots=True)
class ExistingLayoutSolverHints:
    """Derived trunk seed / cleanup unions (§E.9); does not imply hard-protected corridors."""

    trunk_seed_cell_union: frozenset[Coord]
    cleanup_candidate_cell_union: frozenset[Coord]


@dataclass(frozen=True, slots=True)
class ExistingLayoutAnalysis:
    """STEP 0.5 read-only context (§E).

    Never substitutes ``reconstruction.mineable_placement_cells``.
    """

    source_kind: SourceKind
    island_bbox: BBox
    belt_transport: ExistingTransportAnalysis
    pipe_transport: ExistingTransportAnalysis
    equipment: ExistingEquipmentAnalysis
    issues: tuple[ExistingLayoutIssue, ...]
    solver_hints: ExistingLayoutSolverHints


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
    """Adjacent cell in the extractor **output** direction (§3.1).

    Used for cheap-escape probe and routing anchor semantics; **not** the physical
    miner body tile. Pass1 preview must not materialize this cell as an installed
    extractor in ``mining_map`` committed frames (see ``PlacementBundle``).
    """

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
    parent_cell: BlueprintCell
    #: Unit cardinal vector from ``cell`` toward ``parent_cell`` (extension "faces" parent, §3.3).
    orientation_toward_parent: tuple[int, int]


@dataclass(frozen=True, slots=True)
class PlacementBundle:
    """One Pass1/Pass2 head + extensions + output stub.

    ``extractor.cell`` is the physical miner coordinate (mineable). ``output_stub.cell``
    is the neighbouring output/probe coordinate only; it is not a second installed tile.
    """

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
    placement_commit_entries: tuple[tuple[str, PlacementCommitState], ...] = ()
    beam_trace: tuple[dict[str, Any], ...] | None = None


@dataclass(frozen=True, slots=True)
class Pass2Result:
    """STEP 3 Pass2 provisional placements (§8)."""

    provisional_placements: tuple[PlacementBundle, ...] = ()
    blocked_cells_delta: tuple[BlueprintCell, ...] = ()
    placement_commit_entries: tuple[tuple[str, PlacementCommitState], ...] = ()
    beam_trace: tuple[dict[str, Any], ...] | None = None


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
    route_level: bool = False
    transport_kind: TransportKind | Literal["batch_mixed", "none"] | None = None

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
        trace_semantics.validate_route_level_trace_transport(
            route_level=self.route_level,
            transport_kind=self.transport_kind,
        )


# Back-compat alias for in-repo skeleton callers (prefer ``Step4RoutingResult``).
RoutingResult = Step4RoutingResult
