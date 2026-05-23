"""RTTP reconstruction → OptimizationInput adapter (PR-2)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.input_contracts import (
    ExistingTransportCell,
    OptimizationInput,
    RouteGoal,
)
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_reconstruction,
)
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedCellDTO


def _field_cell(sx: int, sy: int) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=sx,
        y=sy,
        layer=None,
        rotation=0,
        tile_type="AsteroidShapeField",
        cell_kind="asteroid_shape_field",
        transport_kind="none",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={"X": sx, "Y": sy, "T": "AsteroidShapeField"},
        server_x=sx,
        server_y=sy,
    )


def _belt_cell(sx: int, sy: int) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=sx,
        y=sy,
        layer=None,
        rotation=0,
        tile_type="SpaceBelt_Forward",
        cell_kind="space_belt",
        transport_kind="shape_belt",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={"X": sx, "Y": sy, "T": "SpaceBelt_Forward"},
        server_x=sx,
        server_y=sy,
    )


def _assert_coord_pair(value: object, path: str) -> None:
    assert isinstance(value, tuple), f"{path}: expected tuple coord, got {type(value)!r}"
    assert len(value) == 2, f"{path}: expected 2-tuple, got {value!r}"
    assert isinstance(value[0], int) and isinstance(value[1], int), (
        f"{path}: coord components must be int, got {value!r}"
    )


def _assert_optimization_input_server_coords_only(inp: OptimizationInput) -> None:
    for coord in inp.mineable_cells:
        _assert_coord_pair(coord, "mineable_cells")
    for coord in inp.rim_cells:
        _assert_coord_pair(coord, "rim_cells")
    for coord in inp.inner_cells:
        _assert_coord_pair(coord, "inner_cells")
    for coord in inp.external_void_cells:
        _assert_coord_pair(coord, "external_void_cells")
    for coord in inp.protected_corridor_cells:
        _assert_coord_pair(coord, "protected_corridor_cells")
    for coord in inp.existing_trunk_cells:
        _assert_coord_pair(coord, "existing_trunk_cells")
    for cell in inp.existing_transport_cells:
        assert isinstance(cell, ExistingTransportCell)
        _assert_coord_pair(cell.coord, "existing_transport_cells.coord")
    for goal in inp.route_goals:
        assert isinstance(goal, RouteGoal)
        _assert_coord_pair(goal.coord, "route_goals.coord")


def test_optimization_input_adapter_server_coords_only() -> None:
    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    cells = cells + (_belt_cell(4, 5),)
    result = ReconstructionResult(
        cells=cells,
        server_xy_params=None,
    )
    inp = optimization_input_from_reconstruction(result)
    _assert_optimization_input_server_coords_only(inp)
    assert inp.mineable_cells
    assert inp.route_goals
    assert any(goal.coord not in inp.mineable_cells for goal in inp.route_goals)
    assert inp.existing_transport_cells
    assert inp.existing_trunk_cells == frozenset({(4, 5)})


def test_optimization_input_adapter_greenfield_has_external_margin_goal() -> None:
    cells = tuple(_field_cell(x, y) for x in range(5, 9) for y in range(5, 9))
    result = ReconstructionResult(cells=cells, server_xy_params=None)
    inp = optimization_input_from_reconstruction(result)
    assert inp.existing_transport_cells == frozenset()
    assert inp.existing_trunk_cells == frozenset()
    assert len(inp.route_goals) >= 1
    void_neighbors = inp.external_void_cells & frozenset(
        goal.coord for goal in inp.route_goals
    )
    assert void_neighbors
