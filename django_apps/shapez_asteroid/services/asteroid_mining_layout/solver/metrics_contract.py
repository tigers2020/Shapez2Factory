"""Canonical keys for solver summary / replay metrics (incremental single-source migration)."""

from __future__ import annotations

# --- Optimization / replay block (``build_final_solver_output`` optimization_replay_metrics) ---
OPTIMIZATION_REPLAY_METRIC_KEYS: tuple[str, ...] = (
    "baseline_snapshot_kind",
    "baseline_internal_transport_count",
    "baseline_internal_transport_post_step4_count",
    "final_internal_transport_count",
    "optimization_warnings",
    "counterfactual_internal_transport_sequential_v1",
    "counterfactual_aggregation",
    "counterfactual_failure_reason",
    "internal_transport_quality_ratio",
    "placement_candidate_blocked_count",
)

# --- STEP4 / trunk route counters mirrored on ``solver_summary`` and timeline STEP4 summary ---
SOLVER_SUMMARY_STEP4_TRUNK_KEYS: tuple[str, ...] = (
    "routed_stub_count",
    "total_stub_count",
    "route_cell_count",
    "step4_route_count",
    "step4_routing_failure_count",
    "step4_routed_count",
    "step4_rolled_back_count",
    "step4_quarantined_count",
    "route_revalidation_passed",
    "broken_routed_route_count",
    "cascade_reroute_count",
    "cascade_rollback_count",
)
