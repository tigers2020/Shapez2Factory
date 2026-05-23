"""Unit tests for RTTP full-snapshot compose projection (Sequence 3B-S)."""

from __future__ import annotations

import base64
import gzip
import json

import pytest
from django.test import override_settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    RTTP_MILESTONE_EVENT_TYPES,
)
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    build_lab_replay_frames_for_project,
)
from django_apps.asteroid_lab.services.lab_rttp_snapshot_compose import (
    clip_overlay_cells_to_base_map_domain,
    frame_has_renderable_map,
    interleave_rttp_snapshot_frames,
    last_renderable_frame_index,
    project_rttp_row_to_product_frame,
)
from django_apps.asteroid_lab.services.replay_pipeline_service import (
    build_initial_replay_for_map_input,
)
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
        "cell_overlay_json": {"cells": [{"x": 0, "y": 0, "kind": "probe.path"}]},
    }
    out = project_rttp_row_to_product_frame(row, base_map_view=dict(base["map_view"]))
    assert out.get("render_mode") != "inherited_snapshot"
    assert "render_mode" not in out
    assert len(out["map_view"]["full_cells"]) >= 1
    assert out["description"] == "probe domain snapshot"
    assert len(out["map_view"]["overlay_cells"]) == 1


def test_project_rttp_overlay_cells_clipped_to_base_map_domain() -> None:
    base_mv = {
        "full_cells": [{"x": 0, "y": 0, "kind": "asteroid_shape_field"}],
        "cell_delta": [],
        "overlay_cells": [],
        "bbox": {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0},
    }
    overlay = [
        {"x": 0, "y": 0, "kind": "route_domain.preferred"},
        {"x": 9, "y": 0, "kind": "probe.start"},
    ]
    clipped = clip_overlay_cells_to_base_map_domain(overlay, base_mv)
    assert clipped == [{"x": 0, "y": 0, "kind": "route_domain.preferred"}]


def test_project_rttp_overlay_ignores_legacy_server_fields_on_full_cells() -> None:
    base_mv = {
        "full_cells": [
            {
                "x": 10,
                "y": 20,
                "server_x": 5,
                "server_y": 6,
                "kind": "asteroid_shape_field",
            },
        ],
        "cell_delta": [],
        "overlay_cells": [],
        "bbox": {"min_x": 10, "min_y": 20, "max_x": 10, "max_y": 20},
    }
    overlay = [{"x": 10, "y": 20, "kind": "probe.start"}]
    clipped = clip_overlay_cells_to_base_map_domain(overlay, base_mv)
    assert clipped == [{"x": 10, "y": 20, "kind": "probe.start"}]


def test_project_rttp_overlay_clips_island_coords_to_base_anchors() -> None:
    lab_xy = (0, 1)
    base_mv = {
        "full_cells": [{"x": lab_xy[0], "y": lab_xy[1], "kind": "asteroid_shape_field"}],
        "cell_delta": [],
        "overlay_cells": [],
        "bbox": {"min_x": 0, "min_y": 1, "max_x": 0, "max_y": 1},
    }
    overlay = [{"x": lab_xy[0], "y": lab_xy[1], "kind": "probe.start"}]
    clipped = clip_overlay_cells_to_base_map_domain(overlay, base_mv)
    assert clipped == [{"x": lab_xy[0], "y": lab_xy[1], "kind": "probe.start"}]

    row = {
        "event_type": et.EVENT_TYPE_RTTP_ROUTE_DOMAIN_SNAPSHOT,
        "phase": "rttp_pipeline",
        "title": "RTTP",
        "description": "void overlay clipped",
        "metrics": {},
        "cell_overlay_json": {"cells": overlay},
    }
    out = project_rttp_row_to_product_frame(row, base_map_view=base_mv)
    assert out["map_view"]["overlay_cells"] == clipped


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


def test_interleave_per_row_anchor_chain_after_reconstruction() -> None:
    map_frames = [_map_frame(0), _map_frame(1)]
    rows = [
        {
            "event_type": "routing.probe_started",
            "phase": "rttp_pipeline",
            "title": "RTTP started",
            "description": "probe",
            "metrics": {},
            "cell_overlay_json": {"cells": [{"x": 9, "y": 0, "kind": "probe.start"}]},
        },
        {
            "event_type": "candidate.generated",
            "phase": "candidate_generation",
            "title": "Candidates",
            "description": "cands",
            "metrics": {},
            "cell_overlay_json": {},
        },
        {
            "event_type": "ga.best_updated",
            "phase": "genome_fitness",
            "title": "Selection",
            "description": "sel",
            "metrics": {},
            "cell_overlay_json": {},
        },
        {
            "event_type": "routing.committed",
            "phase": "incremental_commit",
            "title": "Commit",
            "description": "commit",
            "metrics": {},
            "cell_overlay_json": {"cells": [{"x": 5, "y": 0, "kind": "route.committed_path"}]},
        },
    ]
    out = interleave_rttp_snapshot_frames(map_frames, rows)
    assert len(out) == 6
    assert [f["event_type"] for f in out] == [
        "reconstruction.completed",
        "reconstruction.completed",
        et.EVENT_TYPE_RTTP_ROUTE_DOMAIN_SNAPSHOT,
        et.EVENT_TYPE_RTTP_CANDIDATE_POOL_SNAPSHOT,
        et.EVENT_TYPE_RTTP_GENOME_SELECTION_SNAPSHOT,
        et.EVENT_TYPE_RTTP_COMMIT_DOMAIN_SNAPSHOT,
    ]
    probe = out[2]
    assert probe["description"] == "probe"
    assert probe["map_view"]["overlay_cells"] == []
    assert out[5]["map_view"]["overlay_cells"] == []


def test_interleave_legacy_write_buffer_rows_emit_canonical_product_types() -> None:
    map_frames = [_map_frame(0)]
    rows = [
        {
            "event_type": et.EVENT_TYPE_ROUTING_PROBE_STARTED,
            "phase": "rttp_pipeline",
            "title": "legacy probe",
            "description": "legacy",
            "metrics": {},
            "cell_overlay_json": {},
        },
    ]
    out = interleave_rttp_snapshot_frames(map_frames, rows)
    assert len(out) == 2
    assert out[1]["event_type"] == et.EVENT_TYPE_RTTP_ROUTE_DOMAIN_SNAPSHOT


def test_interleave_skips_rttp_when_no_renderable_base() -> None:
    rows = [
        {
            "event_type": "routing.probe_started",
            "phase": "rttp_pipeline",
            "title": "RTTP started",
            "description": "",
            "metrics": {},
            "cell_overlay_json": {},
        },
    ]
    out = interleave_rttp_snapshot_frames([], rows)
    assert out == []


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
        assert fr.get("description", "").strip()
        assert len(fr.get("map_view", {}).get("overlay_cells") or []) >= 1
