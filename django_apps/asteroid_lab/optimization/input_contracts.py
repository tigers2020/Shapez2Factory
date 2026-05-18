"""Phase 1 optimization input DTOs and related Sequence 1A contracts."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.enums import (
    EdgeKind,
    ReservationState,
    RouteClass,
    RouteGoalKind,
    TopologyNodeKind,
    TransportKind,
    ValidationIssueCode,
    ValidationSeverity,
)


@dataclass(frozen=True, slots=True)
class BBox:
    """Inclusive Server X/Y bounding box."""

    min_sx: int
    max_sx: int
    min_sy: int
    max_sy: int


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


@dataclass(frozen=True, slots=True)
class TopologyGraph:
    """Undirected topology: store both (a,b) and (b,a) for every adjacency (Phase 1)."""

    nodes: frozenset[TopologyNode]
    edges: frozenset[TopologyEdge]


@dataclass(frozen=True, slots=True)
class RouteGoal:
    coord: Coord
    goal_kind: RouteGoalKind
    transport_kind: TransportKind | None
    priority: int
    existing_trunk: bool


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
class EvolutionConfig:
    """Phase 6 evolution parameters."""

    seed: int
    population_size: int
    elite_count: int
    mutation_rate: float
    tournament_size: int
    max_generation: int
    max_stall_generation: int
    time_budget_ms: int | None
    forced_distant_mutation_period: int | None


@dataclass(frozen=True, slots=True)
class GenomeDiversityMetrics:
    """Phase 6 observability (v0 may fill with zeros)."""

    distinct_topology_signatures: int
    rim_cell_entropy_bits: float
    transport_kind_mix_score: float


@dataclass(frozen=True, slots=True)
class RecoveryBudget:
    """Phase 7 thrashing caps."""

    max_removed_candidates: int
    max_carve_cells: int
    max_reroute_attempts: int


@dataclass(frozen=True, slots=True)
class RouteDomainCellTransition:
    """Phase 7 minimal before/after route_class delta."""

    coord: Coord
    route_class_before: RouteClass
    route_class_after: RouteClass


@dataclass(frozen=True, slots=True)
class RouteReservation:
    """Phase 7 reservation row."""

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
class ValidationIssue:
    """Phase 8 validation row."""

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
    passed: bool
    issues: tuple[ValidationIssue, ...]


def greenfield_optimization_input(*, bbox: BBox | None = None) -> OptimizationInput:
    """Greenfield = empty transport, trunk, protected (Phase 1; no alternate DTO path)."""

    bb = bbox if bbox is not None else BBox(0, 0, 0, 0)
    empty: frozenset[Coord] = frozenset()
    empty_t: frozenset[ExistingTransportCell] = frozenset()
    empty_g = TopologyGraph(frozenset(), frozenset())
    return OptimizationInput(
        asteroid_cells=empty,
        mineable_cells=empty,
        rim_cells=empty,
        interior_cells=empty,
        external_void_cells=empty,
        route_goals=frozenset(),
        existing_transport_cells=empty_t,
        existing_trunk_cells=empty,
        protected_corridor_cells=empty,
        blocked_cells=empty,
        topology_graph=empty_g,
        bbox=bb,
    )
