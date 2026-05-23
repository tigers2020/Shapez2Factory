"""Unified lab replay: map timeline + RTTP milestone tail."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.replay_track_keys import rttp_optimization_track_key
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.replay.replay_render_modes import RENDER_MODE_INHERITED_SNAPSHOT
from django_apps.asteroid_lab.services.dto import SnapshotEventDTO
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    RTTP_MILESTONE_EVENT_TYPES,
    build_lab_optimization_milestone_frames_for_project,
)
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    build_lab_replay_frames_for_project,
)
from django_apps.asteroid_lab.services.replay_recorder import ReplayRecorder

pytestmark = pytest.mark.django_db


def test_build_lab_replay_frames_appends_rttp_tail_when_track_exists() -> None:
    project = m.AsteroidProject.objects.create(name="UnifiedReplay", slug="uni-replay-append")
    inspection_run = m.SolverRun.objects.create(
        project=project,
        run_key="inspection-old",
        algorithm_label="inspection_only",
        config_json={},
    )
    inspection_track = m.ReplayTrack.objects.create(
        project=project,
        track_key="inspection-old-track",
        solver_run=inspection_run,
    )
    ReplayRecorder(inspection_track.id).record_event(
        SnapshotEventDTO(
            event_key="recon",
            phase="reconstruction",
            event_type=et.EVENT_TYPE_RECONSTRUCTION_MAP_COMPLETE,
            title="Reconstruction",
            is_decision_point=True,
            full_map=[{"x": 1, "y": 0, "cell_kind": "asteroid_shape_field"}],
        )
    )

    newer_run = m.SolverRun.objects.create(
        project=project,
        run_key="rttp-newer",
        algorithm_label="rttp_v0.1",
        config_json={},
    )
    rttp_track = m.ReplayTrack.objects.create(
        project=project,
        track_key=rttp_optimization_track_key("rttp-newer"),
        solver_run=newer_run,
    )
    ReplayRecorder(rttp_track.id).record_event(
        SnapshotEventDTO(
            event_key="mile",
            phase="rttp_pipeline",
            event_type=et.EVENT_TYPE_ROUTING_PROBE_STARTED,
            title="RTTP started",
            is_decision_point=True,
        )
    )

    milestone_frames, _milestone_metrics = build_lab_optimization_milestone_frames_for_project(
        int(project.pk),
        run_key=None,
    )
    assert len(milestone_frames) >= 1

    frames, metrics = build_lab_replay_frames_for_project(int(project.pk))
    map_only_count = len(frames) - len(milestone_frames)
    assert map_only_count >= 1
    assert len(frames) == map_only_count + len(milestone_frames)
    assert metrics["frame_count"] == len(frames)
    assert [f["frame_index"] for f in frames] == list(range(len(frames)))

    first_inherited = next(
        i for i, fr in enumerate(frames) if fr.get("render_mode") == RENDER_MODE_INHERITED_SNAPSHOT
    )
    map_prefix = frames[:first_inherited]
    assert map_prefix
    map_types = {fr["event_type"] for fr in map_prefix}
    assert map_types.isdisjoint(RTTP_MILESTONE_EVENT_TYPES)

    tail = frames[first_inherited:]
    assert tail
    for fr in tail:
        assert fr["render_mode"] == RENDER_MODE_INHERITED_SNAPSHOT
    assert {fr["event_type"] for fr in tail} <= RTTP_MILESTONE_EVENT_TYPES
