"""Phase C — planned external RouteGoals without transport materialization (PR2.5)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.asteroid_lab.optimization.capacity_planner import CapacityPlan
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.enums import RouteGoalKind, TransportKind
from django_apps.asteroid_lab.optimization.input_contracts import BBox, OptimizationInput, RouteGoal


@dataclass(frozen=True, slots=True)
class PlannedRouteGoals:
    """Phase C output — goals only, no belt/pipe placement."""

    goals: frozenset[RouteGoal]
    capacity_plan: CapacityPlan


def _margin_distance(coord: Coord, bb: BBox) -> int:
    sx, sy = coord
    return min(sx - bb.min_sx, bb.max_sx - sx, sy - bb.min_sy, bb.max_sy - sy)


def _quadrant(coord: Coord, bb: BBox) -> int:
    """0=NW, 1=NE, 2=SW, 3=SE relative to bbox center."""

    cx = (bb.min_sx + bb.max_sx) / 2.0
    cy = (bb.min_sy + bb.max_sy) / 2.0
    sx, sy = coord
    east = sx >= cx
    south = sy >= cy
    if not east and not south:
        return 0
    if east and not south:
        return 1
    if not east and south:
        return 2
    return 3


def _rank_void_candidates(void_cells: frozenset[Coord], bb: BBox) -> list[Coord]:
    return sorted(
        void_cells,
        key=lambda c: (_margin_distance(c, bb), _quadrant(c, bb), c[0], c[1]),
    )


def _pick_spread(ranked: list[Coord], bb: BBox, count: int) -> list[Coord]:
    """Round-robin across quadrants for deterministic spread."""

    if count <= 0 or not ranked:
        return []
    buckets: dict[int, list[Coord]] = {0: [], 1: [], 2: [], 3: []}
    for c in ranked:
        buckets[_quadrant(c, bb)].append(c)

    picked: list[Coord] = []
    seen: set[Coord] = set()
    idx = 0
    while len(picked) < count:
        progressed = False
        for q in (0, 1, 2, 3):
            bucket = buckets[q]
            if idx < len(bucket):
                c = bucket[idx]
                if c not in seen:
                    picked.append(c)
                    seen.add(c)
                    if len(picked) >= count:
                        return picked
                progressed = True
        if not progressed:
            break
        idx += 1
    return picked


def plan_route_goals(
    inp: OptimizationInput,
    capacity: CapacityPlan,
    *,
    default_priority: int = 20,
) -> PlannedRouteGoals:
    """Create external margin goals on ``external_void_cells`` (no transport install)."""

    ranked = _rank_void_candidates(inp.external_void_cells, inp.bbox)
    shape_coords = _pick_spread(ranked, inp.bbox, capacity.shape_goal_count)
    shape_set = frozenset(shape_coords)
    remaining = [c for c in ranked if c not in shape_set]
    fluid_coords = _pick_spread(remaining, inp.bbox, capacity.fluid_goal_count)

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

    return PlannedRouteGoals(goals=frozenset(goals), capacity_plan=capacity)
