"""Artifact replay files are the first authority for lazy replay payloads."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.lab_replay_persisted_cache import (
    is_cache_summary_valid,
    load_composed_frames_for_run_id,
    load_manifest_summary_for_run_id,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY,
)

pytestmark = pytest.mark.django_db


def _write_replay_core(path: Path, frames: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True)
    path.write_text(
        "".join(f"{json.dumps(frame, sort_keys=True)}\n" for frame in frames),
        encoding="utf-8",
    )


def test_artifact_jsonl_does_not_return_stale_non_renderable_db_cache(tmp_path: Path) -> None:
    project = m.AsteroidProject.objects.create(name="ArtifactFirst", slug="artifact-first")
    replay_path = tmp_path / "output" / "replay_core.jsonl"
    artifact_frames = [
        {"frame_index": 0, "phase": "artifact-decode"},
        {"frame_index": 1, "phase": "artifact-solve"},
    ]
    _write_replay_core(replay_path, artifact_frames)
    run = m.SolverRun.objects.create(
        project=project,
        run_key="artifact-first-run",
        artifact_root=str(tmp_path.resolve()),
        lifecycle_status="succeeded",
        lab_replay_manifest_summary_json={
            "mode": "artifact_jsonl",
            "artifact_run_key": "artifact-first-run",
            "replay_core_path": str(replay_path.resolve()),
            "frame_count": 2,
            "preview_frame_index": 1,
            "preview_frame": artifact_frames[1],
            "replay_track_metrics": {},
        },
        lab_replay_payload_json={
            "composed_frames": [{"frame_index": 99, "phase": "stale-db-payload"}],
        },
        config_json={
            SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY: [
                {"frame_index": 100, "phase": "stale-config"}
            ],
        },
    )

    loaded_frames = load_composed_frames_for_run_id(int(run.pk))
    summary = load_manifest_summary_for_run_id(int(run.pk))

    assert loaded_frames is None
    assert summary is not None
    assert is_cache_summary_valid(summary)
    assert summary["mode"] == "artifact_jsonl"


def test_dedicated_payload_wins_over_legacy_config_cache() -> None:
    project = m.AsteroidProject.objects.create(name="PayloadFirst", slug="payload-first")
    expected_frames = [
        {
            "frame_index": 0,
            "phase": "dedicated-payload",
            "event_type": "result.layout",
            "title": "payload",
            "description": "",
            "map_view": {
                "full_cells": [{"x": 0, "y": 0, "kind": "asteroid_shape_field"}],
                "cell_delta": [],
                "overlay_cells": [],
                "annotations": [],
                "bbox": {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0},
            },
        }
    ]
    run = m.SolverRun.objects.create(
        project=project,
        run_key="payload-first-run",
        lab_replay_manifest_summary_json={"frame_count": 1},
        lab_replay_payload_json={"composed_frames": expected_frames},
        config_json={
            SOLVER_RUN_CONFIG_LAB_REPLAY_COMPOSED_FRAMES_KEY: [
                {"frame_index": 50, "phase": "stale-config"}
            ],
        },
    )

    assert load_composed_frames_for_run_id(int(run.pk)) == expected_frames
