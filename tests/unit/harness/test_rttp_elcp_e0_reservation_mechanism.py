"""Unit tests for E0 reservation mechanism (no Django DB)."""

from __future__ import annotations

from harness.investigation.rttp_elcp_e0_reservation_mechanism import (
    BSpecNominationWithheldReason,
    ElcpE0MechanismClass,
    ElcpE0Verdict,
    classify_e0_mechanism,
    compute_e0_verdict,
    evaluate_appendix_veto,
    evaluate_b_spec_nomination,
    is_unattributed_mechanism_class,
)


def test_is_unattributed_prefix() -> None:
    assert is_unattributed_mechanism_class(
        ElcpE0MechanismClass.UNATTRIBUTED_ROUTE_CELL_MECHANISM
    )
    assert not is_unattributed_mechanism_class(
        ElcpE0MechanismClass.PRIVATE_ROUTE_OVERLAP
    )


def test_classify_private_route_overlap() -> None:
    assert (
        classify_e0_mechanism(
            commit_conflict_reason="route_cell_conflict",
            private_overlap_cells=frozenset({(1, 2)}),
            shareable_trunk_undercoverage_cells=frozenset(),
            spine_augment_cells=frozenset(),
            probe_merged_route_diff_cells=frozenset(),
            output_stub_in_committed_route=False,
            inlet_stub_adjacent_committed_route_cells=frozenset(),
        )
        is ElcpE0MechanismClass.PRIVATE_ROUTE_OVERLAP
    )


def test_classify_inlet_stub_on_committed_route() -> None:
    assert (
        classify_e0_mechanism(
            commit_conflict_reason="inlet_on_shared_transport",
            private_overlap_cells=frozenset(),
            shareable_trunk_undercoverage_cells=frozenset(),
            spine_augment_cells=frozenset(),
            probe_merged_route_diff_cells=frozenset(),
            output_stub_in_committed_route=True,
            inlet_stub_adjacent_committed_route_cells=frozenset(),
        )
        is ElcpE0MechanismClass.INLET_STUB_ON_COMMITTED_ROUTE
    )


def test_verdict_precedence_mirror_fail_inconclusive() -> None:
    verdict = compute_e0_verdict(
        mechanism_classes=[ElcpE0MechanismClass.PRIVATE_ROUTE_OVERLAP] * 20
        + [ElcpE0MechanismClass.INLET_STUB_ON_COMMITTED_ROUTE] * 14,
        mirror_parity_ok=False,
        appendix_veto=False,
    )
    assert verdict is ElcpE0Verdict.INCONCLUSIVE_NEEDS_TELEMETRY


def test_verdict_precedence_appendix_veto_split() -> None:
    verdict = compute_e0_verdict(
        mechanism_classes=[ElcpE0MechanismClass.PRIVATE_ROUTE_OVERLAP] * 20
        + [ElcpE0MechanismClass.INLET_STUB_ON_COMMITTED_ROUTE] * 14,
        mirror_parity_ok=True,
        appendix_veto=True,
    )
    assert verdict is ElcpE0Verdict.SPLIT_RESERVATION_POLICY_NEEDS_DECOMPOSITION


def test_verdict_route_cell_dominant() -> None:
    verdict = compute_e0_verdict(
        mechanism_classes=[ElcpE0MechanismClass.PRIVATE_ROUTE_OVERLAP] * 18
        + [ElcpE0MechanismClass.INLET_STUB_ON_COMMITTED_ROUTE] * 16,
        mirror_parity_ok=True,
        appendix_veto=False,
    )
    assert verdict is ElcpE0Verdict.ROUTE_CELL_RESERVATION_CONFLICT_DOMINANT


def test_appendix_veto_opposite_family_dominant() -> None:
    veto = evaluate_appendix_veto(
        primary_route_family_count=20,
        primary_inlet_family_count=14,
        appendix_route_family_count=4,
        appendix_inlet_family_count=26,
    )
    assert veto is True


def test_nomination_withheld_owner_split() -> None:
    nomination = evaluate_b_spec_nomination(
        verdict=ElcpE0Verdict.ROUTE_CELL_RESERVATION_CONFLICT_DOMINANT,
        mechanism_classes=[
            ElcpE0MechanismClass.PRIVATE_ROUTE_OVERLAP,
            ElcpE0MechanismClass.SHAREABLE_TRUNK_UNDERCOVERAGE,
            ElcpE0MechanismClass.SPINE_AUGMENTATION_CONFLICT,
            ElcpE0MechanismClass.PROBE_VS_MERGED_ROUTE_MISMATCH,
        ]
        * 9,
        appendix_veto=False,
    )
    assert nomination.nominated is False
    assert nomination.withheld_reason is BSpecNominationWithheldReason.OWNER_SPLIT
