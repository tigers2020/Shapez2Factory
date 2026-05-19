"""Asteroid Lab optimization layer contracts (Sequence 1A/1B).

DTOs and enums are algorithm-facing; replay rows and ORM remain outside this package.
"""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidate_geometry import (
    GeometryValidationResult,
    validate_projected_gene_geometry,
)
from django_apps.asteroid_lab.optimization.capacity_planner import CapacityPlan, plan_capacity
from django_apps.asteroid_lab.optimization.coord_transform import (
    rotate_direction,
    rotate_offset,
    steps_from_canonical_e,
)
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
from django_apps.asteroid_lab.optimization.gene_projection import (
    ProjectedGenePlacement,
    project_gene_placement,
)
from django_apps.asteroid_lab.optimization.gene_template import (
    CANONICAL_EXTRACTOR_OFFSET,
    CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET,
    CANONICAL_OUTPUT_DIR,
    CANONICAL_ROUTE_PROBE_START_OFFSET,
    GeneTemplate,
    throughput_factor_for_extension_count,
)
from django_apps.asteroid_lab.optimization.gene_template_loader import (
    gene_template_from_generated_sample,
    load_gene_templates_from_json,
    parse_gene_template_record,
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
from django_apps.asteroid_lab.optimization.loaded_snapshot import (
    LoadedReconstructionSnapshot,
    loaded_reconstruction_snapshot_from_result,
)
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    build_topology_graph,
    mineable_field_kind,
    optimization_input_from_loaded_snapshot,
    optimization_input_from_reconstruction,
)
from django_apps.asteroid_lab.optimization.route_domain import (
    RouteCellDomain,
    RouteDomainSnapshotBuilder,
)
from django_apps.asteroid_lab.optimization.route_goal_planner import (
    PlannedRouteGoals,
    plan_route_goals,
)
from django_apps.asteroid_lab.optimization.route_probe import (
    RouteProbeInput,
    RouteProbeResult,
    build_route_domain_for_projected_gene_probe,
    run_route_probe,
)

__all__ = [
    "BBox",
    "CapacityPlan",
    "CandidateRejectReason",
    "CommitConflictReason",
    "Coord",
    "Direction",
    "EdgeKind",
    "CANONICAL_EXTRACTOR_OFFSET",
    "CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET",
    "CANONICAL_OUTPUT_DIR",
    "CANONICAL_ROUTE_PROBE_START_OFFSET",
    "EvolutionConfig",
    "EvolutionConvergenceReason",
    "ExistingTransportCell",
    "GeneTemplate",
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
    "GeometryValidationResult",
    "LoadedReconstructionSnapshot",
    "PlannedRouteGoals",
    "RouteProbeInput",
    "RouteProbeResult",
    "build_route_domain_for_projected_gene_probe",
    "build_topology_graph",
    "cardinal_unit_toward",
    "gene_template_from_generated_sample",
    "greenfield_optimization_input",
    "load_gene_templates_from_json",
    "loaded_reconstruction_snapshot_from_result",
    "mineable_field_kind",
    "neighbors4_server",
    "optimization_input_from_loaded_snapshot",
    "optimization_input_from_reconstruction",
    "plan_capacity",
    "plan_route_goals",
    "parse_gene_template_record",
    "project_gene_placement",
    "ProjectedGenePlacement",
    "run_route_probe",
    "validate_projected_gene_geometry",
    "rotate_direction",
    "rotate_offset",
    "steps_from_canonical_e",
    "throughput_factor_for_extension_count",
]
