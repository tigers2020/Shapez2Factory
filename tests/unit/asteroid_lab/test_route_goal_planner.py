"""Route goal planner tests (Solver Runtime PR2.5)."""

from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.optimization.capacity_planner import plan_capacity
from django_apps.asteroid_lab.optimization.coords import neighbors4_server
from django_apps.asteroid_lab.optimization.enums import RouteGoalKind, TransportKind
from django_apps.asteroid_lab.optimization.input_contracts import (
    MAX_GOAL_DISTANCE_FROM_MINEABLE,
    MIN_GOAL_DISTANCE_FROM_MINEABLE,
    BBox,
    cells_in_bbox,
    greenfield_optimization_input,
)
from django_apps.asteroid_lab.optimization.route_goal_planner import (
    _distance_to_mineable,
    _eligible_void_cells,
    plan_route_goals,
)


def _large_void_grid_input() -> tuple:
    """5x5 mineable centered; route domain 15x15 with void band for goal distance 3–5."""

    mineable = frozenset((cx, cy) for cx in range(5, 10) for cy in range(5, 10))
    asteroid_bb = BBox(5, 9, 5, 9)
    route_bb = BBox(0, 14, 0, 14)
    rim_set: set[tuple[int, int]] = set()
    for sv in mineable:
        if any(n not in mineable for n in neighbors4_server(sv)):
            rim_set.add(sv)
    rim = frozenset(rim_set)
    interior = mineable - rim
    external_void = frozenset(c for c in cells_in_bbox(route_bb) if c not in mineable)
    inp = greenfield_optimization_input(bbox=route_bb)
    return replace(
        inp,
        asteroid_cells=mineable,
        mineable_cells=mineable,
        rim_cells=rim,
        interior_cells=interior,
        external_void_cells=external_void,
        asteroid_bbox=asteroid_bb,
        route_domain_bbox=route_bb,
        bbox=route_bb,
    )


def test_route_goal_distance_band_excludes_near_and_far_void() -> None:
    inp = _large_void_grid_input()
    eligible = _eligible_void_cells(inp)
    bb_cells = cells_in_bbox(inp.route_domain_bbox)
    dist_map = _distance_to_mineable(inp.mineable_cells, bbox_cells=bb_cells)
    near = (4, 5)
    far = (0, 0)
    assert near in inp.external_void_cells
    assert far in inp.external_void_cells
    assert dist_map[near] < MIN_GOAL_DISTANCE_FROM_MINEABLE
    assert dist_map[far] > MAX_GOAL_DISTANCE_FROM_MINEABLE
    assert all(
        MIN_GOAL_DISTANCE_FROM_MINEABLE <= dist_map[c] <= MAX_GOAL_DISTANCE_FROM_MINEABLE
        for c, _ in eligible
    )


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


def test_route_goals_bilateral_wide_faces_top_bottom_even_x() -> None:
    """Square/wide mineable → goals on top/bottom (wide faces), even spread along x."""

    inp = _large_void_grid_input()
    min_sy = min(c[1] for c in inp.mineable_cells)
    max_sy = max(c[1] for c in inp.mineable_cells)
    xs = [c[0] for c in inp.mineable_cells]
    band = max(2, (max(xs) - min(xs) + 1) // 8)
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
    top = [g for g in shape_goals if g.coord[1] <= min_sy + band]
    bottom = [g for g in shape_goals if g.coord[1] >= max_sy - band]
    assert len(top) == 2
    assert len(bottom) == 2
    xs = sorted(g.coord[0] for g in shape_goals)
    assert len(set(xs)) >= 2
    assert xs[-1] - xs[0] >= 1
    assert min(g.coord[1] for g in top) < max(g.coord[1] for g in bottom)


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
