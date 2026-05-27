"""ELCP-TM Task 2 — trunk partition and state helpers."""

from __future__ import annotations

from decimal import Decimal

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import (
    ExteriorLaneCapacityPlan,
    ExteriorLaneTrunkState,
    ExteriorTransportLane,
)
from django_apps.asteroid_lab.optimization.commit.exterior_lane_trunk import (
    initial_trunk_states,
    partition_path_branch_and_trunk,
    shareable_trunk_cells_for_transport,
    shareable_trunk_cells_from_states,
    update_trunk_state_after_commit,
)
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


def _lane(lane_id: str, coord: tuple[int, int]) -> ExteriorTransportLane:
    goal = _goal(coord)
    cap = Decimal("2880")
    return ExteriorTransportLane(
        lane_id=lane_id,
        transport_kind=TransportKind.SHAPE_BELT,
        connector_goal=goal,
        capacity_per_min=cap,
        target_load_per_min=cap,
        anchor_coord=coord,
    )


def _plan(*lanes: ExteriorTransportLane) -> ExteriorLaneCapacityPlan:
    cap = lanes[0].capacity_per_min if lanes else Decimal("2880")
    return ExteriorLaneCapacityPlan(
        transport_kind=TransportKind.SHAPE_BELT,
        max_asteroid_throughput_per_min=cap * len(lanes),
        lane_capacity_per_min=cap,
        required_lane_count=len(lanes),
        lanes=lanes,
    )


def _state(trunk: frozenset[tuple[int, int]]) -> ExteriorLaneTrunkState:
    return ExteriorLaneTrunkState(
        lane_id="exterior_lane:shape_belt:0",
        transport_kind=TransportKind.SHAPE_BELT,
        active=True,
        assigned_load_per_min=Decimal("0"),
        trunk_cells=trunk,
        connector_coord=(3, 0),
    )


def test_initial_trunk_states_only_lane0_active() -> None:
    plan = _plan(
        _lane("exterior_lane:shape_belt:0", (0, 5)),
        _lane("exterior_lane:shape_belt:1", (0, 10)),
    )
    states = initial_trunk_states(plan)
    assert len(states) == 2
    assert states[0].active is True
    assert states[1].active is False


def test_partition_first_commit_establishes_trunk() -> None:
    path = ((0, 0), (1, 0), (2, 0), (3, 0))
    branch, reused, new_trunk = partition_path_branch_and_trunk(
        path=path,
        existing_trunk=frozenset(),
        connector_coord=(3, 0),
    )
    assert branch == ()
    assert reused == ()
    assert new_trunk == path


def test_partition_second_commit_reuses_trunk_with_branch_only() -> None:
    existing = frozenset({(1, 0), (2, 0), (3, 0)})
    path = ((0, 1), (0, 0), (1, 0), (2, 0))
    branch, reused, new_trunk = partition_path_branch_and_trunk(
        path=path,
        existing_trunk=existing,
        connector_coord=(3, 0),
    )
    assert branch == ((0, 1), (0, 0))
    assert reused == ((1, 0), (2, 0))
    assert new_trunk == ()


def test_shareable_trunk_union() -> None:
    s0 = _state(frozenset({(1, 0)}))
    s1 = ExteriorLaneTrunkState(
        lane_id="exterior_lane:shape_belt:1",
        transport_kind=TransportKind.SHAPE_BELT,
        active=True,
        assigned_load_per_min=Decimal("0"),
        trunk_cells=frozenset({(5, 0)}),
        connector_coord=(6, 0),
    )
    assert shareable_trunk_cells_from_states((s0, s1)) == frozenset({(1, 0), (5, 0)})


def test_shareable_trunk_cells_for_transport_filters_kind_and_adds_prospective() -> None:
    s_shape = _state(frozenset({(1, 0)}))
    s_fluid = ExteriorLaneTrunkState(
        lane_id="exterior_lane:fluid_pipe:0",
        transport_kind=TransportKind.FLUID_PIPE,
        active=True,
        assigned_load_per_min=Decimal("0"),
        trunk_cells=frozenset({(9, 9)}),
        connector_coord=(10, 9),
    )
    shareable = shareable_trunk_cells_for_transport(
        (s_shape, s_fluid),
        transport_kind=TransportKind.SHAPE_BELT,
        prospective_new_trunk=frozenset({(2, 0)}),
    )
    assert shareable == frozenset({(1, 0), (2, 0)})
    assert (9, 9) not in shareable


def test_update_trunk_state_merges_new_cells() -> None:
    state = _state(frozenset({(1, 0)}))
    updated = update_trunk_state_after_commit(
        state,
        new_trunk_cells=((2, 0), (3, 0)),
        assigned_delta=Decimal("480"),
    )
    assert updated.trunk_cells == frozenset({(1, 0), (2, 0), (3, 0)})
    assert updated.assigned_load_per_min == Decimal("480")
