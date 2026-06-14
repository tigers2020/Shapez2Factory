"""Simplified reconstruction fixture contracts (miner/extension → field)."""

from __future__ import annotations

from django_apps.asteroid_lab.adapters.reconstruction_blueprint_export import (
    build_reconstructed_normalized_dto,
    encode_reconstructed_copy_string,
)
from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.confidence import (
    QUALITY_TIER_CONFIDENT,
    reconstruction_acceptance_ok,
)
from django_apps.asteroid_lab.reconstruction.display_map import (
    merged_display_cells_from_reconstruction,
)
from django_apps.asteroid_lab.reconstruction.evidence import MINER_EXTENSION_CELL_KINDS
from django_apps.asteroid_lab.reconstruction.evidence import MINER_EXTENSION_CELL_KINDS
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string,
    load_reconstruction_fixture_line_pairs,
)
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame


def _run_line(line_index: int):
    required_copy, _solved_copy = load_reconstruction_fixture_line_pairs()[line_index]
    snap_req = decode_shapez_copy_string(required_copy)
    cleanup = deconstruct_snapshot(snap_req)
    recon = run_topology_reconstruction(cleanup)
    merged = merged_display_cells_from_reconstruction(cleanup, recon)
    return snap_req, cleanup, recon, merged


def test_reconstruction_fixture_line_miners_become_fields(
    reconstruction_fixture_line_index: int,
) -> None:
    snap_req, _cleanup, recon, merged = _run_line(reconstruction_fixture_line_index)
    removed_xy = {
        (c.x, c.y)
        for c in snap_req.cells
        if c.cell_kind in MINER_EXTENSION_CELL_KINDS
    }
    merged_field_xy = {
        (c.x, c.y)
        for c in merged
        if c.cell_kind in ("asteroid_shape_field", "asteroid_fluid_field")
    }
    assert removed_xy <= merged_field_xy
    assert int(recon.summary_json["synthetic_field_count"]) == len(removed_xy)


def test_reconstruction_fixture_line_export_roundtrip(
    reconstruction_fixture_line_index: int,
) -> None:
    snap_req, cleanup, recon, merged = _run_line(reconstruction_fixture_line_index)
    norm = build_reconstructed_normalized_dto(merged, map_input_id=0, run_key="fixture")
    copy = encode_reconstructed_copy_string(norm.decoded_json)
    roundtrip = decode_shapez_copy_string(copy)
    assert len(roundtrip.cells) == len(merged)


def test_reconstruction_fixture_line_coord_contract(
    reconstruction_fixture_line_index: int,
) -> None:
    _snap_req, _cleanup, recon, _merged = _run_line(reconstruction_fixture_line_index)
    for cell in recon.cells:
        assert isinstance(cell.x, int) and isinstance(cell.y, int)
    assert recon.coord_frame == CoordFrame.ISLAND_RAW


def test_reconstruction_canon_line_confident() -> None:
    _snap_req, _cleanup, recon, _merged = _run_line(1)
    assert recon.quality_tier == QUALITY_TIER_CONFIDENT
    assert reconstruction_acceptance_ok(recon)


def test_reconstruction_canon_line_synthetic_count_matches_removed() -> None:
    snap_req, cleanup, recon, _merged = _run_line(1)
    removed_miner_ext = sum(
        1
        for c in cleanup.removed_building_cells
        if c.cell_kind in MINER_EXTENSION_CELL_KINDS
    )
    assert int(recon.summary_json["synthetic_field_count"]) == removed_miner_ext
    assert len(recon.cells) == removed_miner_ext
