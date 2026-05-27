"""ELCP Task 5 — read-only exterior lane validation."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import (
    ACTIVATION_REASON_CAPACITY_EXHAUSTED,
    ExteriorLaneActivationEvidence,
    ExteriorLaneAssignmentState,
    ExteriorLaneCapacityPlan,
    ExteriorLaneCommitValidationSnapshot,
    ExteriorLaneRouteEvidence,
    ExteriorLaneTrunkState,
    ExteriorTransportLane,
)
from django_apps.asteroid_lab.contracts.rttp_layout_issue_codes import (
    ISSUE_CODE_EXTERIOR_LANE_BRANCH_NOT_CONNECTED_TO_TRUNK,
    ISSUE_CODE_EXTERIOR_LANE_OVER_CAPACITY,
    ISSUE_CODE_EXTERIOR_LANE_PREMATURE_ACTIVATION,
    ISSUE_CODE_EXTERIOR_LANE_TRUNK_NOT_SHARED,
    ISSUE_CODE_ROUTE_WITHOUT_LANE_ASSIGNMENT,
)
from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.pattern_library import build_pattern_library
from django_apps.asteroid_lab.optimization.commit.incremental_commit import CommitResult
from django_apps.asteroid_lab.optimization.input_contracts import (
    RouteGoal,
    RouteGoalKind,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.validation.validate_exterior_lane_contract import (
    validate_exterior_lane_contract_issues,
)


def _goal(coord: tuple[int, int]) -> RouteGoal:
    return RouteGoal(
        coord=coord,
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=20,
        existing_trunk=False,
    )


def _plan() -> ExteriorLaneCapacityPlan:
    lane = ExteriorTransportLane(
        lane_id="exterior_lane:shape_belt:0",
        transport_kind=TransportKind.SHAPE_BELT,
        connector_goal=_goal((5, 5)),
        capacity_per_min=Decimal("2880"),
        target_load_per_min=Decimal("2880"),
        anchor_coord=(5, 5),
    )
    return ExteriorLaneCapacityPlan(
        transport_kind=TransportKind.SHAPE_BELT,
        max_asteroid_throughput_per_min=Decimal("2880"),
        lane_capacity_per_min=Decimal("2880"),
        required_lane_count=1,
        lanes=(lane,),
    )


def _lin_e_len0_pattern() -> BundlePattern:
    for pattern in build_pattern_library():
        if pattern.pattern_id == "lin_e_len0":
            return pattern
    msg = "lin_e_len0 not found"
    raise AssertionError(msg)


def _shape_belt_candidate(candidate_id: str) -> BundleCandidate:
    pattern = _lin_e_len0_pattern()
    return BundleCandidate(
        candidate_id=candidate_id,
        anchor_coord=(0, 0),
        pattern=pattern,
        output_stub=(2, 0),
        output_dir=pattern.output_dir,
        occupied_cells=frozenset({(0, 0)}),
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=4,
        route_probe_cost=0,
        reachable=True,
    )


def _base_commit_result(**kwargs: object) -> CommitResult:
    base = CommitResult(
        committed_ids=("c1",),
        reserved_route_cells=frozenset(),
        domain_version=1,
        conflicts=(),
        exterior_lane_assignments=(
            {
                "candidate_id": "c1",
                "exterior_lane_id": "exterior_lane:shape_belt:0",
            },
        ),
        exterior_lane_assignment_state=(
            ExteriorLaneAssignmentState(
                lane_id="exterior_lane:shape_belt:0",
                assigned_load_per_min=Decimal("100"),
            ),
        ),
    )
    if not kwargs:
        return base
    return replace(base, **kwargs)


def _lane_snapshot(commit_result: CommitResult) -> ExteriorLaneCommitValidationSnapshot:
    return ExteriorLaneCommitValidationSnapshot(
        exterior_lane_assignments=commit_result.exterior_lane_assignments,
        exterior_lane_assignment_state=commit_result.exterior_lane_assignment_state,
        exterior_lane_activations=commit_result.exterior_lane_activations,
        exterior_lane_trunk_states=commit_result.exterior_lane_trunk_states,
        exterior_lane_route_evidence=commit_result.exterior_lane_route_evidence,
    )


def test_missing_lane_assignment_emits_issue() -> None:
    plan = _plan()
    commit_result = CommitResult(
        committed_ids=("c1",),
        reserved_route_cells=frozenset(),
        domain_version=1,
        conflicts=(),
    )
    issues = validate_exterior_lane_contract_issues(
        committed_ids=("c1",),
        lane_commit_snapshot=_lane_snapshot(commit_result),
        candidates_by_id={},
        exterior_lane_plan=plan,
    )
    assert ISSUE_CODE_ROUTE_WITHOUT_LANE_ASSIGNMENT in issues


def test_over_capacity_emits_issue() -> None:
    plan = _plan()
    commit_result = CommitResult(
        committed_ids=("c1",),
        reserved_route_cells=frozenset(),
        domain_version=1,
        conflicts=(),
        exterior_lane_assignments=(
            {
                "candidate_id": "c1",
                "exterior_lane_id": "exterior_lane:shape_belt:0",
            },
        ),
        exterior_lane_assignment_state=(
            ExteriorLaneAssignmentState(
                lane_id="exterior_lane:shape_belt:0",
                assigned_load_per_min=Decimal("3000"),
            ),
        ),
    )
    issues = validate_exterior_lane_contract_issues(
        committed_ids=("c1",),
        lane_commit_snapshot=_lane_snapshot(commit_result),
        candidates_by_id={},
        exterior_lane_plan=plan,
    )
    assert ISSUE_CODE_EXTERIOR_LANE_OVER_CAPACITY in issues


def test_validation_does_not_mutate_commit_result() -> None:
    plan = _plan()
    commit_result = CommitResult(
        committed_ids=(),
        reserved_route_cells=frozenset({(1, 1)}),
        domain_version=0,
        conflicts=(),
    )
    before = commit_result.reserved_route_cells
    validate_exterior_lane_contract_issues(
        committed_ids=(),
        lane_commit_snapshot=_lane_snapshot(commit_result),
        candidates_by_id={},
        exterior_lane_plan=plan,
    )
    assert commit_result.reserved_route_cells == before


def test_validation_does_not_mutate_commit_result_tm_fields() -> None:
    plan = _plan()
    trunk = ExteriorLaneTrunkState(
        lane_id="exterior_lane:shape_belt:0",
        transport_kind=TransportKind.SHAPE_BELT,
        active=True,
        assigned_load_per_min=Decimal("100"),
        trunk_cells=frozenset({(0, 0), (0, 1)}),
        connector_coord=(5, 5),
    )
    evidence = ExteriorLaneRouteEvidence(
        candidate_id="c1",
        lane_id="exterior_lane:shape_belt:0",
        candidate_throughput_per_min=Decimal("100"),
        branch_cells=((0, 2),),
        reused_trunk_cells=((0, 0), (0, 1)),
        new_trunk_cells=(),
        reached_connector_coord=None,
        reached_trunk_coord=None,
    )
    activation = ExteriorLaneActivationEvidence(
        activated_lane_id="exterior_lane:shape_belt:0",
        previous_lane_id="exterior_lane:shape_belt:0",
        previous_lane_assigned_load_per_min=Decimal("2800"),
        previous_lane_capacity_per_min=Decimal("2880"),
        trigger_candidate_id="c1",
        trigger_candidate_throughput_per_min=Decimal("200"),
        activation_reason=ACTIVATION_REASON_CAPACITY_EXHAUSTED,
    )
    commit_result = _base_commit_result(
        exterior_lane_trunk_states=(trunk,),
        exterior_lane_route_evidence=(evidence,),
        exterior_lane_activations=(activation,),
    )
    snapshot = _lane_snapshot(commit_result)
    snapshot_before = replace(snapshot)
    validate_exterior_lane_contract_issues(
        committed_ids=("c1",),
        lane_commit_snapshot=snapshot,
        candidates_by_id={"c1": _shape_belt_candidate("c1")},
        exterior_lane_plan=plan,
    )
    assert snapshot == snapshot_before


def test_premature_activation_bad_evidence() -> None:
    plan = _plan()
    activation = ExteriorLaneActivationEvidence(
        activated_lane_id="exterior_lane:shape_belt:0",
        previous_lane_id="exterior_lane:shape_belt:0",
        previous_lane_assigned_load_per_min=Decimal("100"),
        previous_lane_capacity_per_min=Decimal("2880"),
        trigger_candidate_id="c1",
        trigger_candidate_throughput_per_min=Decimal("50"),
        activation_reason="manual_open",
    )
    commit_result = _base_commit_result(exterior_lane_activations=(activation,))
    issues = validate_exterior_lane_contract_issues(
        committed_ids=("c1",),
        lane_commit_snapshot=_lane_snapshot(commit_result),
        candidates_by_id={"c1": _shape_belt_candidate("c1")},
        exterior_lane_plan=plan,
    )
    assert ISSUE_CODE_EXTERIOR_LANE_PREMATURE_ACTIVATION in issues


def test_premature_activation_when_capacity_not_exhausted() -> None:
    plan = _plan()
    activation = ExteriorLaneActivationEvidence(
        activated_lane_id="exterior_lane:shape_belt:0",
        previous_lane_id="exterior_lane:shape_belt:0",
        previous_lane_assigned_load_per_min=Decimal("100"),
        previous_lane_capacity_per_min=Decimal("2880"),
        trigger_candidate_id="c1",
        trigger_candidate_throughput_per_min=Decimal("50"),
        activation_reason=ACTIVATION_REASON_CAPACITY_EXHAUSTED,
    )
    commit_result = _base_commit_result(exterior_lane_activations=(activation,))
    issues = validate_exterior_lane_contract_issues(
        committed_ids=("c1",),
        lane_commit_snapshot=_lane_snapshot(commit_result),
        candidates_by_id={"c1": _shape_belt_candidate("c1")},
        exterior_lane_plan=plan,
    )
    assert ISSUE_CODE_EXTERIOR_LANE_PREMATURE_ACTIVATION in issues


def test_valid_capacity_exhausted_no_premature() -> None:
    plan = _plan()
    activation = ExteriorLaneActivationEvidence(
        activated_lane_id="exterior_lane:shape_belt:0",
        previous_lane_id="exterior_lane:shape_belt:0",
        previous_lane_assigned_load_per_min=Decimal("2800"),
        previous_lane_capacity_per_min=Decimal("2880"),
        trigger_candidate_id="c1",
        trigger_candidate_throughput_per_min=Decimal("200"),
        activation_reason=ACTIVATION_REASON_CAPACITY_EXHAUSTED,
    )
    commit_result = _base_commit_result(exterior_lane_activations=(activation,))
    issues = validate_exterior_lane_contract_issues(
        committed_ids=("c1",),
        lane_commit_snapshot=_lane_snapshot(commit_result),
        candidates_by_id={"c1": _shape_belt_candidate("c1")},
        exterior_lane_plan=plan,
    )
    assert ISSUE_CODE_EXTERIOR_LANE_PREMATURE_ACTIVATION not in issues


def test_disconnected_trunk_emits_issue() -> None:
    plan = _plan()
    trunk = ExteriorLaneTrunkState(
        lane_id="exterior_lane:shape_belt:0",
        transport_kind=TransportKind.SHAPE_BELT,
        active=True,
        assigned_load_per_min=Decimal("100"),
        trunk_cells=frozenset({(0, 0), (2, 2)}),
        connector_coord=(5, 5),
    )
    commit_result = _base_commit_result(exterior_lane_trunk_states=(trunk,))
    issues = validate_exterior_lane_contract_issues(
        committed_ids=("c1",),
        lane_commit_snapshot=_lane_snapshot(commit_result),
        candidates_by_id={"c1": _shape_belt_candidate("c1")},
        exterior_lane_plan=plan,
    )
    assert ISSUE_CODE_EXTERIOR_LANE_TRUNK_NOT_SHARED in issues


def test_branch_not_connected_emits_issue() -> None:
    plan = _plan()
    evidence = ExteriorLaneRouteEvidence(
        candidate_id="c1",
        lane_id="exterior_lane:shape_belt:0",
        candidate_throughput_per_min=Decimal("100"),
        branch_cells=((10, 10),),
        reused_trunk_cells=((0, 0),),
        new_trunk_cells=(),
        reached_connector_coord=None,
        reached_trunk_coord=None,
    )
    commit_result = _base_commit_result(exterior_lane_route_evidence=(evidence,))
    issues = validate_exterior_lane_contract_issues(
        committed_ids=("c1",),
        lane_commit_snapshot=_lane_snapshot(commit_result),
        candidates_by_id={"c1": _shape_belt_candidate("c1")},
        exterior_lane_plan=plan,
    )
    assert ISSUE_CODE_EXTERIOR_LANE_BRANCH_NOT_CONNECTED_TO_TRUNK in issues


def test_valid_branch_with_reused_trunk_no_tm_issue() -> None:
    plan = _plan()
    evidence = ExteriorLaneRouteEvidence(
        candidate_id="c1",
        lane_id="exterior_lane:shape_belt:0",
        candidate_throughput_per_min=Decimal("100"),
        branch_cells=((0, 1),),
        reused_trunk_cells=((0, 0),),
        new_trunk_cells=(),
        reached_connector_coord=None,
        reached_trunk_coord=None,
    )
    trunk = ExteriorLaneTrunkState(
        lane_id="exterior_lane:shape_belt:0",
        transport_kind=TransportKind.SHAPE_BELT,
        active=True,
        assigned_load_per_min=Decimal("100"),
        trunk_cells=frozenset({(0, 0), (0, 1)}),
        connector_coord=(5, 5),
    )
    commit_result = _base_commit_result(
        exterior_lane_route_evidence=(evidence,),
        exterior_lane_trunk_states=(trunk,),
    )
    issues = validate_exterior_lane_contract_issues(
        committed_ids=("c1",),
        lane_commit_snapshot=_lane_snapshot(commit_result),
        candidates_by_id={"c1": _shape_belt_candidate("c1")},
        exterior_lane_plan=plan,
    )
    assert ISSUE_CODE_EXTERIOR_LANE_BRANCH_NOT_CONNECTED_TO_TRUNK not in issues
    assert ISSUE_CODE_EXTERIOR_LANE_TRUNK_NOT_SHARED not in issues
    assert ISSUE_CODE_EXTERIOR_LANE_PREMATURE_ACTIVATION not in issues
