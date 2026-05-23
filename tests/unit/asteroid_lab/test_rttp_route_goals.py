"""RTTP probe goal coords — ring ports included (review blocker I2)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.routing.route_goals import probe_goal_coords
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder


def test_probe_goal_coords_include_ring_ports(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    inp = greenfield_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())

    assert skeleton.ring_ports
    goals = probe_goal_coords(inp, skeleton)
    adapter_only = frozenset(
        goal.coord
        for goal in inp.route_goals
        if goal.transport_kind is None or goal.transport_kind is inp.transport_kind
    )

    for port in skeleton.ring_ports:
        assert port.coord in goals

    assert goals >= adapter_only
