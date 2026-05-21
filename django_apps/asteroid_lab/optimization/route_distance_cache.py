"""Reverse multi-source distance maps for candidate-phase route prefilter."""

from __future__ import annotations

from collections import deque

from django_apps.asteroid_lab.optimization.coords import Coord, neighbors4_server
from django_apps.asteroid_lab.optimization.enums import TransportKind, TransportMask
from django_apps.asteroid_lab.optimization.input_contracts import RouteGoal
from django_apps.asteroid_lab.optimization.route_domain import RouteCellDomain
from django_apps.asteroid_lab.optimization.route_probe import _goal_cells, _mask_allows

DomainCellSig = tuple[Coord, bool, TransportMask]
GoalSig = tuple[Coord, int, str]


def domain_cells_signature(
    domain: dict[Coord, RouteCellDomain],
) -> tuple[DomainCellSig, ...]:
    return tuple(
        sorted((coord, cell.hard_blocked, cell.transport_mask) for coord, cell in domain.items())
    )


def goals_signature(
    goals: frozenset[RouteGoal],
    transport_kind: TransportKind,
) -> tuple[GoalSig, ...]:
    filtered = _goal_cells(goals, transport_kind)
    by_coord = {g.coord: g for g in goals if g.coord in filtered}
    return tuple(
        sorted(
            (
                coord,
                by_coord[coord].priority,
                by_coord[coord].goal_kind.value,
            )
            for coord in filtered
        )
    )


def distance_cache_key(
    domain: dict[Coord, RouteCellDomain],
    *,
    goals: frozenset[RouteGoal],
    transport_kind: TransportKind,
) -> tuple[object, ...]:
    return (
        domain_cells_signature(domain),
        goals_signature(goals, transport_kind),
        transport_kind,
    )


class RouteDistanceCache:
    """Per-run cache: one reverse BFS per (domain signature, goals, transport_kind)."""

    def __init__(self) -> None:
        self._maps: dict[tuple[object, ...], dict[Coord, int]] = {}

    def get_distance_map(
        self,
        domain: dict[Coord, RouteCellDomain],
        *,
        goals: frozenset[RouteGoal],
        transport_kind: TransportKind,
    ) -> dict[Coord, int]:
        key = distance_cache_key(domain, goals=goals, transport_kind=transport_kind)
        cached = self._maps.get(key)
        if cached is not None:
            return cached
        built = _build_reverse_distance_map(domain, goals=goals, transport_kind=transport_kind)
        self._maps[key] = built
        return built

    def clear(self) -> None:
        self._maps.clear()


def _build_reverse_distance_map(
    domain: dict[Coord, RouteCellDomain],
    *,
    goals: frozenset[RouteGoal],
    transport_kind: TransportKind,
) -> dict[Coord, int]:
    goal_cells = _goal_cells(goals, transport_kind)
    if not goal_cells:
        return {}

    dist: dict[Coord, int] = {}
    queue: deque[Coord] = deque()
    for goal in goal_cells:
        if goal not in domain:
            continue
        cell = domain[goal]
        if cell.hard_blocked:
            continue
        if not _mask_allows(transport_kind, cell.transport_mask):
            continue
        dist[goal] = 0
        queue.append(goal)

    while queue:
        current = queue.popleft()
        current_dist = dist[current]
        for nb in neighbors4_server(current):
            if nb in dist:
                continue
            if nb not in domain:
                continue
            cell = domain[nb]
            if cell.hard_blocked:
                continue
            if not _mask_allows(transport_kind, cell.transport_mask):
                continue
            dist[nb] = current_dist + 1
            queue.append(nb)
    return dist
