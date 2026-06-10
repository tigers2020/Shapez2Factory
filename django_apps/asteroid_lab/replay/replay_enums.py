"""Lab replay timeline enums (Phase 9A product contract)."""

from __future__ import annotations

from enum import StrEnum


class ReplayPhase(StrEnum):
    """Lifecycle phase marker on a replay timeline frame (not a separate track)."""

    DECODE = "decode"
    RECONSTRUCTION = "reconstruction"
    OPTIMIZATION_INPUT = "optimization_input"
    PATTERN_GENERATION = "pattern_generation"
    CANDIDATE_GENERATION = "candidate_generation"
    ROUTE_PROBE = "route_probe"
    GENOME_FITNESS = "genome_fitness"
    EVOLUTION = "evolution"
    INCREMENTAL_COMMIT = "incremental_commit"
    ROLLBACK = "rollback"
    VALIDATION = "validation"
    RESULT = "result"


class ReplayEventType(StrEnum):
    """Wire ``event_type`` for replay timeline frames (free strings forbidden)."""

    # Lifecycle (decode ~ reconstruction)
    DECODE_STARTED = "decode.started"
    DECODE_COMPLETED = "decode.completed"
    RECONSTRUCTION_STARTED = "reconstruction.started"
    RECONSTRUCTION_COMPLETED = "reconstruction.completed"
    EXTERIOR_TRANSPORT_COMPLETED = "exterior_transport.completed"

    # Layer 03 rim bundle scan (solver runtime segment)
    LAYER03_RIM_BUNDLE_SCAN_BEGIN = "layer03_rim_bundle_scan_begin"
    LAYER03_RIM_BUNDLE_SCAN_COMPLETE = "layer03_rim_bundle_scan_complete"
    LAYER03_RIM_BUNDLE_POOL_SUMMARY = "layer03_rim_bundle_pool_summary"
    LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW = "layer03_rim_bundle_pool_probe_window"

    # Layer 03 rim greedy placement (solver runtime segment)
    LAYER03_RIM_GREEDY_BEGIN = "layer03_rim_greedy_begin"
    LAYER03_RIM_GREEDY_SUMMARY = "layer03_rim_greedy_summary"
    LAYER03_RIM_GREEDY_PASS1_COMPLETE = "layer03_rim_greedy_pass1_complete"
    LAYER03_RIM_GREEDY_SEED_COMMITTED = "layer03_rim_greedy_seed_committed"
    LAYER03_RIM_GREEDY_COMPLETE = "layer03_rim_greedy_complete"

    # Layer 04 inner pattern fill (canonical L4)
    LAYER04_INNER_PATTERN_FILL_BEGIN = "layer04_inner_pattern_fill_begin"
    LAYER04_INNER_PATTERN_FILL_COMPLETE = "layer04_inner_pattern_fill_complete"

    # Layer 04 rim provisional placement (solver runtime segment)
    LAYER04_RIM_PLACEMENT_BEGIN = "layer04_rim_placement_begin"
    LAYER04_RIM_CANDIDATE_SELECTED = "layer04_rim_candidate_selected"
    LAYER04_RIM_CANDIDATE_REJECTED_OVERLAP = "layer04_rim_candidate_rejected_overlap"
    LAYER04_RIM_PLACEMENT_COMPLETE = "layer04_rim_placement_complete"

    # Layer 04 transport routing (deprecated wire; read-compat one release)
    LAYER04_TRANSPORT_ROUTING_BEGIN = "layer04_transport_routing_begin"
    LAYER04_TRANSPORT_ROUTING_COMPLETE = "layer04_transport_routing_complete"

    # Layer 05 transport routing (canonical committed belt/pipe tiles)
    LAYER05_TRANSPORT_ROUTING_BEGIN = "layer05_transport_routing_begin"
    LAYER05_TRANSPORT_ROUTING_COMPLETE = "layer05_transport_routing_complete"

    # Optimization (superset: matches OptimizationReplayEventType wire values)
    OPTIMIZATION_INPUT_LOADED = "optimization.input_loaded"
    CAPACITY_PLAN_CREATED = "capacity.plan_created"
    ROUTE_GOAL_GENERATED = "route_goal.generated"
    PATTERN_GENERATED = "pattern.generated"
    CANDIDATE_GENERATED = "candidate.generated"
    CANDIDATE_REJECTED = "candidate.rejected"
    ROUTE_PROBE_SUCCEEDED = "route_probe.succeeded"
    ROUTE_PROBE_FAILED = "route_probe.failed"
    CANDIDATE_POOL_COMPLETED = "candidate_pool.completed"
    CANDIDATE_SELECTION_COMPLETED = "candidate_selection.completed"
    GENOME_GENERATED = "genome.generated"
    GENOME_EVALUATED = "genome.evaluated"
    GENERATION_COMPLETED = "generation.completed"
    BEST_GENOME_SELECTED = "best_genome.selected"
    ROUTE_COMMIT_ATTEMPTED = "route.commit_attempted"
    ROUTE_COMMITTED = "route.committed"
    ROUTE_ROLLED_BACK = "route.rolled_back"
    ROUTE_MATERIALIZED = "route.materialized"
    VALIDATION_COMPLETED = "validation.completed"
    VALIDATION_FAILED = "validation.failed"
    RESULT_LAYOUT = "result.layout"

    # RTTP diagnostic snapshots (3B-S-3; distinct from generic optimization wire types)
    RTTP_ROUTE_DOMAIN_SNAPSHOT = "rttp.route_domain_snapshot"
    RTTP_CANDIDATE_POOL_SNAPSHOT = "rttp.candidate_pool_snapshot"
    RTTP_GENOME_SELECTION_SNAPSHOT = "rttp.genome_selection_snapshot"
    RTTP_COMMIT_DOMAIN_SNAPSHOT = "rttp.commit_domain_snapshot"
