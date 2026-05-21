"""Asteroid Lab optimization layer contracts (Sequence 1A/1B).

DTOs and enums are algorithm-facing; replay rows and ORM remain outside this package.
"""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.bundle_selection_targets import (
    BundleSelectionTargets,
    bundle_selection_targets_from_run_config,
    compute_bundle_selection_targets,
)
from django_apps.asteroid_lab.optimization.candidate_dtos import (
    CandidateGenerationConfig,
    CandidateGenerationResult,
    ExtractorPlacementPolicy,
    GeneCandidate,
    GenerationDiagnostics,
    RejectedGeneCandidate,
    build_normal_gene_candidate,
    make_candidate_id,
    make_topology_signature,
)
from django_apps.asteroid_lab.optimization.candidate_equivalence import (
    CandidateEquivalenceKey,
    dedupe_gene_candidates,
    equivalence_key_for_candidate,
)
from django_apps.asteroid_lab.optimization.candidate_generator import (
    default_generation_config,
    generate_gene_candidates,
)
from django_apps.asteroid_lab.optimization.candidate_geometry import (
    GeometryValidationResult,
    validate_projected_gene_geometry,
)
from django_apps.asteroid_lab.optimization.candidate_score import (
    CandidateScoreBreakdown,
    score_gene_candidate,
)
from django_apps.asteroid_lab.optimization.candidate_selector import (
    DEFAULT_MAX_SELECTED_VARIANTS_PER_EXTRACTOR,
    SelectedCandidatePlan,
    SelectionDiagnostics,
    select_gene_candidates_greedy,
)
from django_apps.asteroid_lab.optimization.capacity_planner import CapacityPlan, plan_capacity
from django_apps.asteroid_lab.optimization.commit_best_candidates import (
    ConfirmedGenePlacement,
    IncrementalCommitResult,
    SkippedCandidateRecord,
    commit_selected_candidates,
)
from django_apps.asteroid_lab.optimization.commit_order_diversity import diversify_commit_order
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
    MaterializationFailureReason,
    PenaltyMode,
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
from django_apps.asteroid_lab.optimization.final_validation import validate_final_layout
from django_apps.asteroid_lab.optimization.fitness_contracts import (
    CommitSurvivabilityMetrics,
    FitnessBreakdown,
    FitnessMetrics,
    compute_conservative_fragility_penalties,
    evolution_distant_mutation_slot_index,
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
from django_apps.asteroid_lab.optimization.materialization_dtos import (
    MaterializedEquipmentCell,
    MaterializedLayoutCells,
    MaterializedTransportCell,
    RouteMaterializationResult,
)
from django_apps.asteroid_lab.optimization.pipeline_result import SolverRuntimeResult
from django_apps.asteroid_lab.optimization.placement_network_materializer import (
    materialize_confirmed_placements,
    merge_materialized_layout,
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
from django_apps.asteroid_lab.optimization.route_network_materializer import (
    full_path_for_reservation,
    materialize_route_network,
    pick_tile_rotation,
    pick_tile_type,
)
from django_apps.asteroid_lab.optimization.route_probe import (
    RouteProbeInput,
    RouteProbeResult,
    build_route_domain_for_projected_gene_probe,
    run_route_probe,
)

__all__ = [
    "BBox",
    "BundleSelectionTargets",
    "bundle_selection_targets_from_run_config",
    "compute_bundle_selection_targets",
    "CapacityPlan",
    "CandidateEquivalenceKey",
    "CandidateGenerationConfig",
    "CandidateGenerationResult",
    "GenerationDiagnostics",
    "CandidateRejectReason",
    "CandidateScoreBreakdown",
    "ConfirmedGenePlacement",
    "CommitConflictReason",
    "Coord",
    "Direction",
    "EdgeKind",
    "CANONICAL_EXTRACTOR_OFFSET",
    "CANONICAL_FIXED_OUTPUT_TRANSPORT_OFFSET",
    "CANONICAL_OUTPUT_DIR",
    "CANONICAL_ROUTE_PROBE_START_OFFSET",
    "CommitSurvivabilityMetrics",
    "EvolutionConfig",
    "EvolutionConvergenceReason",
    "FitnessBreakdown",
    "FitnessMetrics",
    "compute_conservative_fragility_penalties",
    "evolution_distant_mutation_slot_index",
    "ExistingTransportCell",
    "ExtractorPlacementPolicy",
    "GeneCandidate",
    "GeneTemplate",
    "IncrementalCommitResult",
    "SkippedCandidateRecord",
    "MaterializationFailureReason",
    "MaterializedEquipmentCell",
    "MaterializedLayoutCells",
    "MaterializedTransportCell",
    "materialize_confirmed_placements",
    "merge_materialized_layout",
    "GenomeDiversityMetrics",
    "OptimizationInput",
    "PenaltyMode",
    "PlacementCommitState",
    "RecoveryBudget",
    "RejectedGeneCandidate",
    "SelectedCandidatePlan",
    "SelectionDiagnostics",
    "DEFAULT_MAX_SELECTED_VARIANTS_PER_EXTRACTOR",
    "SolverRuntimeResult",
    "ReservationState",
    "RouteCellDomain",
    "RouteClass",
    "RouteDomainCellTransition",
    "RouteDomainSnapshotBuilder",
    "RouteGoal",
    "RouteGoalKind",
    "RouteProbeFailureReason",
    "RouteMaterializationResult",
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
    "build_normal_gene_candidate",
    "build_route_domain_for_projected_gene_probe",
    "build_topology_graph",
    "cardinal_unit_toward",
    "dedupe_gene_candidates",
    "default_generation_config",
    "equivalence_key_for_candidate",
    "generate_gene_candidates",
    "gene_template_from_generated_sample",
    "greenfield_optimization_input",
    "load_gene_templates_from_json",
    "loaded_reconstruction_snapshot_from_result",
    "make_candidate_id",
    "make_topology_signature",
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
    "commit_selected_candidates",
    "full_path_for_reservation",
    "materialize_route_network",
    "pick_tile_rotation",
    "pick_tile_type",
    "score_gene_candidate",
    "select_gene_candidates_greedy",
    "diversify_commit_order",
    "validate_final_layout",
    "validate_projected_gene_geometry",
    "rotate_direction",
    "rotate_offset",
    "steps_from_canonical_e",
    "throughput_factor_for_extension_count",
]
