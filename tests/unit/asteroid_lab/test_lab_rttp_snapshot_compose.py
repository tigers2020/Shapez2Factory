"""Unit tests for RTTP full-snapshot compose projection (Sequence 3B-S)."""

from __future__ import annotations

import base64
import gzip
import json

import pytest
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    RTTP_MILESTONE_EVENT_TYPES,
)
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    build_lab_replay_frames_for_project,
)
from django_apps.asteroid_lab.services.lab_rttp_snapshot_compose import (
    frame_has_renderable_map,
    interleave_rttp_snapshot_frames,
    last_renderable_frame_index,
    project_rttp_row_to_product_frame,
)
from django_apps.asteroid_lab.services.replay_pipeline_service import build_initial_replay_for_map_input
from django_apps.asteroid_lab.services.solver_runtime_entry import run_solver_runtime_for_project


def _minimal_valid_copy() -> str:
    payload = json.dumps(
        {
            "V": 1,
            "BP": {
                "$type": "Island",
                "Entries": [
                    {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                    {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
                ],
            },
        },
        separators=(",", ":"),
    ).encode("utf-8")
    b64 = base64.b64encode(gzip.compress(payload)).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


def _map_frame(idx: int, event_type: str = "reconstruction.completed") -> dict:
    return {
        "frame_index": idx,
        "event_type": event_type,
        "phase": "reconstruction",
        "title": "Map",
        "map_view": {
            "full_cells": [{"x": 0, "y": 0, "kind": "asteroid_shape_field"}],
            "cell_delta": [],
            "overlay_cells": [],
            "bbox": {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0},
        },
        "inspector": {},
        "metrics": {},
    }


def test_frame_has_renderable_map_cells() -> None:
    assert frame_has_renderable_map(_map_frame(0)) is True
    assert frame_has_renderable_map({"event_type": "x", "map_view": {}}) is False


def test_project_rttp_row_has_concrete_full_cells_no_inherited_mode() -> None:
    base = _map_frame(0)
    row = {
        "event_type": "routing.probe_started",
        "phase": "rttp_pipeline",
        "title": "RTTP pipeline started",
        "description": "probe domain snapshot",
        "metrics": {"skeleton_id": "sk1"},
        "cell_overlay_json": {"cells": [{"x": 1, "y": 0, "kind": "probe.path"}]},
    }
    out = project_rttp_row_to_product_frame(row, base_map_view=dict(base["map_view"]))
    assert out.get("render_mode") != "inherited_snapshot"
    assert "render_mode" not in out
    assert len(out["map_view"]["full_cells"]) >= 1
    assert out["description"] == "probe domain snapshot"
    assert len(out["map_view"]["overlay_cells"]) == 1


def test_interleave_inserts_after_renderable_not_tail_only() -> None:
    map_frames = [_map_frame(0), _map_frame(1)]
    rows = [
        {
            "event_type": "routing.probe_started",
            "phase": "rttp_pipeline",
            "title": "RTTP started",
            "description": "",
            "metrics": {},
            "cell_overlay_json": {},
        },
        {
            "event_type": "candidate.generated",
            "phase": "candidate_generation",
            "title": "Candidates",
            "description": "",
            "metrics": {},
            "cell_overlay_json": {},
        },
    ]
    out = interleave_rttp_snapshot_frames(map_frames, rows)
    assert len(out) == 4
    assert [f["frame_index"] for f in out] == [0, 1, 2, 3]
    rttp_idxs = [i for i, f in enumerate(out) if f["event_type"] in RTTP_MILESTONE_EVENT_TYPES]
    assert rttp_idxs == [2, 3]
    assert rttp_idxs[0] < len(out) - 1
    for fr in out:
        assert fr.get("render_mode") != "inherited_snapshot"
        if fr["event_type"] in RTTP_MILESTONE_EVENT_TYPES:
            assert len(fr["map_view"]["full_cells"]) >= 1


def test_last_renderable_prefers_candidate_generated_over_decode() -> None:
    frames = [
        _map_frame(0, "decode.started"),
        _map_frame(1, "candidate.generated"),
    ]
    assert last_renderable_frame_index(frames) == 1


@pytest.mark.django_db
@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_build_lab_replay_has_no_inherited_snapshot_when_rttp_track_exists() -> None:
    proj = m.AsteroidProject.objects.create(name="3bs", slug="3bs-compose")
    inp = create_copy_code_map_input(proj, _minimal_valid_copy())
    build_initial_replay_for_map_input(int(inp.pk), overwrite=True)
    run_solver_runtime_for_project(int(proj.pk), run_key="3bs", config={"rttp_record_replay": True})
    frames, _ = build_lab_replay_frames_for_project(int(proj.pk))
    assert frames
    assert all(fr.get("render_mode") != "inherited_snapshot" for fr in frames)
    rttp = [fr for fr in frames if fr["event_type"] in RTTP_MILESTONE_EVENT_TYPES]
    assert len(rttp) >= 4
    for fr in rttp:
        assert len(fr.get("map_view", {}).get("full_cells") or []) >= 1
