"""Run-scoped product replay timeline (Sequence 13C A-1)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.replay_track_keys import rttp_optimization_track_key
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.dto import SnapshotEventDTO
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    build_lab_replay_frames_for_project,
)
from django_apps.asteroid_lab.services.replay_recorder import ReplayRecorder
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY,
)

pytestmark = pytest.mark.django_db


def _recon_event() -> SnapshotEventDTO:
    return SnapshotEventDTO(
        event_key="recon-complete",
        phase="reconstruction",
        event_type=et.EVENT_TYPE_RECONSTRUCTION_MAP_COMPLETE,
        title="Reconstruction complete",
        is_decision_point=True,
        full_map=[{"x": 1, "y": 0, "cell_kind": "asteroid_shape_field"}],
    )


def _runtime_frame_dict(*, frame_index: int, tag: str) -> dict:
    return {
        "frame_index": frame_index,
        "frame_key": f"runtime-{tag}",
        "phase": "result",
        "event_type": "result.layout",
        "title": f"Runtime {tag}",
        "description": "",
        "map_view": {
            "full_cells": [],
            "overlay_cells": [],
            "cell_delta": [],
            "bbox": {"min_x": 0, "min_y": 0, "max_x": 0, "max_y": 0},
        },
        "metrics": {"replay_truncated": False},
        "inspector": {"runtime_tag": tag},
    }


def test_build_lab_replay_frames_for_run_uses_that_runs_config_json_not_latest() -> None:
    project = m.AsteroidProject.objects.create(name="RunScope", slug="run-scope")
    inspection_run = m.SolverRun.objects.create(
        project=project,
        run_key="inspection",
        algorithm_label="inspection_only",
        config_json={},
    )
    inspection_track = m.ReplayTrack.objects.create(
        project=project,
        track_key="inspection",
        solver_run=inspection_run,
    )
    ReplayRecorder(inspection_track.id).record_event(_recon_event())

    older_run = m.SolverRun.objects.create(
        project=project,
        run_key="rttp-old",
        algorithm_label="rttp_v0.1",
        config_json={
            SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY: [
                _runtime_frame_dict(frame_index=10, tag="old"),
            ],
        },
    )
    m.ReplayTrack.objects.create(
        project=project,
        track_key=rttp_optimization_track_key("rttp-old"),
        solver_run=older_run,
    )

    newer_run = m.SolverRun.objects.create(
        project=project,
        run_key="rttp-new",
        algorithm_label="rttp_v0.1",
        config_json={
            SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY: [
                _runtime_frame_dict(frame_index=10, tag="new"),
            ],
        },
    )
    m.ReplayTrack.objects.create(
        project=project,
        track_key=rttp_optimization_track_key("rttp-new"),
        solver_run=newer_run,
    )

    latest_frames, _ = build_lab_replay_frames_for_project(int(project.pk))
    old_frames, _ = build_lab_replay_frames_for_project(
        int(project.pk),
        solver_run_id=int(older_run.pk),
    )
    new_frames, _ = build_lab_replay_frames_for_project(
        int(project.pk),
        solver_run_id=int(newer_run.pk),
    )

    latest_tags = {
        str((fr.get("inspector") or {}).get("runtime_tag"))
        for fr in latest_frames
        if isinstance(fr, dict)
    }
    old_tags = {
        str((fr.get("inspector") or {}).get("runtime_tag"))
        for fr in old_frames
        if isinstance(fr, dict)
    }
    new_tags = {
        str((fr.get("inspector") or {}).get("runtime_tag"))
        for fr in new_frames
        if isinstance(fr, dict)
    }

    assert "new" in latest_tags
    assert "new" in new_tags
    assert "old" in old_tags
    assert "new" not in old_tags
    assert old_frames != new_frames


def test_build_lab_replay_frames_unknown_run_id_returns_empty() -> None:
    project = m.AsteroidProject.objects.create(name="NoRun", slug="no-run")
    frames, metrics = build_lab_replay_frames_for_project(
        int(project.pk),
        solver_run_id=999_999,
    )
    assert frames == []
    assert metrics["frame_count"] == 0
