"""Unit tests for F1.1 private overlap forensic (no Django DB)."""

from __future__ import annotations

from harness.investigation.rttp_elcp_f11_private_overlap_forensic import (
    ElcpF11PrivateOverlapRootCause,
    F12NominationWithheldReason,
    classify_f11_root_cause,
    evaluate_f12_nomination,
)


def test_classify_trunk_evidence_missing_when_undercoverage_in_overlap() -> None:
    assert (
        classify_f11_root_cause(
            overlap_undercoverage_cells=frozenset({(1, 0)}),
            overlap_full_not_reserved=frozenset({(2, 0)}),
            overlap_spine_stub=frozenset(),
            overlap_branch_only=frozenset(),
            overlap_trunk_mask=frozenset({(1, 0)}),
        )
        is ElcpF11PrivateOverlapRootCause.TRUNK_EVIDENCE_MISSING
    )


def test_classify_committed_growth_artifact_from_full_route_not_reserved() -> None:
    assert (
        classify_f11_root_cause(
            overlap_undercoverage_cells=frozenset(),
            overlap_full_not_reserved=frozenset({(3, 0)}),
            overlap_spine_stub=frozenset(),
            overlap_branch_only=frozenset(),
            overlap_trunk_mask=frozenset(),
        )
        is ElcpF11PrivateOverlapRootCause.COMMITTED_GROWTH_ARTIFACT
    )


def test_classify_spine_or_stub_residual_overlap() -> None:
    assert (
        classify_f11_root_cause(
            overlap_undercoverage_cells=frozenset(),
            overlap_full_not_reserved=frozenset(),
            overlap_spine_stub=frozenset({(4, 0)}),
            overlap_branch_only=frozenset(),
            overlap_trunk_mask=frozenset({(4, 0)}),
        )
        is ElcpF11PrivateOverlapRootCause.SPINE_OR_STUB_RESIDUAL_OVERLAP
    )


def test_classify_true_peer_conservative_empty_trunk_only_when_no_other_buckets() -> None:
    assert (
        classify_f11_root_cause(
            overlap_undercoverage_cells=frozenset(),
            overlap_full_not_reserved=frozenset(),
            overlap_spine_stub=frozenset(),
            overlap_branch_only=frozenset(),
            overlap_trunk_mask=frozenset(),
        )
        is ElcpF11PrivateOverlapRootCause.TRUE_PEER_BRANCH_OVERLAP
    )


def test_classify_true_peer_not_from_empty_trunk_when_full_route_bucket_nonempty() -> None:
    assert (
        classify_f11_root_cause(
            overlap_undercoverage_cells=frozenset(),
            overlap_full_not_reserved=frozenset({(1, 0)}),
            overlap_spine_stub=frozenset(),
            overlap_branch_only=frozenset(),
            overlap_trunk_mask=frozenset(),
        )
        is ElcpF11PrivateOverlapRootCause.COMMITTED_GROWTH_ARTIFACT
    )


def test_classify_unclear_when_only_trunk_mask_present_without_undercoverage() -> None:
    assert (
        classify_f11_root_cause(
            overlap_undercoverage_cells=frozenset(),
            overlap_full_not_reserved=frozenset(),
            overlap_spine_stub=frozenset(),
            overlap_branch_only=frozenset(),
            overlap_trunk_mask=frozenset({(1, 0)}),
        )
        is ElcpF11PrivateOverlapRootCause.UNCLEAR_NEEDS_TRACE
    )


def test_f12_nomination_withheld_when_true_peer_dominant() -> None:
    nomination = evaluate_f12_nomination(
        root_cause_counts={
            ElcpF11PrivateOverlapRootCause.TRUE_PEER_BRANCH_OVERLAP.value: 12,
            ElcpF11PrivateOverlapRootCause.TRUNK_EVIDENCE_MISSING.value: 8,
        },
        unclear_count=0,
        mirror_parity_ok=True,
        row_count=20,
    )
    assert nomination.withheld_reason is F12NominationWithheldReason.TRUE_PEER_DOMINANT
    assert nomination.nominated_track is None


def test_f12_nomination_dominant_fixable_trunk_f12a() -> None:
    nomination = evaluate_f12_nomination(
        root_cause_counts={
            ElcpF11PrivateOverlapRootCause.TRUNK_EVIDENCE_MISSING.value: 12,
            ElcpF11PrivateOverlapRootCause.COMMITTED_GROWTH_ARTIFACT.value: 8,
        },
        unclear_count=0,
        mirror_parity_ok=True,
        row_count=20,
    )
    assert nomination.nominated is True
    assert nomination.nominated_track == "F1.2a"
    assert nomination.withheld_reason is F12NominationWithheldReason.NONE


def test_f12_nomination_dominant_fixable_growth_artifact_f12b() -> None:
    nomination = evaluate_f12_nomination(
        root_cause_counts={
            ElcpF11PrivateOverlapRootCause.COMMITTED_GROWTH_ARTIFACT.value: 12,
            ElcpF11PrivateOverlapRootCause.TRUNK_EVIDENCE_MISSING.value: 8,
        },
        unclear_count=0,
        mirror_parity_ok=True,
        row_count=20,
    )
    assert nomination.nominated is True
    assert nomination.nominated_track == "F1.2b"
    assert nomination.withheld_reason is F12NominationWithheldReason.NONE


def test_f12_nomination_dominant_fixable_spine_stub_f12c() -> None:
    nomination = evaluate_f12_nomination(
        root_cause_counts={
            ElcpF11PrivateOverlapRootCause.SPINE_OR_STUB_RESIDUAL_OVERLAP.value: 12,
            ElcpF11PrivateOverlapRootCause.TRUNK_EVIDENCE_MISSING.value: 8,
        },
        unclear_count=0,
        mirror_parity_ok=True,
        row_count=20,
    )
    assert nomination.nominated is True
    assert nomination.nominated_track == "F1.2c"
    assert nomination.withheld_reason is F12NominationWithheldReason.NONE


def test_f12_nomination_unclear_too_high() -> None:
    nomination = evaluate_f12_nomination(
        root_cause_counts={},
        unclear_count=3,
        mirror_parity_ok=True,
        row_count=20,
    )
    assert nomination.withheld_reason is F12NominationWithheldReason.UNCLEAR_TOO_HIGH


def test_f12_nomination_split_fixable_classes() -> None:
    nomination = evaluate_f12_nomination(
        root_cause_counts={
            ElcpF11PrivateOverlapRootCause.TRUNK_EVIDENCE_MISSING.value: 8,
            ElcpF11PrivateOverlapRootCause.COMMITTED_GROWTH_ARTIFACT.value: 8,
            ElcpF11PrivateOverlapRootCause.TRUE_PEER_BRANCH_OVERLAP.value: 4,
        },
        unclear_count=0,
        mirror_parity_ok=True,
        row_count=20,
    )
    assert nomination.withheld_reason is F12NominationWithheldReason.SPLIT_FIXABLE_CLASSES


def test_f12_nomination_parent_mirror_fail() -> None:
    nomination = evaluate_f12_nomination(
        root_cause_counts={},
        unclear_count=0,
        mirror_parity_ok=False,
        row_count=20,
    )
    assert nomination.withheld_reason is F12NominationWithheldReason.PARENT_MIRROR_FAIL
