"""Replay reconstruction_final must overlay recon onto structural full_map (no key shrink)."""

from __future__ import annotations

import json

import pytest

from django_apps.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from django_apps.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from django_apps.asteroid_lab.reconstruction.trace import ReconstructionTraceCollector
from django_apps.asteroid_lab.replay.reconstruction_frames import build_reconstruction_replay_events
from django_apps.asteroid_lab.replay.snapshot_map_replay import (
    build_cleanup_and_reconstruction_rows,
    cell_key_xy_layer,
    snapshot_summary_from_rows,
)
from django_apps.asteroid_lab.services.dto import DecodedBlueprintSnapshotDTO, DecodedCellDTO


def _cell(
    x: int,
    y: int,
    *,
    tile_type: str = "",
    cell_kind: str = "unknown",
    transport_kind: str = "none",
    raw: dict | None = None,
) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type=tile_type,
        cell_kind=cell_kind,
        transport_kind=transport_kind,
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json=dict(raw or {}),
    )


def _snapshot(cells: tuple[DecodedCellDTO, ...]) -> DecodedBlueprintSnapshotDTO:
    xs = [c.x for c in cells]
    ys = [c.y for c in cells]
    mn_x, mx_x = min(xs), max(xs)
    mn_y, mx_y = min(ys), max(ys)
    ck: dict[str, int] = {}
    for c in cells:
        ck[c.cell_kind] = ck.get(c.cell_kind, 0) + 1
    return DecodedBlueprintSnapshotDTO(
        project_id=None,
        map_input_id=None,
        binary_version=3,
        blueprint_type="Island",
        entry_count=len(cells),
        bbox_json={
            "min_x": mn_x,
            "max_x": mx_x,
            "min_y": mn_y,
            "max_y": mx_y,
            "width": mx_x - mn_x + 1,
            "height": mx_y - mn_y + 1,
        },
        cell_kind_counts_json=ck,
        transport_kind_counts_json={},
        cells=cells,
        summary_json={},
    )


def test_reconstruction_final_full_map_merges_overlay_not_replace() -> None:
    """``recon.cells`` can omit structural-only keys; final replay frame must keep them."""

    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(2, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
        _cell(1, 1, tile_type="UnknownTile_A"),
        _cell(2, 1, tile_type="UnknownTile_B"),
        _cell(3, 1, tile_type="UnknownTile_C"),
        _cell(1, 2, tile_type="UnknownTile_D"),
        _cell(3, 2, tile_type="UnknownTile_E"),
        _cell(1, 3, tile_type="UnknownTile_F"),
        _cell(2, 3, tile_type="UnknownTile_G"),
        _cell(3, 3, tile_type="UnknownTile_H"),
    )
    snap = _snapshot(cells)
    _, _, _, row_extension, _, _ = build_cleanup_and_reconstruction_rows(snap)
    structural_keys = {cell_key_xy_layer(r) for r in row_extension}
    cleanup = deconstruct_snapshot(snap)
    collector = ReconstructionTraceCollector()
    recon = run_topology_reconstruction(cleanup, trace_collector=collector)
    recon_keys = {(c.x, c.y, c.layer) for c in recon.cells}
    assert (2, 2, None) in recon_keys
    assert (2, 2, None) not in structural_keys

    row_recon = [r for r in row_extension if cell_key_xy_layer(r) in recon_keys]
    recon_summary = snapshot_summary_from_rows(row_recon)
    recon_summary.update({**dict(cleanup.summary_json), **dict(recon.summary_json)})

    events = build_reconstruction_replay_events(
        structural_rows=list(row_extension),
        cleanup=cleanup,
        recon=recon,
        trace_events=collector.events,
        recon_summary=dict(recon_summary),
        hints={},
    )
    final_ev = next(e for e in events if e.event_key == "step4_09_reconstruction_final")
    fm = final_ev.full_map
    final_keys = {cell_key_xy_layer(r) for r in fm}
    assert structural_keys <= final_keys
    assert recon_keys <= final_keys
    assert len(fm) == len(final_keys) == len(structural_keys | recon_keys)
    hole = next(r for r in fm if int(r["x"]) == 2 and int(r["y"]) == 2)
    assert hole.get("cell_kind") == "asteroid_shape_field"


def test_reconstruction_complete_boundary_jsonl_full_map(
    monkeypatch: pytest.MonkeyPatch, tmp_path,
) -> None:
    monkeypatch.setenv("ASTEROID_LAB_BOUNDARY_JSONL", "1")
    monkeypatch.setenv("ASTEROID_LAB_BOUNDARY_JSONL_DIR", str(tmp_path))

    cells = (
        _cell(1, 0, cell_kind="fluid_miner"),
        _cell(2, 0, cell_kind="space_pipe", transport_kind="fluid_pipe"),
        _cell(3, 0, cell_kind="fluid_miner_extension", transport_kind="fluid_pipe"),
        _cell(1, 1, tile_type="UnknownTile_A"),
        _cell(2, 1, tile_type="UnknownTile_B"),
        _cell(3, 1, tile_type="UnknownTile_C"),
        _cell(1, 2, tile_type="UnknownTile_D"),
        _cell(3, 2, tile_type="UnknownTile_E"),
        _cell(1, 3, tile_type="UnknownTile_F"),
        _cell(2, 3, tile_type="UnknownTile_G"),
        _cell(3, 3, tile_type="UnknownTile_H"),
    )
    snap = _snapshot(cells)
    _, _, _, row_extension, _, _ = build_cleanup_and_reconstruction_rows(snap)
    cleanup = deconstruct_snapshot(snap)
    collector = ReconstructionTraceCollector()
    recon = run_topology_reconstruction(cleanup, trace_collector=collector)
    recon_keys = {(c.x, c.y, c.layer) for c in recon.cells}
    row_recon = [r for r in row_extension if cell_key_xy_layer(r) in recon_keys]
    recon_summary = snapshot_summary_from_rows(row_recon)
    recon_summary.update({**dict(cleanup.summary_json), **dict(recon.summary_json)})

    build_reconstruction_replay_events(
        structural_rows=list(row_extension),
        cleanup=cleanup,
        recon=recon,
        trace_events=collector.events,
        recon_summary=dict(recon_summary),
        hints={},
        boundary_run_id="rid_jsonl_full_map",
        map_input_id=99,
        project_id=88,
    )

    log_path = tmp_path / "rid_jsonl_full_map.jsonl"
    raw_lines = log_path.read_text(encoding="utf-8").strip().splitlines()
    lines = [json.loads(line) for line in raw_lines]
    b_complete = "reconstruction.reconstruction_complete"
    complete_lines = [x for x in lines if x.get("boundary") == b_complete]
    assert len(complete_lines) == 1
    payload = complete_lines[0]
    assert payload["stage"] == "reconstruction"
    assert payload["event_key"] == "step4_10_asteroid_map_complete"
    snap_rows = payload["full_map_snapshot"]
    assert payload["full_map_cell_count"] == len(snap_rows)
    assert all("raw_x" in r and "server_x" in r for r in snap_rows)
