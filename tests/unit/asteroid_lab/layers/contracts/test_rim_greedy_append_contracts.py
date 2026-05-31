"""Layer 03 rim greedy append contracts (Task A)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_03_RIM_GREEDY_PLACEMENT,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    build_empty_integrated_rim_greedy_result,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy_append import (
    APPEND_CELL_KIND_PRIORITY,
    LAYER_03_APPEND_SOURCE,
    AppendCellKind,
    AppendedPlacementCell,
    Layer03AppendResult,
    build_empty_layer03_append_result,
)


def test_append_cell_kind_values() -> None:
    assert AppendCellKind.MINER.value == "MINER"
    assert AppendCellKind.ROUTE_RESERVED.value == "ROUTE_RESERVED"


def test_append_cell_kind_priority_order() -> None:
    assert APPEND_CELL_KIND_PRIORITY == (
        AppendCellKind.MINER,
        AppendCellKind.EXTENSION,
        AppendCellKind.OUTPUT_STUB,
        AppendCellKind.ROUTE_RESERVED,
    )


def test_appended_placement_cell_is_frozen() -> None:
    cell = AppendedPlacementCell(
        coord=(1, 2),
        kind=AppendCellKind.MINER,
        placement_id="p0",
        variant_id="CW_TL",
        source_layer=LAYER_03_APPEND_SOURCE,
    )
    assert cell.coord == (1, 2)
    assert cell.kind is AppendCellKind.MINER


def test_empty_append_result() -> None:
    result = build_empty_layer03_append_result()
    assert result.cells == ()
    assert result.placement_count == 0
    assert result.route_reserved_cell_count == 0
    assert result.source_layer == LAYER_03_APPEND_SOURCE


def test_layer03_append_result_source_layer_matches_greedy_slug() -> None:
    result = Layer03AppendResult(
        cells=(),
        placement_count=0,
        route_reserved_cell_count=0,
        source_layer=LAYER_03_RIM_GREEDY_PLACEMENT,
    )
    assert result.source_layer == LAYER_03_RIM_GREEDY_PLACEMENT


def test_integrated_result_requires_append_result() -> None:
    empty = build_empty_integrated_rim_greedy_result(
        layer_skip_reason="missing_exterior_connection_plan",
    )
    assert isinstance(empty.append_result, Layer03AppendResult)
    assert empty.append_result.placement_count == 0
