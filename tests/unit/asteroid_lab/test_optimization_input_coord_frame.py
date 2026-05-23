"""PR-E: ``OptimizationInput.coord_frame`` and island reconstruction path."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_reconstruction,
)
from django_apps.asteroid_lab.reconstruction.acceptance_topology import (
    acceptance_topology_from_reconstruction,
)
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
def test_optimization_input_defaults_to_server_dense_frame(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    assert greenfield_optimization_input.coord_frame == CoordFrame.SERVER_DENSE


def test_acceptance_topology_island_raw_uses_cell_xy_not_server() -> None:
    cell = DecodedCellDTO(
        x=1,
        y=2,
        layer=None,
        rotation=0,
        tile_type="AsteroidShapeField",
        cell_kind="asteroid_shape_field",
        transport_kind="none",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
        server_x=99,
        server_y=88,
    )
    result = ReconstructionResult(
        cells=(cell,),
        server_xy_params=(0, 0),
    )
    topo = acceptance_topology_from_reconstruction(result, coord_frame=CoordFrame.ISLAND_RAW)
    assert (1, 2) in topo.mineable_cells
    assert (99, 88) not in topo.mineable_cells


def test_optimization_input_from_reconstruction_island_raw_frame() -> None:
    cell = DecodedCellDTO(
        x=0,
        y=1,
        layer=None,
        rotation=0,
        tile_type="AsteroidShapeField",
        cell_kind="asteroid_shape_field",
        transport_kind="none",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
        server_x=5,
        server_y=6,
    )
    result = ReconstructionResult(
        cells=(cell,),
        server_xy_params=(0, 0),
    )
    inp = optimization_input_from_reconstruction(result, coord_frame=CoordFrame.ISLAND_RAW)
    assert inp.coord_frame == CoordFrame.ISLAND_RAW
    assert (0, 1) in inp.mineable_cells
