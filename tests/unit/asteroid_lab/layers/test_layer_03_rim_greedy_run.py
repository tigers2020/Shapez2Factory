"""Rim greedy layer run entry (skeleton)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.plan import (
    build_exterior_connection_plan,
)
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.greedy_seed import (
    DEFAULT_GREEDY_SEEDS,
)
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from django_apps.asteroid_lab.reconstruction.complete_map import build_reconstruction_complete_map
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string,
    load_reconstruction_fixture_line_pairs,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport import (
    plan as plan_mod,
)
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import (
    build_rect_field_with_void_shell,
)


@pytest.fixture
def canonical_complete_map():
    required_copy, _solved = load_reconstruction_fixture_line_pairs()[1]
    snap = decode_shapez_copy_string(required_copy)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    return build_reconstruction_complete_map(cleanup=cleanup, recon=recon)


@pytest.fixture
def budget_ctx() -> LayerBudgetContext:
    return LayerBudgetContext.from_budget_ms(60_000)


def test_run_returns_empty_when_exterior_plan_missing(
    canonical_complete_map,
    budget_ctx: LayerBudgetContext,
) -> None:
    result = run_layer_03_rim_greedy_placement(
        complete_map=canonical_complete_map,
        exterior_plan=None,
        budget_ctx=budget_ctx,
    )
    assert result.metrics.layer_skip_reason == "missing_exterior_connection_plan"


@pytest.mark.django_db
def test_partial_exterior_plan_does_not_skip_no_route_goals(
    canonical_complete_map,
    budget_ctx: LayerBudgetContext,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cm = build_rect_field_with_void_shell(width=10, height=10, void_pad=12)
    fake_slots = {
        CardinalEdge.NORTH: [(0, -12), (5, -12), (10, -12)],
        CardinalEdge.EAST: [(22, 5), (22, 10)],
        CardinalEdge.SOUTH: [],
        CardinalEdge.WEST: [],
    }
    monkeypatch.setattr(
        plan_mod,
        "build_candidate_slots_by_edge",
        lambda _cm: fake_slots,
    )
    exterior_plan = build_exterior_connection_plan(
        complete_map=cm,
        resource_kind="shape",
        terrain_upper_bound_per_min=Decimal("999999"),
        throughput_target_percent=100,
        speed_tier=1,
    )
    assert exterior_plan.planned_connectors

    result = run_layer_03_rim_greedy_placement(
        complete_map=canonical_complete_map,
        exterior_plan=exterior_plan,
        budget_ctx=budget_ctx,
        seed_catalog=DEFAULT_GREEDY_SEEDS,
    )
    assert result.metrics.layer_skip_reason != "no_route_goals"
