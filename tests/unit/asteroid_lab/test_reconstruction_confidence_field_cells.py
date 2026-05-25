"""Confidence result coords align with complete-map field cells when cleanup provided."""

from __future__ import annotations

from django_apps.asteroid_lab.reconstruction.complete_map import (
    build_reconstruction_complete_map,
)
from django_apps.asteroid_lab.reconstruction.confidence import apply_confidence_to_result
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from tests.support.reconstruction_complete_map_fixtures import (
    minimal_cleanup_and_recon_from_cells,
)


def _cell(x: int, y: int) -> DecodedCellDTO:
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
        raw_entry_json={},
    )


def test_apply_confidence_confirmed_equals_complete_field_cells() -> None:
    cleanup, base = minimal_cleanup_and_recon_from_cells(
        _cell(0, 0),
        _cell(1, 0),
        _cell(2, 0),
    )
    out = apply_confidence_to_result(
        base,
        wall_coords=set(),
        interior_patch_coords=frozenset(),
        cleanup=cleanup,
    )
    complete = build_reconstruction_complete_map(cleanup=cleanup, recon=out)
    assert out.confirmed_cells == complete.field_cells
    assert out.ambiguous_cells == frozenset()
