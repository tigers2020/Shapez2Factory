"""Timeline enrichment for pattern_bundle_highlights from equipment_bundles."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.pattern_bundle_highlight import METRICS_KEY
from django_apps.asteroid_lab.services.lab_timeline_pattern_bundle_enrichment import (
    enrich_lab_timeline_frames_with_pattern_bundle_highlights,
)
from django_apps.asteroid_lab.snapshots.equipment_bundles import build_equipment_bundles


def _row(x: int, y: int, cell_kind: str, *, rotation: int = 0) -> dict:
    transport = "fluid_pipe" if cell_kind.startswith("fluid") else "shape_belt"
    return {
        "x": x,
        "y": y,
        "rotation": rotation,
        "cell_kind": cell_kind,
        "transport_kind": transport,
    }


def test_enrichment_adds_highlights_from_equipment_bundles() -> None:
    rows = [
        _row(-1, 0, "fluid_miner", rotation=0),
        _row(-1, 1, "fluid_miner_extension", rotation=3),
        _row(5, 0, "fluid_miner", rotation=0),
    ]
    bundles = build_equipment_bundles(rows)
    frame = {
        "event_type": "replay.snapshot.cleanup_transport",
        "map_view": {"full_cells": rows},
        "cell_overlay_json": {"equipment_bundles": bundles},
        "metrics": {},
    }
    out = enrich_lab_timeline_frames_with_pattern_bundle_highlights([frame])
    highlights = out[0]["metrics"].get(METRICS_KEY)
    assert highlights is not None
    assert len(highlights["bundles"]) == 2


def test_enrichment_does_not_overwrite_existing_highlights() -> None:
    existing = {
        "version": 1,
        "bundles": [{"bundle_key": "keep", "color_index": 0, "outline_loops": []}],
    }
    frame = {
        "map_view": {"full_cells": [{"x": 1, "y": 0, "cell_kind": "shape_miner"}]},
        "metrics": {METRICS_KEY: existing},
    }
    out = enrich_lab_timeline_frames_with_pattern_bundle_highlights([frame])
    assert out[0]["metrics"][METRICS_KEY] == existing


def test_enrichment_replaces_empty_pattern_bundle_placeholder() -> None:
    rows = [
        _row(-1, 0, "fluid_miner", rotation=0),
        _row(-1, 1, "fluid_miner_extension", rotation=3),
    ]
    bundles = build_equipment_bundles(rows)
    frame = {
        "map_view": {"full_cells": rows},
        "cell_overlay_json": {"equipment_bundles": bundles},
        "metrics": {METRICS_KEY: {"version": 1, "bundles": []}},
    }
    out = enrich_lab_timeline_frames_with_pattern_bundle_highlights([frame])
    highlights = out[0]["metrics"].get(METRICS_KEY)
    assert highlights is not None
    assert len(highlights["bundles"]) >= 1
