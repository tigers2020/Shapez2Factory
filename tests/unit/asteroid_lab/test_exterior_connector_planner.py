"""EVTC-2 — exterior connector planner."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.routing.exterior_connector_planner import (
    plan_exterior_connectors,
)
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder


def test_planner_emits_exactly_required_goals(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    inp = greenfield_optimization_input
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    plan = plan_exterior_connectors(
        inp,
        skeleton=skeleton,
        required_count=3,
        transport_kind=inp.transport_kind,
    )
    assert len(plan.selected_goals) == 3
    for goal in plan.selected_goals:
        assert goal.coord in inp.external_void_cells


def test_planner_shortfall_when_insufficient_void(greenfield_optimization_input: OptimizationInput) -> None:
    inp = greenfield_optimization_input
    plan = plan_exterior_connectors(
        inp,
        required_count=10_000,
        transport_kind=inp.transport_kind,
    )
    assert plan.planner_shortfall is True
    assert len(plan.selected_goals) < 10_000


def test_planner_deterministic_ordering(greenfield_optimization_input: OptimizationInput) -> None:
    inp = greenfield_optimization_input
    first = plan_exterior_connectors(inp, required_count=2, transport_kind=inp.transport_kind)
    second = plan_exterior_connectors(inp, required_count=2, transport_kind=inp.transport_kind)
    assert first.selected_goals == second.selected_goals
