"""Frozen DTOs for optimization input and topology (Phase 1)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from django_apps.shapez_asteroid.optimization.coords import BBox, Coord
from django_apps.shapez_asteroid.optimization.enums import (
    CandidateRejectReason,
    CardinalDirection,
    CommitConflictReason,
    EdgeKind,
    EvolutionConvergenceReason,
    ExtractorPlacementPolicy,
    OptimizationReplayEventType,
    PlacementCommitState,
    ReservationState,
    RouteClass,
    RouteGoalKind,
    RouteProbeFailureReason,
    TopologyNodeKind,
    TransportKind,
    TransportMask,
    ValidationIssueCode,
    ValidationSeverity,
)


@dataclass(frozen=True, slots=True)
class RouteGoal:
    coord: Coord
    goal_kind: RouteGoalKind
    transport_kind: TransportKind | None
    priority: int
    existing_trunk: bool


@dataclass(frozen=True, slots=True)
class TopologyNode:
    coord: Coord
    node_kind: TopologyNodeKind


@dataclass(frozen=True, slots=True)
class TopologyEdge:
    a: Coord
    b: Coord
    edge_kind: EdgeKind
    traversal_cost: int

    def __post_init__(self) -> None:
        if self.a == self.b:
            raise ValueError("TopologyEdge endpoints must differ")
        if self.a.x > self.b.x or (self.a.x == self.b.x and self.a.y > self.b.y):
            raise ValueError("TopologyEdge must be stored canonically with a <= b lexicographic")


@dataclass(frozen=True, slots=True)
class TopologyGraph:
    """Undirected graph: one canonical (a,b) edge per pair (a<=b); treat as bidirectional."""

    nodes: frozenset[TopologyNode]
    edges: frozenset[TopologyEdge]


@dataclass(frozen=True, slots=True)
class ExistingTransportCell:
    coord: Coord
    transport_kind: TransportKind


@dataclass(frozen=True, slots=True)
class OptimizationInput:
    asteroid_cells: frozenset[Coord]
    mineable_cells: frozenset[Coord]
    rim_cells: frozenset[Coord]
    interior_cells: frozenset[Coord]
    external_void_cells: frozenset[Coord]
    route_goals: frozenset[RouteGoal]
    existing_transport_cells: frozenset[ExistingTransportCell]
    existing_trunk_cells: frozenset[Coord]
    protected_corridor_cells: frozenset[Coord]
    blocked_cells: frozenset[Coord]
    topology_graph: TopologyGraph
    bbox: BBox


@dataclass(frozen=True, slots=True)
class RouteCellDomain:
    coord: Coord
    route_class: RouteClass
    traversal_cost: int
    hard_blocked: bool
    carve_allowed: bool
    transport_mask: TransportMask


@dataclass(frozen=True, slots=True)
class RouteDomainCellTransition:
    coord: Coord
    route_class_before: RouteClass
    route_class_after: RouteClass


@dataclass(frozen=True, slots=True)
class RecoveryBudget:
    max_removed_candidates: int
    max_carve_cells: int
    max_reroute_attempts: int


@dataclass(frozen=True, slots=True)
class GenomeDiversityMetrics:
    distinct_topology_signatures: int
    rim_cell_entropy_bits: float
    transport_kind_mix_score: float


@dataclass(frozen=True, slots=True)
class EvolutionConfig:
    seed: int
    population_size: int
    elite_count: int
    mutation_rate: float
    tournament_size: int
    max_generation: int
    max_stall_generation: int
    time_budget_ms: int | None
    forced_distant_mutation_period: int | None
    wall_clock_deadline_perf: float | None = None


@dataclass(frozen=True, slots=True)
class EvolutionResult:
    """Output of Sequence 5 evolutionary search (combination selection only)."""

    best_genome: Genome
    best_fitness: FitnessBreakdown
    generation_count: int
    evaluated_genome_count: int
    convergence_reason: EvolutionConvergenceReason


@dataclass(frozen=True, slots=True)
class CandidateGenerationConfig:
    extractor_policy: ExtractorPlacementPolicy
    allow_diagnostic_unreachable: bool
    max_candidates: int | None
    route_probe_max_expansions: int
    transport_kinds: frozenset[TransportKind]
    route_probe_goal_priority_weight: int
    wall_clock_deadline_perf: float | None = None
    max_consecutive_rejections: int | None = None


@dataclass(frozen=True, slots=True)
class CandidateEquivalenceKey:
    occupied_cells: frozenset[Coord]
    output_stub: Coord
    output_dir: CardinalDirection
    transport_kind: TransportKind
    base_throughput: int
    topology_signature: str


@dataclass(frozen=True, slots=True)
class RouteProbeInput:
    start: Coord
    goals: frozenset[RouteGoal]
    route_domain: Mapping[Coord, RouteCellDomain]
    topology_graph: TopologyGraph
    max_expansions: int
    transport_kind: TransportKind
    goal_priority_weight: int
    wall_clock_deadline_perf: float | None = None


@dataclass(frozen=True, slots=True)
class RouteProbeResult:
    reachable: bool
    path: tuple[Coord, ...]
    cost: int
    expanded_nodes: int
    reached_goal: RouteGoal | None
    goal_priority: int | None
    failure_reason: RouteProbeFailureReason | None


@dataclass(frozen=True, slots=True)
class BundleCandidate:
    candidate_id: str
    pattern_id: str
    topology_signature: str
    extractor: Coord
    extensions: tuple[Coord, ...]
    occupied_cells: frozenset[Coord]
    output_stub: Coord
    output_dir: CardinalDirection
    transport_kind: TransportKind
    base_throughput: int
    base_score: float
    route_probe_result: RouteProbeResult


@dataclass(frozen=True, slots=True)
class RejectedBundleCandidate:
    attempted_pattern_id: str
    extractor: Coord | None
    rejection_reason: CandidateRejectReason
    route_probe_result: RouteProbeResult | None


@dataclass(frozen=True, slots=True)
class CandidateGenerationDiagnostics:
    """Lab / HTTP diagnostics only; not used as algorithm input."""

    enumeration_attempts: int
    pre_dedupe_route_success_count: int
    route_probe_unreachable_suppressed_count: int
    reject_reason_counts: tuple[tuple[str, int], ...]
    route_probe_failure_reason_counts: tuple[tuple[str, int], ...]
    enumeration_aborted_wall_clock: bool
    enumeration_aborted_consecutive_rejects: bool
    max_consecutive_rejections: int | None
    route_probe_wall_ms_sum: int


@dataclass(frozen=True, slots=True)
class CandidateGenerationResult:
    normal_candidates: tuple[BundleCandidate, ...]
    rejected_candidates: tuple[RejectedBundleCandidate, ...]
    diagnostics: CandidateGenerationDiagnostics | None = None


@dataclass(frozen=True, slots=True)
class Gene:
    """Genome entry: references a bundle candidate by id only (Sequence 4)."""

    candidate_id: str
    enabled: bool
    commit_order: int


@dataclass(frozen=True, slots=True)
class Genome:
    genome_id: str
    genes: tuple[Gene, ...]
    seed: int


@dataclass(frozen=True, slots=True)
class FitnessMetrics:
    selected_candidate_count: int
    extractor_count: int
    extension_count: int
    overlap_count: int
    unreachable_count: int
    total_route_cost: int
    max_trunk_sharing: int
    narrow_passage_occupied_count: int


@dataclass(frozen=True, slots=True)
class FitnessBreakdown:
    """Scalar fitness components; penalties are stored as positive magnitudes to subtract."""

    extractor_score: float
    extension_score: float
    throughput_score: float
    route_cost_penalty: float
    overlap_penalty: float
    unreachable_penalty: float
    congestion_penalty: float
    orphan_penalty: float
    corridor_block_penalty: float
    future_expansion_penalty: float
    narrow_passage_penalty: float
    trunk_sharing_penalty: float
    dead_end_penalty: float
    route_goal_quality_score: float
    route_goal_priority_penalty: float
    route_fragility_penalty: float
    shared_corridor_pressure_penalty: float
    total: float
    metrics: FitnessMetrics


@dataclass(frozen=True, slots=True)
class OptimizationReplayFrame:
    """Output-only replay/debug frame (Phase 9 / Sequence 3B). Not algorithm input."""

    frame_index: int
    event_type: OptimizationReplayEventType
    title: str
    description: str
    visible_cells: tuple[Any, ...]
    overlay_cells: tuple[Any, ...]
    metrics: dict[str, Any]


@dataclass(frozen=True, slots=True)
class RouteReservation:
    """Route hold for Sequence 6; ``reservation_id`` is deterministic (no UUID)."""

    reservation_id: str
    candidate_id: str
    transport_kind: TransportKind
    path: tuple[Coord, ...]
    reserved_cells: frozenset[Coord]
    cost: int
    reached_goal: RouteGoal
    goal_priority: int
    reservation_state: ReservationState
    domain_cell_transitions: tuple[RouteDomainCellTransition, ...]


@dataclass(frozen=True, slots=True)
class CommittedPlacement:
    candidate_id: str
    occupied_cells: frozenset[Coord]
    transport_kind: TransportKind
    route_reservation_id: str


@dataclass(frozen=True, slots=True)
class CandidateCommitResult:
    candidate_id: str
    commit_state: PlacementCommitState
    conflict_reason: CommitConflictReason | None
    route_reservation_id: str | None
    route_probe_result: RouteProbeResult
    message: str


@dataclass(frozen=True, slots=True)
class IncrementalCommitResult:
    committed_placements: tuple[CommittedPlacement, ...]
    route_reservations: tuple[RouteReservation, ...]
    candidate_results: tuple[CandidateCommitResult, ...]
    final_route_domain: Mapping[Coord, RouteCellDomain]
    confirmed_candidate_count: int
    rolled_back_candidate_count: int


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    """Read-only validation finding (Sequence 7 assert gate)."""

    issue_code: ValidationIssueCode
    severity: ValidationSeverity
    coord: Coord | None
    candidate_id: str | None
    route_reservation_id: str | None
    path_index: int | None
    route_goal_kind: RouteGoalKind | None
    transport_kind: TransportKind | None
    message: str


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of ``validate_incremental_commit_result`` (issues sorted; ``passed`` = no ERROR)."""

    passed: bool
    issues: tuple[ValidationIssue, ...]
