"""Persisted copy/json must match replay reconstruction_complete full_map bbox."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string, encode_copy_string
from django_apps.asteroid_lab.adapters.normalization import normalize_decoded_blueprint
from django_apps.asteroid_lab.adapters.reconstruction_blueprint_export import (
    load_reconstruction_cells_from_decoded_json,
)
from django_apps.asteroid_lab.reconstruction.display_map import (
    full_map_island_bbox_from_decoded_json,
    merged_display_cells_from_reconstruction,
)
from django_apps.asteroid_lab.snapshots.island_bbox import (
    island_bbox_from_cells,
    island_bbox_from_xy_dicts,
)
from django_apps.asteroid_lab.reconstruction.trace import ReconstructionTraceCollector
from django_apps.asteroid_lab.replay.reconstruction_frames import build_reconstruction_replay_events
from django_apps.asteroid_lab.replay.snapshot_map_replay import (
    build_cleanup_and_reconstruction_rows,
    snapshot_summary_from_rows,
)
from django_apps.asteroid_lab.services.cell_snapshot_service import (
    build_decoded_blueprint_snapshot_from_input,
)
from django_apps.asteroid_lab.services.input_service import persist_decoded_snapshot_for_map_input
from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
    persist_reconstructed_asteroid_map,
    run_reconstruction_for_map_input,
)


def _extent_from_island_bbox(bb: dict[str, int]) -> dict[str, int]:
    return {"width": bb["width"], "height": bb["height"]}


def _bbox_from_full_map_rows(rows: list[dict]) -> dict[str, int]:
    bb = island_bbox_from_xy_dicts(rows)
    if bb is None:
        return {"width": 0, "height": 0}
    return _extent_from_island_bbox(bb)


@pytest.fixture
def hole_island_copy() -> str:
    decoded = {
        "V": 21,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_FluidMiner"},
                {"X": 2, "Y": 0, "T": "SpacePipe_Forward"},
                {"X": 3, "Y": 0, "T": "Layout_FluidMinerExtension"},
                {"X": 1, "Y": 1, "T": "UnknownTile_A"},
                {"X": 2, "Y": 1, "T": "UnknownTile_B"},
                {"X": 3, "Y": 1, "T": "UnknownTile_C"},
                {"X": 1, "Y": 2, "T": "UnknownTile_D"},
                {"X": 3, "Y": 2, "T": "UnknownTile_E"},
                {"X": 1, "Y": 3, "T": "UnknownTile_F"},
                {"X": 2, "Y": 3, "T": "UnknownTile_G"},
                {"X": 3, "Y": 3, "T": "UnknownTile_H"},
            ],
        },
    }
    return encode_copy_string(decoded)


@pytest.mark.django_db
def test_persist_full_map_matches_replay_complete_bbox(hole_island_copy: str) -> None:
    """Regression: recon.cells-only subset shrinks server bbox vs merged full_map."""

    proj = m.AsteroidProject.objects.create(name="BBox", slug="persist-full-map-bbox")
    inp = m.AsteroidMapInput.objects.create(project=proj, copy_code=hole_island_copy)
    norm = normalize_decoded_blueprint(decode_copy_string(hole_island_copy.removesuffix("$")))
    persist_decoded_snapshot_for_map_input(inp.id, norm)

    snap = build_decoded_blueprint_snapshot_from_input(inp.id)
    _, _, _, row_extension, _, _ = build_cleanup_and_reconstruction_rows(snap)
    cleanup, recon = run_reconstruction_for_map_input(inp.id)
    merged = merged_display_cells_from_reconstruction(cleanup, recon)
    replay_bbox = island_bbox_from_cells(merged)
    assert replay_bbox is not None
    recon_only_bbox = island_bbox_from_cells(tuple(recon.cells))
    assert recon_only_bbox is not None
    assert replay_bbox["width"] >= recon_only_bbox["width"]
    assert replay_bbox["height"] >= recon_only_bbox["height"]

    collector = ReconstructionTraceCollector()
    cleanup2, recon2 = run_reconstruction_for_map_input(inp.id, trace_collector=collector)
    recon_summary = snapshot_summary_from_rows(row_extension)
    recon_summary.update({**dict(cleanup2.summary_json), **dict(recon2.summary_json)})
    events = build_reconstruction_replay_events(
        structural_rows=list(row_extension),
        cleanup=cleanup2,
        recon=recon2,
        trace_events=collector.events,
        recon_summary=dict(recon_summary),
        hints={},
    )
    complete = next(e for e in events if e.event_key == "step4_10_asteroid_map_complete")
    fm_bbox = _bbox_from_full_map_rows(list(complete.full_map))

    pk = persist_reconstructed_asteroid_map(
        map_input_id=inp.id,
        run_key="bbox",
        recon=recon,
        cleanup=cleanup,
    )
    row = m.ReconstructedAsteroidMap.objects.get(pk=pk)
    meta_bbox = full_map_island_bbox_from_decoded_json(dict(row.decoded_json))
    assert meta_bbox is not None
    assert meta_bbox["width"] == replay_bbox["width"]
    assert meta_bbox["height"] == replay_bbox["height"]
    assert fm_bbox == {
        "width": replay_bbox["width"],
        "height": replay_bbox["height"],
    }

    entries = row.decoded_json.get("BP", {}).get("Entries") or []
    assert len(entries) == len(merged)

    persist_cells = load_reconstruction_cells_from_decoded_json(dict(row.decoded_json))
    by_xy = {(c.x, c.y): c for c in persist_cells}
    assert by_xy[(2, 2)].cell_kind in ("asteroid_shape_field", "asteroid_fluid_field")
    for xy in ((1, 1), (2, 1), (3, 1), (1, 2), (3, 2), (1, 3), (2, 3), (3, 3)):
        assert by_xy[xy].cell_kind == "unknown"

    assert row.copy_code.startswith("SHAPEZ2-4-")
    assert row.original_copy_code == hole_island_copy.strip()
    assert row.original_decoded_json.get("BP")
    decoded = decode_copy_string(row.copy_code.removesuffix("$"))
    assert len(decoded.root.get("BP", {}).get("Entries", [])) == len(merged)
