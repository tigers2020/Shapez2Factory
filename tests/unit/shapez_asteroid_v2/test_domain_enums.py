from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    CommitReason,
    PlacementCommitState,
    RecoveryTrigger,
    RejectedReason,
    RollbackReason,
    RouteZone,
    SolverTerminationTier,
    SourceKind,
    TransportKind,
)


def test_transport_kind_values() -> None:
    assert TransportKind.SHAPE_BELT.value == "shape_belt"
    assert TransportKind.FLUID_PIPE.value == "fluid_pipe"
    assert TransportKind.SHAPE_BELT != TransportKind.FLUID_PIPE


def test_placement_commit_state_values() -> None:
    assert PlacementCommitState.PROVISIONAL_PLACED.value == "provisional_placed"
    assert PlacementCommitState.ROUTED_CONFIRMED.value == "routed_confirmed"
    assert PlacementCommitState.QUARANTINED_UNROUTED.value == "quarantined_unrouted"
    assert PlacementCommitState.ROLLED_BACK.value == "rolled_back"
    assert len(frozenset(PlacementCommitState)) == 4


def test_route_zone_values() -> None:
    assert RouteZone.OUTSIDE.value == "outside"
    assert RouteZone.BOUNDARY_VOID.value == "boundary_void"
    assert RouteZone.INTERNAL_VOID.value == "internal_void"
    assert RouteZone.FILLABLE_INTERIOR.value == "fillable_interior"
    assert RouteZone.PLACEMENT_CANDIDATE.value == "placement_candidate"
    assert RouteZone.PLACEMENT_OCCUPIED.value == "placement_occupied"
    assert RouteZone.BLOCKED.value == "blocked"


def test_solver_termination_tier_values() -> None:
    assert SolverTerminationTier.SUCCESS.value == "success"
    assert SolverTerminationTier.PARTIAL_SUCCESS.value == "partial_success"
    assert SolverTerminationTier.SOLVER_FAILURE.value == "solver_failure"


def test_recovery_trigger_values() -> None:
    assert RecoveryTrigger.STEP4_ROUTING_FAILURE.value == "step4_routing_failure"
    assert RecoveryTrigger.STEP4_CAPACITY_FAILURE.value == "step4_capacity_failure"
    assert RecoveryTrigger.PASS3_CONNECTIVITY_BREAK.value == "pass3_connectivity_break"
    assert (
        RecoveryTrigger.POST_RECLAIM_PASS3_CONNECTIVITY_BREAK.value
        == "post_reclaim_pass3_connectivity_break"
    )
    assert RecoveryTrigger.RECLAIM_INCREMENTAL_FAILURE.value == "reclaim_incremental_failure"
    assert RecoveryTrigger.FINAL_VALIDATION_FAILURE.value == "final_validation_failure"


def test_commit_reason_values() -> None:
    assert CommitReason.NORMAL_GAIN.value == "normal_gain"
    assert CommitReason.DEGRADED_CONNECTED_RECOVERY.value == "degraded_connected_recovery"


def test_rollback_reason_values() -> None:
    assert RollbackReason.ROLLBACK_UNROUTED_PLACEMENT.value == "rollback_unrouted_placement"
    assert RollbackReason.ROLLBACK_RECLAIM_CANDIDATE.value == "rollback_reclaim_candidate"


def test_rejected_reason_values() -> None:
    assert RejectedReason.REJECTED_BY_GAIN_OR_LENGTH.value == "rejected_by_gain_or_length"
    assert RejectedReason.REJECTED_BY_CONNECTIVITY.value == "rejected_by_connectivity"
    assert RejectedReason.REJECTED_BY_OVERLAP.value == "rejected_by_overlap"
    assert RejectedReason.REJECTED_BY_CAPACITY.value == "rejected_by_capacity"
    assert (
        RejectedReason.REJECTED_BY_INTERNAL_TRANSPORT_BUDGET.value
        == "rejected_by_internal_transport_budget"
    )
    assert (
        RejectedReason.REJECTED_BY_HARD_PROTECTED_CORRIDOR.value
        == "rejected_by_hard_protected_corridor"
    )
    assert (
        RejectedReason.REJECTED_BY_NO_REPLACEMENT_ROUTE.value == "rejected_by_no_replacement_route"
    )
    assert RejectedReason.SOLVER_FAILURE_ATTEMPT_LIMIT.value == "solver_failure_attempt_limit"


def test_source_kind_unknown_exists() -> None:
    assert SourceKind.UNKNOWN.value == "unknown"
