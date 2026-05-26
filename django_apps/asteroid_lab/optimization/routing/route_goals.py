"""Probe/commit goal coord union (adapter goals + skeleton ring ports)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton


def probe_goal_coords(
    inp: OptimizationInput,
    skeleton: RttpSkeleton,
) -> frozenset[Coord]:
    """Coords for route probe: EVTC selected connectors; legacy adds ring ports."""

    goals: set[Coord] = {
        goal.coord
        for goal in inp.route_goals
        if goal.transport_kind is None or goal.transport_kind is inp.transport_kind
    }
    if inp.required_external_connector_count is None:
        goals.update(port.coord for port in skeleton.ring_ports)
    return frozenset(goals)


def probe_goal_priorities(inp: OptimizationInput) -> dict[Coord, int]:
    """Per-goal priority for commit-time probe tie-break (EVTC-7a)."""

    return {
        goal.coord: goal.priority
        for goal in inp.route_goals
        if goal.transport_kind is None or goal.transport_kind is inp.transport_kind
    }


__all__ = ["probe_goal_coords", "probe_goal_priorities"]
