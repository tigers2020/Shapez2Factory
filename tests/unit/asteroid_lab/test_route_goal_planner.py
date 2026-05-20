"""Route goal planner tests (Solver Runtime PR2.5)."""

from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.optimization.capacity_planner import plan_capacity
from django_apps.asteroid_lab.optimization.enums import RouteGoalKind, TransportKind
from django_apps.asteroid_lab.optimization.input_contracts import (
    BBox,
    greenfield_optimization_input,
)
from django_apps.asteroid_lab.optimization.route_goal_planner import plan_route_goals


def _void_grid_input() -> tuple:
    """3x3 mineable center with void ring in bbox 0..4."""

    bb = BBox(0, 4, 0, 4)
    from django_apps.asteroid_lab.optimization.coords import neighbors4_server

    mineable = frozenset((cx, cy) for cx in range(1, 4) for cy in range(1, 4))
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


def test_route_goal_planner_creates_multiple_external_margin_goals() -> None:
    inp = _void_grid_input()
    capacity = plan_capacity(
        mineable_cell_count=len(inp.mineable_cells),
        shape_platform_count=24,
        fluid_platform_count=72,
    )
    planned = plan_route_goals(inp, capacity)
    shape_goals = [g for g in planned.goals if g.transport_kind == TransportKind.SHAPE_BELT]
    fluid_goals = [g for g in planned.goals if g.transport_kind == TransportKind.FLUID_PIPE]
    assert len(shape_goals) >= 2
    assert len(fluid_goals) >= 1
    for g in planned.goals:
        assert g.goal_kind == RouteGoalKind.EXTERNAL_MARGIN
        assert g.coord in inp.external_void_cells


def test_route_goal_planner_does_not_materialize_transport() -> None:
    inp = _void_grid_input()
    capacity = plan_capacity(
        mineable_cell_count=len(inp.mineable_cells),
        shape_platform_count=12,
        fluid_platform_count=72,
    )
    before_transport = inp.existing_transport_cells
    plan_route_goals(inp, capacity)
    assert inp.existing_transport_cells == before_transport


def test_route_goal_planner_distributes_goals_by_quadrant() -> None:
    inp = _void_grid_input()
    capacity = plan_capacity(
        mineable_cell_count=len(inp.mineable_cells),
        shape_platform_count=48,
        fluid_platform_count=0,
    )
    capacity = replace(
        capacity,
        shape_goal_count=4,
        fluid_goal_count=0,
        estimated_shape_platforms=48,
    )
    planned = plan_route_goals(inp, capacity)
    shape_goals = [g for g in planned.goals if g.transport_kind == TransportKind.SHAPE_BELT]
    assert len(shape_goals) == 4
    bb = inp.bbox
    cx = (bb.min_sx + bb.max_sx) / 2.0
    cy = (bb.min_sy + bb.max_sy) / 2.0
    quadrants: set[int] = set()
    for g in shape_goals:
        sx, sy = g.coord
        east = sx >= cx
        south = sy >= cy
        q = (2 if south else 0) + (1 if east else 0)
        quadrants.add(q)
    assert len(quadrants) >= 3
