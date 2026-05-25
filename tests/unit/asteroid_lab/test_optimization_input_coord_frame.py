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
from tests.support.reconstruction_complete_map_fixtures import (
    minimal_cleanup_and_recon_from_cells,
)


def test_optimization_input_defaults_to_island_raw_frame(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    assert greenfield_optimization_input.coord_frame == CoordFrame.ISLAND_RAW


def test_acceptance_topology_island_raw_uses_cell_xy() -> None:
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
    )
    result = ReconstructionResult(
        cells=(cell,),
    )
    topo = acceptance_topology_from_reconstruction(result, coord_frame=CoordFrame.ISLAND_RAW)
    assert (1, 2) in topo.mineable_cells


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
    )
    cleanup, result = minimal_cleanup_and_recon_from_cells(cell)
    inp = optimization_input_from_reconstruction(
        result,
        cleanup=cleanup,
        coord_frame=CoordFrame.ISLAND_RAW,
    )
    assert inp.coord_frame == CoordFrame.ISLAND_RAW
    assert (0, 1) in inp.mineable_cells
