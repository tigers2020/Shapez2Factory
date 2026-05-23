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
