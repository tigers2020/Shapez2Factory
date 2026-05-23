"""Lab replay track selection must not prefer RTTP-only optimization tracks."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.replay_track_keys import rttp_optimization_track_key
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.dto import SnapshotEventDTO
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    DIAGNOSTIC_LAB_TIMELINE_ADAPTER_FILTERED_ALL,
    build_lab_replay_frames_for_project,
    get_latest_lab_replay_track_for_project,
)
from django_apps.asteroid_lab.services.replay_recorder import ReplayRecorder

pytestmark = pytest.mark.django_db


def _reconstruction_frame_event() -> SnapshotEventDTO:
    return SnapshotEventDTO(
        event_key="recon-complete",
        phase="reconstruction",
        event_type=et.EVENT_TYPE_RECONSTRUCTION_MAP_COMPLETE,
        title="Reconstruction complete",
        is_decision_point=True,
        full_map=[{"x": 1, "y": 0, "cell_kind": "asteroid_shape_field"}],
    )


def _rttp_milestone_event() -> SnapshotEventDTO:
    return SnapshotEventDTO(
        event_key="rttp-start",
        phase="rttp_pipeline",
        event_type=et.EVENT_TYPE_ROUTING_PROBE_STARTED,
        title="RTTP pipeline started",
        is_decision_point=True,
    )


def test_latest_lab_replay_track_skips_rttp_optimization_track() -> None:
    project = m.AsteroidProject.objects.create(name="LabPick", slug="lab-pick")
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
    ReplayRecorder(inspection_track.id).record_event(_reconstruction_frame_event())

    solver_run = m.SolverRun.objects.create(
        project=project,
        run_key="rttp-solver-run",
        algorithm_label="rttp_v0.1",
        config_json={},
    )
    rttp_track = m.ReplayTrack.objects.create(
        project=project,
        track_key=rttp_optimization_track_key("rttp-solver-run"),
        solver_run=solver_run,
    )
    ReplayRecorder(rttp_track.id).record_event(_rttp_milestone_event())

    latest = get_latest_lab_replay_track_for_project(int(project.pk))
    assert latest is not None
    assert latest.id == inspection_track.id


def test_latest_lab_replay_track_skips_legacy_rttp_run_key_track() -> None:
    """PR #38 wrote frames to ``rttp-{run_key}`` before ``:rttp`` split."""

    project = m.AsteroidProject.objects.create(name="LegacyRttp", slug="legacy-rttp-pick")
    inspection_run = m.SolverRun.objects.create(
        project=project,
        run_key="inspection",
        algorithm_label="inspection_only",
        config_json={},
    )
    inspection_track = m.ReplayTrack.objects.create(
        project=project,
        track_key="inspection-legacy",
        solver_run=inspection_run,
    )
    ReplayRecorder(inspection_track.id).record_event(_reconstruction_frame_event())

    solver_run = m.SolverRun.objects.create(
        project=project,
        run_key="rttp-legacy-run",
        algorithm_label="rttp_v0.1",
        config_json={},
    )
    legacy_rttp_track = m.ReplayTrack.objects.create(
        project=project,
        track_key="rttp-legacy-run",
        solver_run=solver_run,
    )
    ReplayRecorder(legacy_rttp_track.id).record_event(_rttp_milestone_event())

    latest = get_latest_lab_replay_track_for_project(int(project.pk))
    assert latest is not None
    assert latest.id == inspection_track.id


def test_build_lab_replay_falls_back_to_inspection_when_latest_track_unrenderable() -> None:
    project = m.AsteroidProject.objects.create(name="Fallback", slug="lab-fallback")
    inspection_run = m.SolverRun.objects.create(
        project=project,
        run_key="inspection",
        algorithm_label="inspection_only",
        config_json={},
    )
    inspection_track = m.ReplayTrack.objects.create(
        project=project,
        track_key="inspection-fallback",
        solver_run=inspection_run,
    )
    ReplayRecorder(inspection_track.id).record_event(_reconstruction_frame_event())

    blocker_run = m.SolverRun.objects.create(
        project=project,
        run_key="blocker",
        algorithm_label="custom",
        config_json={},
    )
    blocker_track = m.ReplayTrack.objects.create(
        project=project,
        track_key="blocker-latest",
        solver_run=blocker_run,
    )
    ReplayRecorder(blocker_track.id).record_event(_rttp_milestone_event())

    frames, metrics = build_lab_replay_frames_for_project(int(project.pk))
    assert len(frames) >= 1
    assert metrics.get("frame_count") == len(frames)
    assert metrics.get("diagnostic_reason") is None


def test_build_lab_replay_diagnostic_when_only_rttp_orm_frames() -> None:
    project = m.AsteroidProject.objects.create(name="RttpOnly", slug="lab-rttp-only")
    solver_run = m.SolverRun.objects.create(
        project=project,
        run_key="rttp-only",
        algorithm_label="rttp_v0.1",
        config_json={},
    )
    rttp_track = m.ReplayTrack.objects.create(
        project=project,
        track_key="rttp-only-run",
        solver_run=solver_run,
    )
    ReplayRecorder(rttp_track.id).record_event(_rttp_milestone_event())

    frames, metrics = build_lab_replay_frames_for_project(int(project.pk))
    assert frames == []
    assert metrics.get("diagnostic_reason") == DIAGNOSTIC_LAB_TIMELINE_ADAPTER_FILTERED_ALL
