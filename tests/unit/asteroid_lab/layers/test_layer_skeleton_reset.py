"""Layer L2–L6 skeleton smoke after algorithm reset."""

from __future__ import annotations

from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import Layer03SkipReason
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_inner_fill import (
    Layer04SkipReason,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.provisional_overlay import (
    ProvisionalLayoutOverlay,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.run import (
    run_layer_05_transport_routing,
)
from shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill.run import (
    run_layer_04_inner_pattern_fill,
)
from tests.support.reconstruction_complete_map_fixtures import complete_map_from_overlay_cells


def _field_cell(x: int, y: int) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type="",
        cell_kind="asteroid_shape_field",
        transport_kind="none",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={"T": "AsteroidShapeField", "X": x, "Y": y},
    )


def _sample_complete_map():
    return complete_map_from_overlay_cells(_field_cell(0, 0))


def test_layer03_skips_without_exterior_plan() -> None:
    result = run_layer_03_rim_greedy_placement(
        complete_map=_sample_complete_map(),
        exterior_plan=None,
        budget_ctx=LayerBudgetContext.from_budget_ms(1000),
    )
    assert (
        result.metrics.layer_skip_reason
        == Layer03SkipReason.MISSING_EXTERIOR_CONNECTION_PLAN.value
    )
    assert result.committed_placements == ()


def test_layer04_inner_fill_skeleton_deferred() -> None:
    result = run_layer_04_inner_pattern_fill(
        complete_map=_sample_complete_map(),
        exterior_plan=None,
        provisional_overlay=ProvisionalLayoutOverlay.empty(),
        budget_ctx=LayerBudgetContext.from_budget_ms(1000),
    )
    assert result.skip_reason is Layer04SkipReason.MACRO_ONLY_DEFERRED
    assert result.interior_occupied_cells == frozenset()


def test_layer05_routing_skeleton_empty_plan() -> None:
    plan = run_layer_05_transport_routing(exterior_plan=None)
    assert plan.failures
    assert plan.routes == ()
