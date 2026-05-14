"""Canonical enum string stability (``03_data_schema_dto.md``)."""

from __future__ import annotations

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    CommitReason,
    PlacementCommitState,
    RecoveryTrigger,
    RejectedReason,
    RollbackReason,
    RouteZone,
    SolverTerminationTier,
    TransportKind,
)


def test_transport_kind_distinct_strings() -> None:
    assert TransportKind.SHAPE_BELT.value == "shape_belt"
    assert TransportKind.FLUID_PIPE.value == "fluid_pipe"
    assert TransportKind.SHAPE_BELT != TransportKind.FLUID_PIPE
    assert {TransportKind.SHAPE_BELT.value, TransportKind.FLUID_PIPE.value} == {
        "shape_belt",
        "fluid_pipe",
    }


@pytest.mark.parametrize(
    ("member", "expected"),
    [
        (PlacementCommitState.PROVISIONAL_PLACED, "provisional_placed"),
        (PlacementCommitState.ROUTED_CONFIRMED, "routed_confirmed"),
        (PlacementCommitState.QUARANTINED_UNROUTED, "quarantined_unrouted"),
        (PlacementCommitState.ROLLED_BACK, "rolled_back"),
    ],
)
def test_placement_commit_state_values(member: PlacementCommitState, expected: str) -> None:
    assert member.value == expected


@pytest.mark.parametrize(
    ("member", "expected"),
    [
        (RouteZone.OUTSIDE, "outside"),
        (RouteZone.BOUNDARY_VOID, "boundary_void"),
        (RouteZone.INTERNAL_VOID, "internal_void"),
        (RouteZone.FILLABLE_INTERIOR, "fillable_interior"),
        (RouteZone.PLACEMENT_CANDIDATE, "placement_candidate"),
        (RouteZone.PLACEMENT_OCCUPIED, "placement_occupied"),
        (RouteZone.BLOCKED, "blocked"),
    ],
)
def test_route_zone_values(member: RouteZone, expected: str) -> None:
    assert member.value == expected


@pytest.mark.parametrize(
    ("member", "expected"),
    [
        (SolverTerminationTier.SUCCESS, "success"),
        (SolverTerminationTier.PARTIAL_SUCCESS, "partial_success"),
        (SolverTerminationTier.SOLVER_FAILURE, "solver_failure"),
    ],
)
def test_solver_termination_tier_values(member: SolverTerminationTier, expected: str) -> None:
    assert member.value == expected


@pytest.mark.parametrize(
    ("member", "expected"),
    [
        (RecoveryTrigger.STEP4_ROUTING_FAILURE, "step4_routing_failure"),
        (RecoveryTrigger.STEP4_CAPACITY_FAILURE, "step4_capacity_failure"),
        (RecoveryTrigger.PASS3_CONNECTIVITY_BREAK, "pass3_connectivity_break"),
        (
            RecoveryTrigger.POST_RECLAIM_PASS3_CONNECTIVITY_BREAK,
            "post_reclaim_pass3_connectivity_break",
        ),
        (RecoveryTrigger.RECLAIM_INCREMENTAL_FAILURE, "reclaim_incremental_failure"),
        (RecoveryTrigger.FINAL_VALIDATION_FAILURE, "final_validation_failure"),
    ],
)
def test_recovery_trigger_values(member: RecoveryTrigger, expected: str) -> None:
    assert member.value == expected


@pytest.mark.parametrize(
    ("member", "expected"),
    [
        (CommitReason.NORMAL_GAIN, "normal_gain"),
        (CommitReason.DEGRADED_CONNECTED_RECOVERY, "degraded_connected_recovery"),
    ],
)
def test_commit_reason_values(member: CommitReason, expected: str) -> None:
    assert member.value == expected


@pytest.mark.parametrize(
    ("member", "expected"),
    [
        (RollbackReason.ROLLBACK_UNROUTED_PLACEMENT, "rollback_unrouted_placement"),
        (RollbackReason.ROLLBACK_RECLAIM_CANDIDATE, "rollback_reclaim_candidate"),
    ],
)
def test_rollback_reason_values(member: RollbackReason, expected: str) -> None:
    assert member.value == expected


@pytest.mark.parametrize(
    ("member", "expected"),
    [
        (RejectedReason.REJECTED_BY_GAIN_OR_LENGTH, "rejected_by_gain_or_length"),
        (RejectedReason.REJECTED_BY_CONNECTIVITY, "rejected_by_connectivity"),
        (RejectedReason.REJECTED_BY_OVERLAP, "rejected_by_overlap"),
        (RejectedReason.REJECTED_BY_CAPACITY, "rejected_by_capacity"),
        (
            RejectedReason.REJECTED_BY_INTERNAL_TRANSPORT_BUDGET,
            "rejected_by_internal_transport_budget",
        ),
        (
            RejectedReason.REJECTED_BY_HARD_PROTECTED_CORRIDOR,
            "rejected_by_hard_protected_corridor",
        ),
        (
            RejectedReason.REJECTED_BY_NO_REPLACEMENT_ROUTE,
            "rejected_by_no_replacement_route",
        ),
        (RejectedReason.SOLVER_FAILURE_ATTEMPT_LIMIT, "solver_failure_attempt_limit"),
    ],
)
def test_rejected_reason_values(member: RejectedReason, expected: str) -> None:
    assert member.value == expected


def test_placement_commit_states_distinct() -> None:
    states = list(PlacementCommitState)
    assert len(states) == len({s.value for s in states})
