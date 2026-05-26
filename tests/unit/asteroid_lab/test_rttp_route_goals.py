"""RTTP probe goal coords — EVTC selected connectors only."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.routing.route_goals import probe_goal_coords
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder


def test_probe_goal_coords_match_selected_connectors_only(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    from dataclasses import replace

    from django_apps.asteroid_lab.optimization.routing.exterior_connector_planner import (
        plan_exterior_connectors,
    )

    base = greenfield_optimization_input
    plan = plan_exterior_connectors(
        base,
        required_count=2,
        transport_kind=base.transport_kind,
    )
    inp = replace(
        base,
        route_goals=plan.selected_goals,
        required_external_connector_count=2,
    )
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())

    goals = probe_goal_coords(inp, skeleton)
    expected = frozenset(
        goal.coord
        for goal in inp.route_goals
        if goal.transport_kind is None or goal.transport_kind is inp.transport_kind
    )
    assert goals == expected
    for port in skeleton.ring_ports:
        if port.coord not in expected:
            assert port.coord not in goals


def test_probe_goal_coords_legacy_includes_ring_ports(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    inp = greenfield_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    goals = probe_goal_coords(inp, skeleton)
    for port in skeleton.ring_ports:
        assert port.coord in goals
