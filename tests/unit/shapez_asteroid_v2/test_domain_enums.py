"""Canonical enum string stability (``03_data_schema_dto.md``)."""

from __future__ import annotations

from enum import StrEnum

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    ROUTE_ZONE_PASS3_BASE_COST,
    TRANSPORT_KIND_ROUTE_ZONE_MULTIPLIER,
    CommitReason,
    EquipmentKind,
    ExistingLayoutIssueCode,
    ExistingLayoutIssueSeverity,
    MineableEmptyCause,
    PlacementCommitState,
    RecoveryTrigger,
    RejectedReason,
    RollbackReason,
    RouteZone,
    SolverTerminationTier,
    SourceKind,
    TransportComponentStatus,
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


@pytest.mark.parametrize(
    ("member", "expected"),
    [
        (SourceKind.RAW_ASTEROID_FIELD, "raw_asteroid_field"),
        (SourceKind.EXISTING_FLUID_LAYOUT, "existing_fluid_layout"),
        (SourceKind.EXISTING_SHAPE_LAYOUT, "existing_shape_layout"),
        (SourceKind.MIXED_EXISTING_LAYOUT, "mixed_existing_layout"),
        (SourceKind.UNKNOWN, "unknown"),
    ],
)
def test_source_kind_values(member: SourceKind, expected: str) -> None:
    assert member.value == expected


@pytest.mark.parametrize(
    ("member", "expected"),
    [
        (TransportComponentStatus.MAIN_TRUNK_CANDIDATE, "main_trunk_candidate"),
        (TransportComponentStatus.ORPHAN_COMPONENT, "orphan_component"),
        (TransportComponentStatus.SINGLE_CELL_ARTIFACT, "single_cell_artifact"),
        (TransportComponentStatus.CLEANUP_CANDIDATE, "cleanup_candidate"),
    ],
)
def test_transport_component_status_values(member: TransportComponentStatus, expected: str) -> None:
    assert member.value == expected


@pytest.mark.parametrize(
    ("member", "expected"),
    [
        (EquipmentKind.FLUID_MINER, "fluid_miner"),
        (EquipmentKind.SHAPE_MINER, "shape_miner"),
        (EquipmentKind.EXTENSION, "extension"),
    ],
)
def test_equipment_kind_values(member: EquipmentKind, expected: str) -> None:
    assert member.value == expected


@pytest.mark.parametrize(
    ("member", "expected"),
    [
        (ExistingLayoutIssueCode.TRANSPORT_DISCONNECTED, "TRANSPORT_DISCONNECTED"),
        (ExistingLayoutIssueCode.ORPHAN_TRANSPORT_COMPONENT, "ORPHAN_TRANSPORT_COMPONENT"),
        (
            ExistingLayoutIssueCode.SINGLE_CELL_TRANSPORT_ARTIFACT,
            "SINGLE_CELL_TRANSPORT_ARTIFACT",
        ),
        (
            ExistingLayoutIssueCode.MINER_NO_ADJACENT_TRANSPORT,
            "MINER_NO_ADJACENT_TRANSPORT",
        ),
        (
            ExistingLayoutIssueCode.MINER_ATTACHED_TO_ORPHAN_TRANSPORT,
            "MINER_ATTACHED_TO_ORPHAN_TRANSPORT",
        ),
        (ExistingLayoutIssueCode.SOURCE_KIND_AMBIGUOUS, "SOURCE_KIND_AMBIGUOUS"),
    ],
)
def test_existing_layout_issue_code_values(member: ExistingLayoutIssueCode, expected: str) -> None:
    assert member.value == expected


@pytest.mark.parametrize(
    ("member", "expected"),
    [
        (ExistingLayoutIssueSeverity.INFO, "info"),
        (ExistingLayoutIssueSeverity.WARNING, "warning"),
        (ExistingLayoutIssueSeverity.ERROR, "error"),
    ],
)
def test_existing_layout_issue_severity_values(
    member: ExistingLayoutIssueSeverity, expected: str
) -> None:
    assert member.value == expected


@pytest.mark.parametrize(
    ("member", "expected"),
    [
        (MineableEmptyCause.NOT_EMPTY, "not_empty"),
        (MineableEmptyCause.SHELL_T_NOT_RECOGNIZED, "shell_t_not_recognized"),
        (
            MineableEmptyCause.DUPLICATE_COORD_OVERLAY_BLOCKED,
            "duplicate_coord_overlay_blocked",
        ),
        (MineableEmptyCause.ALL_CANDIDATES_BLOCKED, "all_candidates_blocked"),
        (
            MineableEmptyCause.SMALL_OR_FRAGMENTED_SHELL,
            "small_or_fragmented_shell",
        ),
        (MineableEmptyCause.UNKNOWN, "unknown"),
    ],
)
def test_mineable_empty_cause_values(member: MineableEmptyCause, expected: str) -> None:
    assert member.value == expected


def test_domain_str_enum_member_names_frozen() -> None:
    """멤버 추가·삭제 시 명시적 갱신(문자열·trace 계약)."""

    cases: list[tuple[type[StrEnum], frozenset[str]]] = [
        (
            TransportKind,
            frozenset({"SHAPE_BELT", "FLUID_PIPE"}),
        ),
        (
            PlacementCommitState,
            frozenset(
                {
                    "PROVISIONAL_PLACED",
                    "ROUTED_CONFIRMED",
                    "QUARANTINED_UNROUTED",
                    "ROLLED_BACK",
                }
            ),
        ),
        (
            RouteZone,
            frozenset(
                {
                    "OUTSIDE",
                    "BOUNDARY_VOID",
                    "INTERNAL_VOID",
                    "FILLABLE_INTERIOR",
                    "PLACEMENT_CANDIDATE",
                    "PLACEMENT_OCCUPIED",
                    "BLOCKED",
                }
            ),
        ),
        (
            SolverTerminationTier,
            frozenset({"SUCCESS", "PARTIAL_SUCCESS", "SOLVER_FAILURE"}),
        ),
        (
            RecoveryTrigger,
            frozenset(
                {
                    "STEP4_ROUTING_FAILURE",
                    "STEP4_CAPACITY_FAILURE",
                    "PASS3_CONNECTIVITY_BREAK",
                    "POST_RECLAIM_PASS3_CONNECTIVITY_BREAK",
                    "RECLAIM_INCREMENTAL_FAILURE",
                    "FINAL_VALIDATION_FAILURE",
                }
            ),
        ),
        (CommitReason, frozenset({"NORMAL_GAIN", "DEGRADED_CONNECTED_RECOVERY"})),
        (
            RollbackReason,
            frozenset({"ROLLBACK_UNROUTED_PLACEMENT", "ROLLBACK_RECLAIM_CANDIDATE"}),
        ),
        (
            RejectedReason,
            frozenset(
                {
                    "REJECTED_BY_GAIN_OR_LENGTH",
                    "REJECTED_BY_CONNECTIVITY",
                    "REJECTED_BY_OVERLAP",
                    "REJECTED_BY_CAPACITY",
                    "REJECTED_BY_INTERNAL_TRANSPORT_BUDGET",
                    "REJECTED_BY_HARD_PROTECTED_CORRIDOR",
                    "REJECTED_BY_NO_REPLACEMENT_ROUTE",
                    "SOLVER_FAILURE_ATTEMPT_LIMIT",
                }
            ),
        ),
        (
            SourceKind,
            frozenset(
                {
                    "RAW_ASTEROID_FIELD",
                    "EXISTING_FLUID_LAYOUT",
                    "EXISTING_SHAPE_LAYOUT",
                    "MIXED_EXISTING_LAYOUT",
                    "UNKNOWN",
                }
            ),
        ),
        (
            TransportComponentStatus,
            frozenset(
                {
                    "MAIN_TRUNK_CANDIDATE",
                    "ORPHAN_COMPONENT",
                    "SINGLE_CELL_ARTIFACT",
                    "CLEANUP_CANDIDATE",
                }
            ),
        ),
        (EquipmentKind, frozenset({"FLUID_MINER", "SHAPE_MINER", "EXTENSION"})),
        (
            ExistingLayoutIssueCode,
            frozenset(
                {
                    "TRANSPORT_DISCONNECTED",
                    "ORPHAN_TRANSPORT_COMPONENT",
                    "SINGLE_CELL_TRANSPORT_ARTIFACT",
                    "MINER_NO_ADJACENT_TRANSPORT",
                    "MINER_ATTACHED_TO_ORPHAN_TRANSPORT",
                    "SOURCE_KIND_AMBIGUOUS",
                }
            ),
        ),
        (ExistingLayoutIssueSeverity, frozenset({"INFO", "WARNING", "ERROR"})),
        (
            MineableEmptyCause,
            frozenset(
                {
                    "NOT_EMPTY",
                    "SHELL_T_NOT_RECOGNIZED",
                    "DUPLICATE_COORD_OVERLAY_BLOCKED",
                    "ALL_CANDIDATES_BLOCKED",
                    "SMALL_OR_FRAGMENTED_SHELL",
                    "UNKNOWN",
                }
            ),
        ),
    ]
    for cls, expected_names in cases:
        got = frozenset(m.name for m in cls)
        assert got == expected_names, f"{cls.__name__}: expected {expected_names!r}, got {got!r}"


def test_route_zone_pass3_base_cost_matches_canon_11_1() -> None:
    """``03_data_schema_dto.md`` §11.1 표와 키 전체 커버."""

    assert set(ROUTE_ZONE_PASS3_BASE_COST) == set(RouteZone)
    assert ROUTE_ZONE_PASS3_BASE_COST[RouteZone.OUTSIDE] == 1.0
    assert ROUTE_ZONE_PASS3_BASE_COST[RouteZone.BOUNDARY_VOID] == 5.0
    assert ROUTE_ZONE_PASS3_BASE_COST[RouteZone.INTERNAL_VOID] == 50.0
    assert ROUTE_ZONE_PASS3_BASE_COST[RouteZone.FILLABLE_INTERIOR] == 150.0
    assert ROUTE_ZONE_PASS3_BASE_COST[RouteZone.PLACEMENT_CANDIDATE] == 400.0
    assert ROUTE_ZONE_PASS3_BASE_COST[RouteZone.PLACEMENT_OCCUPIED] == 900.0
    assert ROUTE_ZONE_PASS3_BASE_COST[RouteZone.BLOCKED] == float("inf")


def test_transport_kind_route_zone_multiplier_matches_canon_11_2() -> None:
    assert set(TRANSPORT_KIND_ROUTE_ZONE_MULTIPLIER) == set(TransportKind)
    assert TRANSPORT_KIND_ROUTE_ZONE_MULTIPLIER[TransportKind.SHAPE_BELT] == 1.0
    assert TRANSPORT_KIND_ROUTE_ZONE_MULTIPLIER[TransportKind.FLUID_PIPE] == 1.0
