"""EVTC-7 — route probe priority tie-break and weighted shortest path."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.routing.lift_lane_domain import RouteCellDomain
from django_apps.asteroid_lab.optimization.routing.route_probe import probe_route


def _mini_domain(
    *,
    traversable: frozenset[tuple[int, int]],
    trunk: frozenset[tuple[int, int]],
    step_costs: frozenset[tuple[tuple[int, int], int]],
) -> RouteCellDomain:
    return RouteCellDomain(
        blocked_cells=frozenset(),
        trunk_mask_cells=trunk,
        lift_edges=(),
        traversable_cells=traversable,
        step_costs=step_costs,
    )


def test_same_hop_count_prefers_higher_priority_goal() -> None:
    traversable = frozenset({(0, 0), (1, 0), (0, 1), (1, 1)})
    domain = _mini_domain(
        traversable=traversable,
        trunk=frozenset({(0, 0)}),
        step_costs=frozenset(),
    )
    start = (0, 0)
    goals = frozenset({(1, 0), (0, 1)})
    result = probe_route(domain, start, goals, goal_priority={(1, 0): 5, (0, 1): 99})
    assert result.reachable
    assert result.reached_goal == (0, 1)
    assert result.cost == 1


def test_weighted_probe_prefers_lower_cost_void_path() -> None:
    traversable = frozenset({(0, 0), (1, 0), (2, 0), (0, 1), (1, 1)})
    domain = _mini_domain(
        traversable=traversable,
        trunk=frozenset({(0, 1)}),
        step_costs=frozenset(
            {
                ((1, 0), 1),
                ((2, 0), 1),
                ((0, 1), 20),
            }
        ),
    )
    start = (0, 0)
    goals = frozenset({(2, 0), (0, 1)})
    first = probe_route(domain, start, goals, goal_priority={(2, 0): 1, (0, 1): 1})
    second = probe_route(domain, start, goals, goal_priority={(2, 0): 1, (0, 1): 1})
    assert first == second
    assert first.reachable
    assert first.reached_goal == (2, 0)
    assert first.cost < 8
