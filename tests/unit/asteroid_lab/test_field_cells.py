"""Asteroid field cell accessors ??complete map SoT only."""

from __future__ import annotations

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.acceptance_topology import (
    acceptance_topology_from_complete_map,
)
from django_apps.asteroid_lab.reconstruction.complete_map import (
    build_reconstruction_complete_map,
    overlay_field_cell_count,
)
from django_apps.asteroid_lab.reconstruction.field_cells import (
    asteroid_field_cells_from_complete_map,
    count_asteroid_field_cells_by_resource,
)
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string,
    load_reconstruction_fixture_line_pairs,
)
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from tests.support.reconstruction_complete_map_fixtures import (
    minimal_complete_map_from_cells,
)


def _cell(x: int, y: int, *, cell_kind: str, transport_kind: str = "none") -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type="",
        cell_kind=cell_kind,
        transport_kind=transport_kind,
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
    )


def _recon(*cells: DecodedCellDTO) -> ReconstructionResult:
    return ReconstructionResult(
        cells=cells,
        confirmed_cells=frozenset(),
        ambiguous_cells=frozenset(),
        external_void_cells=frozenset(),
        confidence_score=1.0,
        quality_tier="CONFIDENT_RECONSTRUCTION",
    )


def test_transport_cell_excluded_on_complete_map() -> None:
    complete = minimal_complete_map_from_cells(
        _cell(0, 0, cell_kind="asteroid_shape_field"),
        _cell(1, 0, cell_kind="shape_belt", transport_kind="shape_belt"),
    )
    fields = asteroid_field_cells_from_complete_map(complete)
    assert fields == frozenset({(0, 0)})
    assert count_asteroid_field_cells_by_resource(complete) == {"shape": 1, "fluid": 0}


def test_miner_extension_excluded_unless_field_kind_on_complete_map() -> None:
    complete = minimal_complete_map_from_cells(
        _cell(0, 0, cell_kind="shape_miner"),
        _cell(1, 0, cell_kind="shape_miner_extension"),
        _cell(2, 0, cell_kind="asteroid_shape_field"),
    )
    fields = asteroid_field_cells_from_complete_map(complete)
    assert fields == frozenset({(2, 0)})


def test_inferred_fill_synthetic_asteroid_field_included() -> None:
    complete = minimal_complete_map_from_cells(
        DecodedCellDTO(
            x=3,
            y=3,
            layer=None,
            rotation=0,
            tile_type="",
            cell_kind="asteroid_shape_field",
            transport_kind="none",
            has_nested_blueprint=False,
            nested_entry_count=0,
            nested_type_counts_json={},
            raw_entry_json={"_replay_synthetic": True},
        ),
    )
    assert asteroid_field_cells_from_complete_map(complete) == frozenset({(3, 3)})


def test_fluid_field_counted_separately() -> None:
    complete = minimal_complete_map_from_cells(
        _cell(0, 0, cell_kind="asteroid_shape_field"),
        _cell(1, 0, cell_kind="asteroid_fluid_field"),
    )
    assert count_asteroid_field_cells_by_resource(complete) == {"shape": 1, "fluid": 1}


def test_acceptance_topology_from_complete_map_matches_field_cells() -> None:
    complete = minimal_complete_map_from_cells(
        _cell(0, 0, cell_kind="asteroid_shape_field"),
        _cell(1, 0, cell_kind="shape_miner"),
    )
    topo = acceptance_topology_from_complete_map(complete)
    assert topo.mineable_cells == complete.field_cells


def test_overlay_count_less_than_complete_on_canon_fixture() -> None:
    required_copy, _solved = load_reconstruction_fixture_line_pairs()[1]
    snap = decode_shapez_copy_string(required_copy)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    complete = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    assert overlay_field_cell_count(recon) < len(complete.field_cells)
