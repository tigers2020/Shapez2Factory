"""RTTP reconstruction -> OptimizationInput adapter."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.adapters.catalog_transport_policy import (
    CatalogTransportUnresolvedError,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    SLICE_VERSION,
    BuildingCatalogSlice,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import TransportRegistryEntry
from django_apps.asteroid_lab.optimization.input_contracts import (
    ExistingTransportCell,
    RouteGoal,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_reconstruction,
)
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedCellDTO


def _field_cell(x: int, y: int) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type="AsteroidShapeField",
        cell_kind="asteroid_shape_field",
        transport_kind="none",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={"X": x, "Y": y, "T": "AsteroidShapeField"},
    )


def _belt_cell(x: int, y: int) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type="SpaceBelt_Forward",
        cell_kind="space_belt",
        transport_kind="shape_belt",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={"X": x, "Y": y, "T": "SpaceBelt_Forward"},
    )


def _pipe_cell(x: int, y: int) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type="SpacePipe_Forward",
        cell_kind="space_pipe",
        transport_kind="fluid_pipe",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={"X": x, "Y": y, "T": "SpacePipe_Forward"},
    )


def _pipe_cell_registry_key(x: int, y: int) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type="SpacePipe_Forward",
        cell_kind="space_pipe",
        transport_kind="space_pipe",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={"X": x, "Y": y, "T": "SpacePipe_Forward"},
    )


def _assert_coord_pair(value: object, path: str) -> None:
    assert isinstance(value, tuple), f"{path}: expected tuple coord, got {type(value)!r}"
    assert len(value) == 2, f"{path}: expected 2-tuple, got {value!r}"
    assert isinstance(value[0], int) and isinstance(value[1], int)


def _assert_optimization_input_raw_coords(inp) -> None:
    for coord in inp.mineable_cells:
        _assert_coord_pair(coord, "mineable_cells")
    for coord in inp.rim_cells:
        _assert_coord_pair(coord, "rim_cells")
    for coord in inp.inner_cells:
        _assert_coord_pair(coord, "inner_cells")
    for coord in inp.external_void_cells:
        _assert_coord_pair(coord, "external_void_cells")
    for cell in inp.existing_transport_cells:
        assert isinstance(cell, ExistingTransportCell)
        _assert_coord_pair(cell.coord, "existing_transport_cells.coord")
    for goal in inp.route_goals:
        assert isinstance(goal, RouteGoal)
        _assert_coord_pair(goal.coord, "route_goals.coord")


def test_mixed_existing_transport_partitions_for_shape_run() -> None:
    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    cells = cells + (_belt_cell(4, 5), _pipe_cell(4, 6))
    inp = optimization_input_from_reconstruction(ReconstructionResult(cells=cells))

    assert inp.transport_kind is TransportKind.SHAPE_BELT
    assert len(inp.existing_transport_cells) == 2
    assert inp.existing_trunk_cells == frozenset({(4, 5)})
    assert inp.blocked_incompatible_transport_cells == frozenset({(4, 6)})


def test_optimization_input_adapter_existing_trunk_uses_raw_coords() -> None:
    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    cells = cells + (_belt_cell(4, 5),)
    inp = optimization_input_from_reconstruction(ReconstructionResult(cells=cells))

    _assert_optimization_input_raw_coords(inp)
    assert inp.mineable_cells
    assert inp.route_goals
    assert any(goal.coord not in inp.mineable_cells for goal in inp.route_goals)
    assert inp.existing_transport_cells
    assert inp.existing_trunk_cells == frozenset({(4, 5)})


def test_optimization_input_adapter_greenfield_has_external_margin_goal() -> None:
    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    inp = optimization_input_from_reconstruction(ReconstructionResult(cells=cells))
    assert inp.existing_transport_cells == frozenset()
    assert inp.existing_trunk_cells == frozenset()
    assert len(inp.route_goals) >= 1
    void_neighbors = inp.external_void_cells & frozenset(goal.coord for goal in inp.route_goals)
    assert void_neighbors


def test_greenfield_default_transport_uses_catalog_slice_t1() -> None:
    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    catalog_slice = BuildingCatalogSlice(
        SLICE_VERSION,
        (TransportRegistryEntry("space_belt", "belt", "bv:1"),),
        (),
    )
    inp = optimization_input_from_reconstruction(
        ReconstructionResult(cells=cells),
        catalog_slice=catalog_slice,
    )
    assert inp.transport_kind is TransportKind.SHAPE_BELT


def test_greenfield_without_catalog_slice_uses_legacy_heuristic() -> None:
    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    inp = optimization_input_from_reconstruction(ReconstructionResult(cells=cells))
    assert inp.transport_kind is TransportKind.SHAPE_BELT


def test_existing_transport_resolves_registry_key_via_catalog_slice() -> None:
    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    cells = cells + (_pipe_cell_registry_key(4, 5),)
    catalog_slice = BuildingCatalogSlice(
        SLICE_VERSION,
        (TransportRegistryEntry("space_pipe", "pipe", "bv:1"),),
        (),
    )
    inp = optimization_input_from_reconstruction(
        ReconstructionResult(cells=cells),
        catalog_slice=catalog_slice,
    )
    assert inp.existing_transport_cells == frozenset(
        {ExistingTransportCell(coord=(4, 5), transport_kind=TransportKind.FLUID_PIPE)}
    )


def test_unresolved_transport_cell_fails_when_catalog_slice_present() -> None:
    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    cells = cells + (_pipe_cell_registry_key(4, 5),)
    catalog_slice = BuildingCatalogSlice(SLICE_VERSION, (), ())
    with pytest.raises(CatalogTransportUnresolvedError) as exc_info:
        optimization_input_from_reconstruction(
            ReconstructionResult(cells=cells),
            catalog_slice=catalog_slice,
        )
    message = str(exc_info.value)
    assert "(4, 5)" in message
    assert "space_pipe" in message
