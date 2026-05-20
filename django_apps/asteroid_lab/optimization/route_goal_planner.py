"""Phase C — planned external RouteGoals without transport materialization (PR2.5)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.capacity_planner import CapacityPlan
from django_apps.asteroid_lab.optimization.coords import Coord, neighbors4_server
from django_apps.asteroid_lab.optimization.enums import Direction, RouteGoalKind, TransportKind
from django_apps.asteroid_lab.optimization.input_contracts import (
    MAX_GOAL_DISTANCE_FROM_MINEABLE,
    MIN_GOAL_DISTANCE_FROM_MINEABLE,
    OptimizationInput,
    RouteGoal,
    cells_in_bbox,
)


@dataclass(frozen=True, slots=True)
class PlannedRouteGoals:
    """Phase C output — goals only, no belt/pipe placement."""

    goals: frozenset[RouteGoal]
    capacity_plan: CapacityPlan
    shape_goals_requested: int
    shape_goals_placed: int
    fluid_goals_requested: int
    fluid_goals_placed: int
    selected_cardinal: Direction | None
    spread_axis: str | None

    @property
    def shape_goals_shortfall(self) -> int:
        return max(0, self.shape_goals_requested - self.shape_goals_placed)

    @property
    def fluid_goals_shortfall(self) -> int:
        return max(0, self.fluid_goals_requested - self.fluid_goals_placed)


def _mineable_extent(mineable: frozenset[Coord]) -> tuple[int, int, int, int]:
    if not mineable:
        return 0, 0, 0, 0
    xs = [c[0] for c in mineable]
    ys = [c[1] for c in mineable]
    return min(xs), max(xs), min(ys), max(ys)


def _distance_to_mineable(
    mineable: frozenset[Coord],
    *,
    bbox_cells: frozenset[Coord],
) -> dict[Coord, int]:
    """Layered BFS distance from mineable cells within ``bbox_cells`` (bounded)."""

    if not mineable:
        return {}
    dist: dict[Coord, int] = {m: 0 for m in mineable}
    frontier: set[Coord] = set(mineable)
    step = 0
    while frontier:
        step += 1
        next_frontier: set[Coord] = set()
        for current in frontier:
            for neighbor in neighbors4_server(current):
                if neighbor in dist:
                    continue
                if neighbor not in bbox_cells:
                    continue
                dist[neighbor] = step
                next_frontier.add(neighbor)
        frontier = next_frontier
    return dist


def _eligible_void_cells(
    inp: OptimizationInput,
    *,
    min_distance: int = MIN_GOAL_DISTANCE_FROM_MINEABLE,
    max_distance: int = MAX_GOAL_DISTANCE_FROM_MINEABLE,
) -> list[tuple[Coord, int]]:
    """Void cells with mineable BFS distance in ``[min_distance, max_distance]``."""

    bb_cells = cells_in_bbox(inp.route_domain_bbox)
    if len(bb_cells) > 50_000:
        return []
    dist_map = _distance_to_mineable(inp.mineable_cells, bbox_cells=bb_cells)
    eligible: list[tuple[Coord, int]] = []
    for coord in inp.external_void_cells:
        d = dist_map.get(coord)
        if d is not None and min_distance <= d <= max_distance:
            eligible.append((coord, d))
    return eligible


def _side_band_width(span: int) -> int:
    return max(2, span // 8)


def _evenly_spaced_int_targets(min_v: int, max_v: int, count: int) -> list[int]:
    """Place ``count`` targets inside ``[min_v, max_v]`` with span / (count + 1) spacing."""

    if count <= 0:
        return []
    span = max_v - min_v + 1
    step = span / (count + 1)
    return [round(min_v + step * (i + 1)) for i in range(count)]


def _split_bilateral_pools(
    eligible: list[tuple[Coord, int]],
    *,
    mineable: frozenset[Coord],
) -> tuple[
    list[tuple[Coord, int]],
    list[tuple[Coord, int]],
    str,
    int,
    int,
    int,
    int,
]:
    """Split eligible void into pools on the two **wide** faces of the mineable bbox.

    ``width >= height`` → top/bottom bands (long horizontal rims); else left/right.
    """

    min_sx, max_sx, min_sy, max_sy = _mineable_extent(mineable)
    width = max_sx - min_sx + 1
    height = max_sy - min_sy + 1
    if width >= height:
        band = _side_band_width(width)
        first = [(c, d) for c, d in eligible if c[1] <= min_sy + band]
        second = [(c, d) for c, d in eligible if c[1] >= max_sy - band]
        spread_axis = "x"
        spread_min, spread_max = min_sx, max_sx
    else:
        band = _side_band_width(height)
        first = [(c, d) for c, d in eligible if c[0] <= min_sx + band]
        second = [(c, d) for c, d in eligible if c[0] >= max_sx - band]
        spread_axis = "y"
        spread_min, spread_max = min_sy, max_sy
    return first, second, spread_axis, spread_min, spread_max, min_sx, max_sx


def _pick_on_side(
    pool: list[tuple[Coord, int]],
    target_spread: int,
    used: set[Coord],
    *,
    spread_axis: str,
    outer_side: str,
) -> Coord | None:
    available = [(c, d) for c, d in pool if c not in used]
    if not available:
        return None

    def key(item: tuple[Coord, int]) -> tuple[int, int, int, int, int]:
        coord, dist = item
        if spread_axis == "x":
            spread_delta = abs(coord[0] - target_spread)
            if outer_side == "first":
                lateral = (coord[1], abs(coord[1]))
            else:
                lateral = (-coord[1], abs(coord[1]))
        else:
            spread_delta = abs(coord[1] - target_spread)
            if outer_side == "first":
                lateral = (coord[0], abs(coord[0]))
            else:
                lateral = (-coord[0], abs(coord[0]))
        return (spread_delta, lateral[0], lateral[1], -dist, coord[0], coord[1])

    return min(available, key=key)[0]


def _place_bilateral_even(
    eligible: list[tuple[Coord, int]],
    *,
    mineable: frozenset[Coord],
    total_count: int,
    used: set[Coord],
) -> tuple[list[Coord], str | None]:
    """Place goals on both wide faces with even spacing along the long rim axis."""

    if total_count <= 0 or not eligible:
        return [], None

    first_pool, second_pool, spread_axis, spread_min, spread_max, _, _ = _split_bilateral_pools(
        eligible, mineable=mineable
    )
    if not first_pool and not second_pool:
        return [], spread_axis

    first_count = total_count // 2
    second_count = total_count - first_count
    targets_first = _evenly_spaced_int_targets(spread_min, spread_max, first_count)
    targets_second = _evenly_spaced_int_targets(spread_min, spread_max, second_count)

    picked: list[Coord] = []
    for target in targets_first:
        coord = _pick_on_side(
            first_pool,
            target,
            used,
            spread_axis=spread_axis,
            outer_side="first",
        )
        if coord is None:
            continue
        used.add(coord)
        picked.append(coord)

    for target in targets_second:
        coord = _pick_on_side(
            second_pool,
            target,
            used,
            spread_axis=spread_axis,
            outer_side="second",
        )
        if coord is None:
            continue
        used.add(coord)
        picked.append(coord)

    return picked, spread_axis


def plan_route_goals(
    inp: OptimizationInput,
    capacity: CapacityPlan,
    *,
    default_priority: int = 20,
    min_goal_distance: int = MIN_GOAL_DISTANCE_FROM_MINEABLE,
    max_goal_distance: int = MAX_GOAL_DISTANCE_FROM_MINEABLE,
) -> PlannedRouteGoals:
    """Place external margin goals on both wide faces (mineable distance band)."""

    shape_requested = capacity.shape_goal_count
    fluid_requested = capacity.fluid_goal_count
    eligible = _eligible_void_cells(
        inp,
        min_distance=min_goal_distance,
        max_distance=max_goal_distance,
    )
    used: set[Coord] = set()

    shape_coords, spread_axis = _place_bilateral_even(
        eligible,
        mineable=inp.mineable_cells,
        total_count=shape_requested,
        used=used,
    )
    fluid_coords, fluid_axis = _place_bilateral_even(
        eligible,
        mineable=inp.mineable_cells,
        total_count=fluid_requested,
        used=used,
    )
    if spread_axis is None:
        spread_axis = fluid_axis

    goals: set[RouteGoal] = set()
    for coord in shape_coords:
        goals.add(
            RouteGoal(
                coord=coord,
                goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
                transport_kind=TransportKind.SHAPE_BELT,
                priority=default_priority,
                existing_trunk=False,
            )
        )
    for coord in fluid_coords:
        goals.add(
            RouteGoal(
                coord=coord,
                goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
                transport_kind=TransportKind.FLUID_PIPE,
                priority=default_priority,
                existing_trunk=False,
            )
        )

    return PlannedRouteGoals(
        goals=frozenset(goals),
        capacity_plan=capacity,
        shape_goals_requested=shape_requested,
        shape_goals_placed=len(shape_coords),
        fluid_goals_requested=fluid_requested,
        fluid_goals_placed=len(fluid_coords),
        selected_cardinal=None,
        spread_axis=spread_axis,
    )
