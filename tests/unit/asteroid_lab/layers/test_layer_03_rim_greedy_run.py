"""Rim greedy layer run entry (skeleton)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from django_apps.asteroid_lab.reconstruction.complete_map import build_reconstruction_complete_map
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string,
    load_reconstruction_fixture_line_pairs,
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
