"""Central literals for mining layout solver: replay contracts, trace ids, tuning knobs.

Algorithm modules import from here; this module must not import sibling package modules
(avoid cycles). Enum-keyed maps stay next to their enums (e.g. route_zone).
"""

from __future__ import annotations

# --- Recovery chain segments / trigger reasons (replay contract, §13) ---
RECOVERY_SEGMENT_P4_RECLAIM = "p4_reclaim"
RECOVERY_SEGMENT_SOFT_REPLACE_V2 = "soft_replace_v2"
RECOVERY_SEGMENT_POST_RECLAIM_PASS3 = "post_reclaim_pass3"
RECOVERY_TRIGGER_POST_PASS3_P4_RECLAIM = "post_pass3_p4_reclaim_entry"
RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE = "step4_routing_failure"

# --- P5 recovery contract (attempt caps) ---
# Sentinels: numeric 0; semantics differ by knob (see recovery_timeline_envelope).
# RECOVERY_VALIDATION_LOOP_DISABLED: MAX_VALIDATION == this → no extra Pass3→P4 cycles.
RECOVERY_VALIDATION_LOOP_DISABLED = 0
# RECOVERY_TOTAL_RECOVERY_CAP_UNLIMITED: MAX_TOTAL == this → no P4 skip by chain-length cap.
# NOTE: 0 does NOT mean "disabled"; it means "unlimited" for this specific knob.
RECOVERY_TOTAL_RECOVERY_CAP_UNLIMITED = 0

MAX_TOTAL_RECOVERY_ATTEMPTS = RECOVERY_TOTAL_RECOVERY_CAP_UNLIMITED
# Bounded Pass3→P4 timeline: total forward finalize passes when the validation recovery loop
# is enabled (``recovery_orchestrator`` sets ``max_cycles`` to this value; not ``N + 1`` retries).
MAX_VALIDATION_RECOVERY_ATTEMPTS = 3

RECOVERY_TERMINAL_TOTAL_ATTEMPTS_EXCEEDED = "recovery_terminal_total_attempts_exceeded"
RECOVERY_TERMINAL_VALIDATION_EXHAUSTED = "recovery_terminal_validation_recovery_exhausted"
RECOVERY_SKIP_P4_TOTAL_CAP = "recovery_skip_p4_total_cap"
RECOVERY_SEGMENT_VALIDATION_RETRY = "validation_recovery_retry"

# §13 pass3_summary ``recovery_terminal_reason`` (docs alias: terminal_reason).
RECOVERY_TERMINAL_POST_RECLAIM_PASS3_SUCCESS = "post_reclaim_pass3_success"
RECOVERY_TERMINAL_FINAL_VALIDATION_FAILED_AFTER_POST_RECLAIM_PASS3 = (
    "final_validation_failed_after_post_reclaim_pass3"
)
RECOVERY_TERMINAL_P4_RECLAIM_COMPLETE = "p4_reclaim_complete"

# P5 STEP9 → recovery action plan ids (planning; bounded loop in recovery_orchestrator only).
RECOVERY_ACTION_ROLLBACK_LOWEST_PRIORITY_PLACEMENT = "rollback_lowest_priority_placement"
RECOVERY_ACTION_PRECALCULATE_REPLACEMENT_ROUTE_SOFT_CORRIDOR = (
    "precalculate_replacement_route_soft_corridor"
)
RECOVERY_ACTION_ROLLBACK_OR_FAIL_QUARANTINED = "rollback_or_fail_quarantined"
RECOVERY_ACTION_GEOMETRY_REPAIR_OR_FAIL = "geometry_repair_or_fail"

# P5 solver_summary: baseline vs final internal transport (Pass1·Pass2 snapshot).
OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_ABOVE_PASS2_BASELINE = (
    "internal_transport_above_pass2_baseline"
)
# Counterfactual sequential-trunk v1: warn when final / counterfactual exceeds this ratio.
OPTIMIZATION_QUALITY_RATIO_WARN_THRESHOLD = 1.35
OPTIMIZATION_WARNING_INTERNAL_TRANSPORT_QUALITY_RATIO_HIGH = "internal_transport_quality_ratio_high"
# Baseline snapshot: Pass1·Pass2 committed map immediately before STEP4 merge/routing.
OPTIMIZATION_BASELINE_SNAPSHOT_PASS1_PASS2_PRE_STEP4 = "pass1_pass2_pre_step4"

# Preserve-first: solver output internal transport worse than merged input baseline (STEP 0.5).
LAYOUT_PRESERVE_HARD_GATE_REASON_TRANSPORT_REGRESSION = (
    "final_internal_transport_above_solver_input_baseline"
)

# Pass12 merged-seed: optional stub recovery (``SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY``).
MAX_PASS12_RECOVERY_PROBES_PER_MINER = 4
MAX_PASS12_RECOVERY_BFS_HOPS = 8
# Drop-trace BFS: nearest same-role transport for taxonomy (separate from recovery hop cap).
MAX_PASS12_NEAREST_TRANSPORT_TRACE_HOPS = 256

# Counterfactual shortest-feasible baseline (geometry + STEP4 Dijkstra; sequential trunk v1).
OPTIMIZATION_COUNTERFACTUAL_AGGREGATION_SEQUENTIAL_TRUNK_V1 = "sequential_trunk_v1"

# Named recovery phases (summary / replay contract; append-only lists on solver_summary).
RECOVERY_PHASE_VALIDATION_RECOVERY = "validation_recovery"
RECOVERY_PHASE_MERGE_PARTIAL_FAILURE = "merge_partial_failure"
RECOVERY_PHASE_RECLAIM_INCREMENTAL_FAILURE = "reclaim_incremental_failure"
RECOVERY_PHASE_POST_RECLAIM_PASS3_CONNECTIVITY_BREAK = "post_reclaim_pass3_connectivity_break"

# --- Trace ``location`` strings (STEP10 NDJSON) ---
SOLVER_SERVICE_BUILD_SOLVER_TIMELINE_LOCATION = (
    "django_apps.shapez_asteroid.services.asteroid_mining_layout."
    "solver_service.build_solver_timeline"
)

PASS12_TRY_COMMIT_PASS1_BUNDLE_TRACE_LOCATION = "pass12_bundle_commit.try_commit_pass1_bundle"
PASS12_TRY_COMMIT_PASS2_BUNDLE_TRACE_LOCATION = "pass12_bundle_commit.try_commit_pass2_bundle"

# --- P4 reclaim tuning (§12.2); values only may change ---
DEFAULT_RECLAIM_GAIN_RATIO_THRESHOLD = 1.5
MAX_RECLAIM_INTERNAL_TRANSPORT_SPEND_RATIO = 0.35
MIN_INTERNAL_TRANSPORT_SPEND_WHEN_NO_PASS3_SAVINGS = 1

# Expected mining throughput gain (slots) for a minimal miner + extension shadow bundle.
RECLAIM_SHADOW_MINER_EXTENSION_GAIN_SLOTS = 2.0

# §12.6 — P4 commit loop vs per-scan bundle-eval cap (separate contracts).
MAX_RECLAIM_ITERATIONS = 3
MAX_RECLAIM_SHADOW_SCAN_LIMIT = 16

# P4 reclaim spatial diversity (search pressure only; gain_ratio threshold stays raw).
# Anchor falloff: per prior p, contribution = max(0, R - manhattan(anchor,p)) * K_FALL.
# At d=0 one prior: contribution = R * K_FALL = RECLAIM_DIVERSITY_CLUSTER_MAX_PRIOR_PENALTY.
RECLAIM_DIVERSITY_CLUSTER_RADIUS = 12
RECLAIM_DIVERSITY_CLUSTER_MAX_PRIOR_PENALTY = 0.08
RECLAIM_DIVERSITY_CLUSTER_FALLOFF_K = (
    RECLAIM_DIVERSITY_CLUSTER_MAX_PRIOR_PENALTY / float(RECLAIM_DIVERSITY_CLUSTER_RADIUS)
)
# Shadow stub path cells already committed as incremental route (weak vs cluster penalty).
RECLAIM_ROUTE_ZONE_OVERLAP_PENALTY = 0.015

P4_REJECT_FINAL_ROUTE_OVERLAP = "rejected_by_final_route_overlap"
P4_REJECT_HARD_PROTECTED_CORRIDOR = "rejected_by_hard_protected_corridor"
P4_REJECT_SOFT_PROTECTED_CORRIDOR = "rejected_by_soft_protected_corridor"
P4_REJECT_NO_OUTPUT_STUB = "rejected_by_no_output_stub"
P4_REJECT_NO_INCREMENTAL_ROUTE = "rejected_by_no_incremental_route"
P4_REJECT_GAIN_RATIO = "rejected_by_gain_ratio"
P4_REJECT_INTERNAL_TRANSPORT_BUDGET = "rejected_by_internal_transport_budget"
P4_REJECT_VALIDATION = "rejected_by_validation"

P4_REJECT_NO_SHADOW_CANDIDATE = "rejected_by_no_shadow_candidate"
P4_ROLLBACK_AFTER_PROVISIONAL_VALIDATION_FAILURE = "rollback_after_provisional_validation_failure"

# §14.3 soft corridor atomic replacement (replacement-first; no old-only removal path).
P4_SOFT_REPLACE_REJECT_OLD_NOT_SOFT_PROTECTED = "rejected_by_old_not_soft_protected"
P4_SOFT_REPLACE_REJECT_OLD_NOT_TRANSPORT = "rejected_by_old_not_transport_on_map"
P4_SOFT_REPLACE_REJECT_NO_ROUTING_JOB = "rejected_by_no_routing_job"
P4_SOFT_REPLACE_REJECT_NO_REPLACEMENT_ROUTE = "rejected_by_no_replacement_route"
P4_SOFT_REPLACE_REJECT_REPLACEMENT_NOT_CONNECTED = "rejected_by_replacement_not_connected"
P4_SOFT_REPLACE_REJECT_VALIDATION = "rejected_by_soft_replace_validation"

P4_SOFT_REPLACE_ROUTE_PLACEMENT_ID = "p4_soft_replace_route"

# §14.3 soft corridor atomic replace (P4 reclaim loop + shared routing primitive; see
# routing.protected_corridor_replace.try_atomic_replace_soft_corridor).
P4_SOFT_REPLACE_V1_CONTRACT = (
    "soft replace v1 = single selected soft corridor + first routing job only"
)
P4_SOFT_REPLACE_V2_CONTRACT = (
    "soft replace v2 = deterministic all routing jobs + first valid replacement"
)

P4_RECLAIM_CORRIDOR_SOURCE_SOLVER_POOL = "solver_pool"
P4_RECLAIM_CORRIDOR_SOURCE_PASS3_TRACE = "pass3_trace"
P4_RECLAIM_CORRIDOR_SOURCE_P3E3_TOUCHED_FALLBACK = "p3e3_touched_fallback"
P4_RECLAIM_CORRIDOR_SOURCE_EMPTY = "empty"

P4_RECLAIM_PROVISIONAL_PLACEMENT_ID = "p4_reclaim_provisional"
P4_RECLAIM_INCREMENTAL_ROUTE_PLACEMENT_ID = "p4_reclaim_incremental_route"

P4_ROLLBACK_AFTER_INCREMENTAL_ROUTE_FAILED = "rollback_after_incremental_route_failed"

# --- Pass3 shared (reject reasons, defaults, ratio bounds) ---
MAX_ROUTE_LENGTH_RATIO = 1.35

COMMIT_REASON_GUARDED_ATOMIC = "guarded_atomic_candidate"

# P3-E3b-1: atomic guarded-commit gate reasons (namespace separate from rollback / commit_reason).
P3E3_REJECT_NONE = "none"
P3E3_REJECT_PRECHECK_NO_CANDIDATE = "precheck_no_candidate"
P3E3_REJECT_PRECHECK_NO_REPLACEMENT_ROUTE = "precheck_no_replacement_route"
P3E3_REJECT_FIXED_STUB_REMOVAL = "rejected_by_fixed_stub_removal"
P3E3_REJECT_HARD_PROTECTED_CORRIDOR = "rejected_by_hard_protected_corridor"
P3E3_REJECT_NO_REPLACEMENT_ROUTE = "rejected_by_no_replacement_route"
P3E3_REJECT_ROUTE_LENGTH_RATIO = "rejected_by_route_length_ratio"
P3E3_REJECT_CONNECTIVITY = "rejected_by_connectivity"
P3E3_REJECT_GEOMETRY = "rejected_by_geometry"
P3E3_REJECT_VALIDATION = "rejected_by_validation"

# P3-E2 shadow trace: ``p3e2_hard_protected_guard_state`` (string contract; keep values stable).
P3E2_GUARD_EMPTY_POOL_NOT_WIRED = "empty_corridor_pool_not_wired"
P3E2_GUARD_FROM_ADAPTER_INPUT = "from_adapter_input"
P3E2_GUARD_FROM_ROUTING_CORRIDOR_POOL = "from_routing_corridor_pool"

P3E2_SHADOW_ENABLED_DEFAULT = True
P3E3_GUARDED_COMMIT_ENABLED_DEFAULT = True
P3E3_ATOMIC_SKIPPED_SHADOW_LEX_INCOMPLETE = "shadow_lex_incomplete_greedy_only"

# --- build_solver_timeline frame ids (replay / trace); order matches pipeline stages ---
SOLVER_FRAME_INIT = "solver_init"
SOLVER_FRAME_PASS1_OUTER = "solver_pass1_outer"
SOLVER_FRAME_PASS2_INTERNAL = "solver_pass2_internal"
SOLVER_FRAME_STEP4_ROUTING = "solver_step4_routing"
SOLVER_FRAME_PASS3_TRANSPORT = "solver_pass3_transport"
# Trace checkpoint after P4 reclaim loop (no separate timeline frame; map lives in pass3 frame).
SOLVER_FRAME_P4_RECLAIM = "solver_p4"
SOLVER_FRAME_VALIDATE = "solver_validate"

SOLVER_TIMELINE_FRAME_ORDER: tuple[str, ...] = (
    SOLVER_FRAME_INIT,
    SOLVER_FRAME_PASS1_OUTER,
    SOLVER_FRAME_PASS2_INTERNAL,
    SOLVER_FRAME_STEP4_ROUTING,
    SOLVER_FRAME_PASS3_TRANSPORT,
    SOLVER_FRAME_VALIDATE,
)

# --- Solver state hash (STEP4 routing subset) ---
ROUTING_STATE_KEYS_STEP4_HASH: tuple[str, ...] = (
    "hard_protected_corridors",
    "soft_protected_corridors",
)

# --- Post-P4 Pass3 reruns ---
MAX_POST_RECLAIM_PASS3_RERUNS = 1

# Post-reclaim Pass3 P3-E3b atomic route-length ratio (메인 Pass3는 ``MAX_ROUTE_LENGTH_RATIO``).
POST_RECLAIM_P3E3_ROUTE_RATIO_BASE = 1.20
POST_RECLAIM_P3E3_ROUTE_RATIO_CAP = 1.35
POST_RECLAIM_P3E3_ROUTE_RATIO_K = 0.004


def post_reclaim_p3e3_route_ratio_max(*, pass3_internal_transport_saved: int) -> float:
    """Adaptive cap: BASE + K * saved, 상한 CAP (post-reclaim Pass3 전용)."""

    saved = max(0, int(pass3_internal_transport_saved))
    raw = float(POST_RECLAIM_P3E3_ROUTE_RATIO_BASE) + float(saved) * float(
        POST_RECLAIM_P3E3_ROUTE_RATIO_K
    )
    return min(raw, float(POST_RECLAIM_P3E3_ROUTE_RATIO_CAP))


# --- Replay NDJSON contract ---
SOLVER_REPLAY_CONTRACT_VERSION = 8

# v8: ``ui_frames[].trunk_load_overlay`` (STEP4 trunk observation slice for STEP10 UI).

# Pass3 lexicographic search: multiply STEP4 ``trunk_edge_load`` counts per canonical edge key.
PASS3_TRUNK_EDGE_CONGESTION_WEIGHT_PER_TRAVERSAL = 10

# Pass3 lex ``route_step``: extra cost on ``ASTEROID_INTERIOR_VOID`` by BFS depth from void-touching
# boundary (encourages perimeter-hugging without a new lex axis).
PASS3_INTERIOR_DEPTH_ROUTE_PENALTY_PER_UNIT = 3
PASS3_INTERIOR_DEPTH_PENALTY_MAX_DEPTH = 12

# --- P3-F: Topology Branch Replacement MVP (branch semantics + trace; no new engine) ---
# Detector kind ordering (deterministic priority for ``p3f_best_candidate_kind`` and the
# ``p3f_candidate_kinds`` list itself).
P3F_KIND_NONE = "none"
P3F_KIND_MINEABLE_HEAVY = "mineable_heavy_branch"
P3F_KIND_LONG_PERIMETER_DETOUR = "long_perimeter_detour"
P3F_KIND_PARALLEL_DUPLICATE = "parallel_duplicate_branch"
P3F_KIND_LOW_REUSE = "low_reuse_branch"
P3F_KIND_PRIORITY_ORDER: tuple[str, ...] = (
    P3F_KIND_MINEABLE_HEAVY,
    P3F_KIND_LONG_PERIMETER_DETOUR,
    P3F_KIND_PARALLEL_DUPLICATE,
    P3F_KIND_LOW_REUSE,
)
# Detector thresholds (MVP heuristics; tunable, unit-tested).
P3F_MINEABLE_HEAVY_RATIO_MIN = 0.35
P3F_LONG_DETOUR_RATIO_MIN = 1.15
P3F_PARALLEL_ENDPOINT_MANHATTAN_MAX = 2
P3F_PARALLEL_OVERLAP_RATIO_MAX = 0.25
P3F_LOW_REUSE_RATIO_MAX = 0.10

# Replacement search mode (fixed for MVP; future expansions may add new strings).
P3F_REPLACEMENT_SEARCH_MODE_LEX_PER_STUB = "p3e3_lex_per_stub"

# Commit reasons (alias namespace separate from existing ``COMMIT_REASON_GUARDED_ATOMIC``).
P3F_COMMIT_REASON_NORMAL_GAIN = "normal_gain"

# Rejected reason mapping fallback when a P3-E3 reason is not in the table.
P3F_REJECTED_REASON_UNMAPPED = "rejected_unmapped"
P3F_REJECTED_NO_REPLACEMENT_ROUTE = "rejected_by_no_replacement_route"

# --- Lexicographic router (mining opportunity penalty) ---
MINING_OPPORTUNITY_LOSS_PER_CANDIDATE = 40

# --- Repair / demolition cost grid (separate from Pass3 mining-priority costs) ---
INF_COST = 10**9
MINEABLE_ROUTE_COST = 60

# --- Mining-map layout_kind sets (extractors / extensions) ---
EXTRACTORS_SHAPE = frozenset({"miner", "extractor"})
EXTRACTORS_FLUID = frozenset({"fluid_miner"})
EXTENSIONS = frozenset({"extension", "fluid_extension"})

# Pass1/Pass2 extension chain cap (maximized extractor+extension group size minus core).
PASS12_MAX_EXTENSION_TILES = 3
