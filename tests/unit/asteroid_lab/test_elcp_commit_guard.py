"""ELCP commit guard — LNS replacement predicate (Run #238 regression)."""

from __future__ import annotations

from decimal import Decimal

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import (
    ExteriorLaneCapacityPlan,
    ExteriorTransportLane,
)
from django_apps.asteroid_lab.optimization.commit.elcp_commit_guard import (
    elcp_plan_is_active,
    is_elcp_incomplete_commit_result,
    retry_may_replace_best,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import CommitResult
from django_apps.asteroid_lab.optimization.input_contracts import (
    RouteGoal,
    RouteGoalKind,
    TransportKind,
)


def _goal(coord: tuple[int, int]) -> RouteGoal:
    return RouteGoal(
        coord=coord,
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=20,
        existing_trunk=False,
    )


def _plan(*, required_lane_count: int = 1) -> ExteriorLaneCapacityPlan:
    lanes = tuple(
        ExteriorTransportLane(
            lane_id=f"exterior_lane:shape_belt:{index}",
            transport_kind=TransportKind.SHAPE_BELT,
            connector_goal=_goal((5 + index, 5)),
            capacity_per_min=Decimal("2880"),
            target_load_per_min=Decimal("2880"),
            anchor_coord=(5 + index, 5),
        )
        for index in range(required_lane_count)
    )
    return ExteriorLaneCapacityPlan(
        transport_kind=TransportKind.SHAPE_BELT,
        max_asteroid_throughput_per_min=Decimal("5760"),
        lane_capacity_per_min=Decimal("2880"),
        required_lane_count=required_lane_count,
        lanes=lanes,
    )


def _commit_result(
    *,
    committed_ids: tuple[str, ...] = (),
    assignments: tuple[dict[str, object], ...] = (),
) -> CommitResult:
    return CommitResult(
        committed_ids=committed_ids,
        reserved_route_cells=frozenset(),
        domain_version=len(committed_ids),
        conflicts=(),
        exterior_lane_assignments=assignments,
    )


def test_elcp_plan_is_active_false_when_none() -> None:
    assert elcp_plan_is_active(None) is False


def test_elcp_plan_is_active_false_when_zero_lanes() -> None:
    assert elcp_plan_is_active(_plan(required_lane_count=0)) is False


def test_elcp_plan_is_active_true_when_required_lane_count_positive() -> None:
    assert elcp_plan_is_active(_plan(required_lane_count=2)) is True


def test_is_elcp_incomplete_false_when_plan_inactive() -> None:
    result = _commit_result(committed_ids=("a",), assignments=())
    assert is_elcp_incomplete_commit_result(exterior_lane_plan=None, commit_result=result) is False


def test_is_elcp_incomplete_false_when_no_commits() -> None:
    plan = _plan()
    result = _commit_result(committed_ids=(), assignments=())
    assert is_elcp_incomplete_commit_result(exterior_lane_plan=plan, commit_result=result) is False


def test_is_elcp_incomplete_false_when_cardinality_matches() -> None:
    plan = _plan()
    result = _commit_result(
        committed_ids=("a", "b"),
        assignments=(
            {"candidate_id": "a", "exterior_lane_id": "exterior_lane:shape_belt:0"},
            {"candidate_id": "b", "exterior_lane_id": "exterior_lane:shape_belt:0"},
        ),
    )
    assert is_elcp_incomplete_commit_result(exterior_lane_plan=plan, commit_result=result) is False


def test_is_elcp_incomplete_true_when_assignments_missing() -> None:
    plan = _plan()
    result = _commit_result(committed_ids=("a", "b"), assignments=())
    assert is_elcp_incomplete_commit_result(exterior_lane_plan=plan, commit_result=result) is True


def test_retry_may_replace_best_rejects_elcp_incomplete_higher_count() -> None:
    plan = _plan()
    primary = _commit_result(
        committed_ids=("keep",),
        assignments=(
            {"candidate_id": "keep", "exterior_lane_id": "exterior_lane:shape_belt:0"},
        ),
    )
    retry = _commit_result(
        committed_ids=("keep", "extra1", "extra2"),
        assignments=(),
    )
    assert (
        retry_may_replace_best(
            exterior_lane_plan=plan,
            best_result=primary,
            retry_result=retry,
        )
        is False
    )


def test_retry_may_replace_best_accepts_elcp_complete_higher_count() -> None:
    plan = _plan()
    primary = _commit_result(
        committed_ids=("keep",),
        assignments=(
            {"candidate_id": "keep", "exterior_lane_id": "exterior_lane:shape_belt:0"},
        ),
    )
    retry = _commit_result(
        committed_ids=("keep", "extra"),
        assignments=(
            {"candidate_id": "keep", "exterior_lane_id": "exterior_lane:shape_belt:0"},
            {"candidate_id": "extra", "exterior_lane_id": "exterior_lane:shape_belt:0"},
        ),
    )
    assert (
        retry_may_replace_best(
            exterior_lane_plan=plan,
            best_result=primary,
            retry_result=retry,
        )
        is True
    )


def test_retry_may_replace_best_unchanged_when_plan_inactive() -> None:
    primary = _commit_result(committed_ids=("a",))
    retry = _commit_result(committed_ids=("a", "b", "c"))
    assert (
        retry_may_replace_best(
            exterior_lane_plan=None,
            best_result=primary,
            retry_result=retry,
        )
        is True
    )
