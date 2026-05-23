"""Probe/commit goal coord union (adapter goals + skeleton ring ports)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


def probe_goal_coords(
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
) -> frozenset[Coord]:
    """Coords reachable by route probe: ``route_goals`` plus skeleton ``ring_ports``."""

    goals: set[Coord] = set()
    for goal in inp.route_goals:
        if goal.transport_kind is None or goal.transport_kind is inp.transport_kind:
            goals.add(goal.coord)
    for port in skeleton.ring_ports:
        goals.add(port.coord)
    return frozenset(goals)


__all__ = ["probe_goal_coords"]
