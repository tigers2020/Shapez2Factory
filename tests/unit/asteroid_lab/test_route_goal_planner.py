"""Route goal planner tests (Solver Runtime PR2.5)."""

from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.optimization.capacity_planner import plan_capacity
from django_apps.asteroid_lab.optimization.coords import neighbors4_server
from django_apps.asteroid_lab.optimization.enums import RouteGoalKind, TransportKind
from django_apps.asteroid_lab.optimization.input_contracts import (
    BBox,
    greenfield_optimization_input,
)
from django_apps.asteroid_lab.optimization.route_goal_planner import (
    MIN_RIM_VOID_DISTANCE,
    _distance_to_mineable,
    _eligible_void_cells,
    plan_route_goals,
)


def _large_void_grid_input() -> tuple:
    """5x5 mineable block centered in 15x15 bbox — void ring allows rim distance >= 5."""

    bb = BBox(0, 14, 0, 14)
    mineable = frozenset((cx, cy) for cx in range(5, 10) for cy in range(5, 10))
    rim_set: set[tuple[int, int]] = set()
    for sv in mineable:
        if any(n not in mineable for n in neighbors4_server(sv)):
            rim_set.add(sv)
    rim = frozenset(rim_set)
    interior = mineable - rim
    external_void = frozenset(
        (sx, sy)
        for sx in range(bb.min_sx, bb.max_sx + 1)
        for sy in range(bb.min_sy, bb.max_sy + 1)
        if (sx, sy) not in mineable
    )
    inp = greenfield_optimization_input(bbox=bb)
    return replace(
        inp,
        asteroid_cells=mineable,
        mineable_cells=mineable,
        rim_cells=rim,
        interior_cells=interior,
        external_void_cells=external_void,
    )


def test_route_goal_rim_distance_filter_excludes_near_void() -> None:
    inp = _large_void_grid_input()
    eligible = _eligible_void_cells(inp, min_distance=MIN_RIM_VOID_DISTANCE)
    bb_cells = frozenset(
        (sx, sy)
        for sx in range(inp.bbox.min_sx, inp.bbox.max_sx + 1)
        for sy in range(inp.bbox.min_sy, inp.bbox.max_sy + 1)
    )
    dist_map = _distance_to_mineable(inp.mineable_cells, bbox_cells=bb_cells)
    near = (4, 4)
    assert near in inp.external_void_cells
    assert dist_map[near] < MIN_RIM_VOID_DISTANCE
    assert all(dist_map[c] >= MIN_RIM_VOID_DISTANCE for c, _ in eligible)


def test_route_goal_planner_creates_multiple_external_margin_goals() -> None:
    inp = _large_void_grid_input()
    capacity = replace(
        plan_capacity(mineable_cell_count=len(inp.mineable_cells)),
        shape_goal_count=2,
        fluid_goal_count=1,
    )
    planned = plan_route_goals(inp, capacity)
    shape_goals = [g for g in planned.goals if g.transport_kind == TransportKind.SHAPE_BELT]
    fluid_goals = [g for g in planned.goals if g.transport_kind == TransportKind.FLUID_PIPE]
    assert len(shape_goals) == 2
    assert len(fluid_goals) == 1
    for g in planned.goals:
        assert g.goal_kind == RouteGoalKind.EXTERNAL_MARGIN
        assert g.coord in inp.external_void_cells


def test_route_goal_planner_does_not_materialize_transport() -> None:
    inp = _large_void_grid_input()
    capacity = plan_capacity(mineable_cell_count=len(inp.mineable_cells))
    before_transport = inp.existing_transport_cells
    plan_route_goals(inp, capacity)
    assert inp.existing_transport_cells == before_transport


def test_route_goals_bilateral_left_right_even_y() -> None:
    inp = _large_void_grid_input()
    min_sx = min(c[0] for c in inp.mineable_cells)
    max_sx = max(c[0] for c in inp.mineable_cells)
    band = max(2, (max_sx - min_sx + 1) // 8)
    capacity = replace(
        plan_capacity(mineable_cell_count=len(inp.mineable_cells)),
        shape_goal_count=4,
        fluid_goal_count=0,
    )
    planned = plan_route_goals(inp, capacity)
    assert planned.spread_axis == "x"
    assert planned.selected_cardinal is None
    shape_goals = [g for g in planned.goals if g.transport_kind == TransportKind.SHAPE_BELT]
    assert len(shape_goals) == 4
    left = [g for g in shape_goals if g.coord[0] <= min_sx + band]
    right = [g for g in shape_goals if g.coord[0] >= max_sx - band]
    assert len(left) == 2
    assert len(right) == 2
    ys = sorted(g.coord[1] for g in shape_goals)
    assert len(set(ys)) >= 2
    assert ys[-1] - ys[0] >= 1
    assert min(g.coord[0] for g in left) < max(g.coord[0] for g in right)


def test_route_goal_planner_records_shortfall_when_eligible_sparse() -> None:
    inp = _large_void_grid_input()
    capacity = replace(
        plan_capacity(mineable_cell_count=len(inp.mineable_cells)),
        shape_goal_count=100,
        fluid_goal_count=50,
    )
    planned = plan_route_goals(inp, capacity)
    assert planned.shape_goals_shortfall > 0
    assert planned.shape_goals_placed < planned.shape_goals_requested
