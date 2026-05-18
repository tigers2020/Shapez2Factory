"""Asteroid Lab optimization layer contracts (Sequence 1A/1B).

DTOs and enums are algorithm-facing; replay rows and ORM remain outside this package.
"""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.coords import (
    Coord,
    cardinal_unit_toward,
    neighbors4_server,
)
from django_apps.asteroid_lab.optimization.enums import (
    CandidateRejectReason,
    CommitConflictReason,
    Direction,
    EdgeKind,
    EvolutionConvergenceReason,
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
from django_apps.asteroid_lab.optimization.input_contracts import (
    BBox,
    EvolutionConfig,
    ExistingTransportCell,
    GenomeDiversityMetrics,
    OptimizationInput,
    RecoveryBudget,
    RouteDomainCellTransition,
    RouteGoal,
    RouteReservation,
    TopologyEdge,
    TopologyGraph,
    TopologyNode,
    ValidationIssue,
    ValidationResult,
    greenfield_optimization_input,
)
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    build_topology_graph,
    optimization_input_from_reconstruction,
)
from django_apps.asteroid_lab.optimization.route_domain import (
    RouteCellDomain,
    RouteDomainSnapshotBuilder,
)

__all__ = [
    "BBox",
    "CandidateRejectReason",
    "CommitConflictReason",
    "Coord",
    "Direction",
    "EdgeKind",
    "EvolutionConfig",
    "EvolutionConvergenceReason",
    "ExistingTransportCell",
    "GenomeDiversityMetrics",
    "OptimizationInput",
    "OptimizationReplayEventType",
    "PlacementCommitState",
    "RecoveryBudget",
    "ReservationState",
    "RouteCellDomain",
    "RouteClass",
    "RouteDomainCellTransition",
    "RouteDomainSnapshotBuilder",
    "RouteGoal",
    "RouteGoalKind",
    "RouteProbeFailureReason",
    "RouteReservation",
    "TopologyEdge",
    "TopologyGraph",
    "TopologyNode",
    "TopologyNodeKind",
    "TransportKind",
    "TransportMask",
    "ValidationIssue",
    "ValidationIssueCode",
    "ValidationResult",
    "ValidationSeverity",
    "build_topology_graph",
    "cardinal_unit_toward",
    "greenfield_optimization_input",
    "neighbors4_server",
    "optimization_input_from_reconstruction",
]
