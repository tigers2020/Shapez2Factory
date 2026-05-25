"""Reconstruction-complete map factory — merged display SoT."""

from __future__ import annotations

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
    build_reconstruction_complete_map,
    overlay_field_cell_count,
)
from django_apps.asteroid_lab.reconstruction.display_map import (
    full_map_rows_from_reconstruction,
    merged_display_cells_from_reconstruction,
)
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string,
    load_reconstruction_fixture_line_pairs,
)
from django_apps.asteroid_lab.replay.snapshot_map_replay import snapshot_summary_from_rows


def _canon_cleanup_recon():
    required_copy, _solved = load_reconstruction_fixture_line_pairs()[1]
    snap = decode_shapez_copy_string(required_copy)
    cleanup = deconstruct_snapshot(snap)
    recon = run_topology_reconstruction(cleanup)
    return cleanup, recon


def test_build_complete_map_cells_equal_merged_display() -> None:
    cleanup, recon = _canon_cleanup_recon()
    complete = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    expected = merged_display_cells_from_reconstruction(cleanup, recon)
    assert complete.cells == expected


def test_overlay_field_count_less_than_complete_on_canon_fixture() -> None:
    cleanup, recon = _canon_cleanup_recon()
    complete = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    overlay_n = overlay_field_cell_count(recon)
    complete_n = len(complete.field_cells)
    assert overlay_n < complete_n
    assert complete_n >= 50


def test_complete_field_count_matches_full_map_row_summary() -> None:
    cleanup, recon = _canon_cleanup_recon()
    complete = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    rows = full_map_rows_from_reconstruction(cleanup, recon)
    summary = snapshot_summary_from_rows(rows)
    assert len(complete.field_cells) == int(summary["field_count"])
    assert complete.shape_field_cell_count + complete.fluid_field_cell_count == int(
        summary["field_count"]
    )


def test_complete_map_is_frozen_dto() -> None:
    cleanup, recon = _canon_cleanup_recon()
    complete = build_reconstruction_complete_map(cleanup=cleanup, recon=recon)
    assert isinstance(complete, ReconstructionCompleteMap)
    assert complete.coord_frame == recon.coord_frame
