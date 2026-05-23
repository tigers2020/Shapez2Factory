"""Per-line reconstruction fixture topology + confidence contracts."""

from __future__ import annotations

import json

from django_apps.asteroid_lab.adapters.reconstruction_blueprint_export import (
    build_reconstructed_normalized_dto,
    encode_reconstructed_copy_string,
)
from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.acceptance_topology import (
    acceptance_topology_from_reconstruction,
)
from django_apps.asteroid_lab.reconstruction.confidence import (
    QUALITY_TIER_CONFIDENT,
    reconstruction_acceptance_ok,
)
from django_apps.asteroid_lab.reconstruction.display_map import (
    merged_display_cells_from_reconstruction,
)
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.topology_contract import (
    build_normalized_reconstruction_topology,
    decode_shapez_copy_string,
    diff_topology,
    load_reconstruction_fixture_line_pairs,
    raw_coords_from_snapshot,
    topology_diff_is_empty,
)
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.copy_json_coords import (
    entries_have_explicit_raw_x_zero,
)


def _run_line(line_index: int):
    required_copy, solved_copy = load_reconstruction_fixture_line_pairs()[line_index]
    snap_req = decode_shapez_copy_string(required_copy)
    snap_sol = decode_shapez_copy_string(solved_copy)
    cleanup = deconstruct_snapshot(snap_req)
    recon = run_topology_reconstruction(cleanup)
    merged = merged_display_cells_from_reconstruction(cleanup, recon)
    shell = raw_coords_from_snapshot(snap_req)
    actual = build_normalized_reconstruction_topology(
        merged,
        shell_raw_coords=shell,
        coord_frame=CoordFrame.ISLAND_RAW,
    )
    expected = build_normalized_reconstruction_topology(
        snap_sol.cells,
        shell_raw_coords=shell,
        coord_frame=CoordFrame.ISLAND_RAW,
    )
    return snap_req, snap_sol, cleanup, recon, merged, actual, expected


def test_reconstruction_fixture_line_topology_matches_solved(
    reconstruction_fixture_line_index: int,
) -> None:
    _snap_req, _snap_sol, _cleanup, _recon, _merged, actual, expected = _run_line(
        reconstruction_fixture_line_index
    )
    diff = diff_topology(actual, expected)
    assert topology_diff_is_empty(diff), (
        f"line {reconstruction_fixture_line_index}: "
        f"extra={len(actual.mineable_cells - expected.mineable_cells)} "
        f"missing={len(expected.mineable_cells - actual.mineable_cells)} "
        f"diff={json.dumps(diff, ensure_ascii=False)}"
    )


def test_reconstruction_fixture_line_export_topology_equivalent(
    reconstruction_fixture_line_index: int,
) -> None:
    snap_req, _snap_sol, cleanup, recon, merged, _actual, expected = _run_line(
        reconstruction_fixture_line_index
    )
    norm = build_reconstructed_normalized_dto(merged, map_input_id=0, run_key="fixture")
    copy = encode_reconstructed_copy_string(norm.decoded_json)
    roundtrip = decode_shapez_copy_string(copy)
    export_topo = build_normalized_reconstruction_topology(
        roundtrip.cells,
        shell_raw_coords=raw_coords_from_snapshot(snap_req),
        coord_frame=CoordFrame.ISLAND_RAW,
    )
    diff = diff_topology(export_topo, expected)
    assert topology_diff_is_empty(diff), json.dumps(diff, ensure_ascii=False)


def test_reconstruction_fixture_line_coord_and_optimization_contract(
    reconstruction_fixture_line_index: int,
) -> None:
    _snap_req, snap_sol, cleanup, recon, _merged, actual, expected = _run_line(
        reconstruction_fixture_line_index
    )
    topo = acceptance_topology_from_reconstruction(
        recon, coord_frame=CoordFrame.ISLAND_RAW
    )
    for cell in recon.cells:
        assert isinstance(cell.x, int) and isinstance(cell.y, int)
        if cell.raw_entry_json.get("_replay_synthetic"):
            continue
    req_entries = [c.raw_entry_json for c in _snap_req.cells if c.raw_entry_json]
    has_explicit_x0 = entries_have_explicit_raw_x_zero(req_entries)
    if reconstruction_fixture_line_index != 1 and not has_explicit_x0:
        assert not any(c.x == 0 and c.raw_entry_json.get("_replay_synthetic") for c in recon.cells)
    assert topo.mineable_cells <= actual.mineable_cells
    if reconstruction_fixture_line_index == 1:
        assert actual.mineable_cells == expected.mineable_cells


def test_reconstruction_canon_line_confident_and_topology_match() -> None:
    _snap_req, _snap_sol, _cleanup, recon, _merged, actual, expected = _run_line(1)
    diff = diff_topology(actual, expected)
    assert topology_diff_is_empty(diff)
    assert recon.quality_tier == QUALITY_TIER_CONFIDENT
    assert reconstruction_acceptance_ok(recon)


def test_reconstruction_canon_line_confidence_calibration() -> None:
    _snap_req, snap_sol, _cleanup, recon, _merged, _actual, expected = _run_line(1)
    solved_mineable = expected.mineable_cells
    _snap_req, _snap_sol, _cleanup, _recon, _merged, actual, _expected = _run_line(1)
    overlap = len(actual.mineable_cells & solved_mineable)
    assert overlap >= int(len(solved_mineable) * 0.95)
    field_overlap = len(recon.confirmed_cells & solved_mineable)
    assert (
        field_overlap >= int(len(recon.confirmed_cells) * 0.95) if recon.confirmed_cells else True
    )
    assert len(recon.ambiguous_cells & solved_mineable) <= int(len(solved_mineable) * 0.05)
