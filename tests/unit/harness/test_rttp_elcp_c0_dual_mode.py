"""Unit tests for C0 dual-mode comparison helpers (no Django DB)."""

from __future__ import annotations

from harness.investigation.rttp_elcp_c0_dual_mode import (
    ElcpC0ModeRunSnapshot,
    build_dual_run_comparison_table,
    derive_lane_capacity_shortfall_regate,
)


def _snap(
    *,
    mode: str,
    commit_order_len: int,
    primary_committed_count: int,
    lane_capacity_shortfall_count: int,
    stale_candidate_reachable_count: int,
    dominant_bucket: str,
    dominant_bucket_pct: float,
) -> ElcpC0ModeRunSnapshot:
    return ElcpC0ModeRunSnapshot(
        selection_mode=mode,
        git_sha="test-sha",
        commit_order_len=commit_order_len,
        primary_committed_count=primary_committed_count,
        primary_conflict_count=commit_order_len - primary_committed_count,
        primary_reprobe_failed_count=0,
        lane_capacity_shortfall_count=lane_capacity_shortfall_count,
        route_feasible_shortfall_count=0,
        stale_candidate_reachable_count=stale_candidate_reachable_count,
        validation_passed=True,
        throughput_shortfall_reason=None,
        bucket_coverage=1.0,
        bucket_histogram={"lane_capacity_shortfall": lane_capacity_shortfall_count},
        dominant_bucket=dominant_bucket,
        dominant_bucket_pct=dominant_bucket_pct,
    )


def test_build_dual_run_comparison_table_delta() -> None:
    baseline = _snap(
        mode="greedy_regret",
        commit_order_len=59,
        primary_committed_count=3,
        lane_capacity_shortfall_count=10,
        stale_candidate_reachable_count=27,
        dominant_bucket="stale_candidate_reachable",
        dominant_bucket_pct=0.48,
    )
    overlap = _snap(
        mode="greedy_regret_overlap_pack",
        commit_order_len=67,
        primary_committed_count=3,
        lane_capacity_shortfall_count=12,
        stale_candidate_reachable_count=30,
        dominant_bucket="lane_capacity_shortfall",
        dominant_bucket_pct=0.42,
    )
    table = build_dual_run_comparison_table(baseline=baseline, overlap=overlap)
    row = next(r for r in table if r["metric"] == "commit_order_len")
    assert row["greedy_regret"] == 59
    assert row["greedy_regret_overlap_pack"] == 67
    assert row["delta"] == 8


def test_derive_regate_unblocked_when_lane_dominant_on_overlap() -> None:
    baseline = _snap(
        mode="greedy_regret",
        commit_order_len=59,
        primary_committed_count=3,
        lane_capacity_shortfall_count=5,
        stale_candidate_reachable_count=27,
        dominant_bucket="stale_candidate_reachable",
        dominant_bucket_pct=0.48,
    )
    overlap = _snap(
        mode="greedy_regret_overlap_pack",
        commit_order_len=67,
        primary_committed_count=3,
        lane_capacity_shortfall_count=20,
        stale_candidate_reachable_count=10,
        dominant_bucket="lane_capacity_shortfall",
        dominant_bucket_pct=0.45,
    )
    verdict, _reason = derive_lane_capacity_shortfall_regate(
        baseline=baseline,
        overlap=overlap,
        validation_regression=False,
    )
    assert verdict in ("UNBLOCKED", "NARROWED_TO_COMMIT_ORDER")


def test_derive_regate_blocked_on_validation_regression() -> None:
    baseline = _snap(
        mode="greedy_regret",
        commit_order_len=59,
        primary_committed_count=3,
        lane_capacity_shortfall_count=5,
        stale_candidate_reachable_count=27,
        dominant_bucket="stale_candidate_reachable",
        dominant_bucket_pct=0.48,
    )
    overlap = _snap(
        mode="greedy_regret_overlap_pack",
        commit_order_len=67,
        primary_committed_count=3,
        lane_capacity_shortfall_count=20,
        stale_candidate_reachable_count=10,
        dominant_bucket="lane_capacity_shortfall",
        dominant_bucket_pct=0.45,
    )
    overlap = ElcpC0ModeRunSnapshot(
        selection_mode=overlap.selection_mode,
        git_sha=overlap.git_sha,
        commit_order_len=overlap.commit_order_len,
        primary_committed_count=overlap.primary_committed_count,
        primary_conflict_count=overlap.primary_conflict_count,
        primary_reprobe_failed_count=overlap.primary_reprobe_failed_count,
        lane_capacity_shortfall_count=overlap.lane_capacity_shortfall_count,
        route_feasible_shortfall_count=overlap.route_feasible_shortfall_count,
        stale_candidate_reachable_count=overlap.stale_candidate_reachable_count,
        validation_passed=False,
        throughput_shortfall_reason=overlap.throughput_shortfall_reason,
        bucket_coverage=overlap.bucket_coverage,
        bucket_histogram=overlap.bucket_histogram,
        dominant_bucket=overlap.dominant_bucket,
        dominant_bucket_pct=overlap.dominant_bucket_pct,
    )
    verdict, reason = derive_lane_capacity_shortfall_regate(
        baseline=baseline,
        overlap=overlap,
        validation_regression=True,
    )
    assert verdict == "BLOCKED"
    assert "informational_e2e" in reason
