"""Unit tests for D0 stale attribution (no Django DB)."""

from __future__ import annotations

from harness.investigation.rttp_elcp_d0_stale_attribution import (
    ElcpD0Verdict,
    ElcpStaleAttributionClass,
    classify_stale_attribution,
    compute_d0_verdict,
    diff_blocking_cells,
)
from harness.investigation.rttp_elcp_reprobe_forensics import (
    ElcpProbeFailureClass,
    MirrorDomainSnapshot,
)


def test_diff_blocking_cells_sample_bounded() -> None:
    before = MirrorDomainSnapshot(0, frozenset({(0, 0)}), frozenset())
    at_attempt = MirrorDomainSnapshot(1, frozenset({(0, 0), (1, 0), (2, 0)}), frozenset())
    count, sample = diff_blocking_cells(before=before, at_attempt=at_attempt)
    assert count == 2
    assert len(sample) <= 10


def test_classify_post_probe_reservation_block() -> None:
    assert (
        classify_stale_attribution(
            probe_failure_class=ElcpProbeFailureClass.STALE_CANDIDATE_REACHABLE,
            commit_probe_reachable=True,
            commit_conflict_reason="overlap",
            probe_start=(1, 2),
            candidate_route_probe_start=(1, 2),
            goals_nonempty_at_commit=True,
            global_goal_count=5,
            committed_route_cell_count=10,
            traversable_cell_count=100,
            new_blocking_cells_since_last_commit_count=3,
        )
        is ElcpStaleAttributionClass.POST_PROBE_RESERVATION_BLOCK
    )


def test_classify_probe_start_drift() -> None:
    assert (
        classify_stale_attribution(
            probe_failure_class=ElcpProbeFailureClass.STALE_CANDIDATE_REACHABLE,
            commit_probe_reachable=True,
            commit_conflict_reason=None,
            probe_start=(1, 2),
            candidate_route_probe_start=(3, 4),
            goals_nonempty_at_commit=True,
            global_goal_count=5,
            committed_route_cell_count=10,
            traversable_cell_count=100,
            new_blocking_cells_since_last_commit_count=0,
        )
        is ElcpStaleAttributionClass.PROBE_START_DRIFT
    )


def test_compute_verdict_reservation_dominant() -> None:
    classes = [ElcpStaleAttributionClass.POST_PROBE_RESERVATION_BLOCK] * 20 + [
        ElcpStaleAttributionClass.SELECTION_SURVIVABILITY_GAP
    ] * 14
    verdict = compute_d0_verdict(
        attribution_classes=classes,
        new_blocking_cells_counts=[5] * 20 + [0] * 14,
        reservation_conflict_flags=[True] * 20 + [False] * 14,
    )
    assert verdict is ElcpD0Verdict.RESERVATION_DRIFT_DOMINANT


def test_compute_verdict_inconclusive_when_unattributed_high() -> None:
    classes = [ElcpStaleAttributionClass.UNATTRIBUTED_STALE] * 5 + [
        ElcpStaleAttributionClass.SELECTION_SURVIVABILITY_GAP
    ] * 29
    verdict = compute_d0_verdict(
        attribution_classes=classes,
        new_blocking_cells_counts=[0] * 34,
        reservation_conflict_flags=[False] * 34,
    )
    assert verdict is ElcpD0Verdict.INCONCLUSIVE_NEEDS_TELEMETRY
