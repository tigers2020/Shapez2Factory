from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.replay_track_keys import rttp_optimization_track_key
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.dto import SnapshotEventDTO
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    DIAGNOSTIC_EMPTY_OPTIMIZATION_MILESTONE_FRAMES,
    DIAGNOSTIC_MISSING_OPTIMIZATION_MILESTONE_TRACK,
    RTTP_MILESTONE_EVENT_TYPES,
    build_lab_optimization_milestone_frames_for_project,
)
from django_apps.asteroid_lab.services.replay_recorder import ReplayRecorder
from tests.support.rttp_milestone_contract import FORBIDDEN_MILESTONE_MAP_KEYS

pytestmark = pytest.mark.django_db


def _rttp_event(
    event_type: str,
    *,
    frame_key: str,
    metrics_json: dict | None = None,
) -> SnapshotEventDTO:
    return SnapshotEventDTO(
        event_key=frame_key,
        phase="rttp_pipeline",
        event_type=event_type,
        title=f"title:{event_type}",
        metrics_json=dict(metrics_json or {}),
    )


def test_build_milestone_frames_from_rttp_track() -> None:
    project = m.AsteroidProject.objects.create(name="Mile", slug="mile-1")
    run = m.SolverRun.objects.create(
        project=project,
        run_key="run-a",
        algorithm_label="rttp_v0.1",
        config_json={},
    )
    track = m.ReplayTrack.objects.create(
        project=project,
        track_key=rttp_optimization_track_key("run-a"),
        solver_run=run,
    )
    rec = ReplayRecorder(track.id)
    for i, etype in enumerate(sorted(RTTP_MILESTONE_EVENT_TYPES)):
        rec.record_event(_rttp_event(etype, frame_key=f"k{i}", metrics_json={"step": i}))

    frames, metrics = build_lab_optimization_milestone_frames_for_project(
        int(project.pk),
        run_key="run-a",
    )
    assert len(frames) == 4
    assert metrics["frame_count"] == 4
    assert metrics["track_key"] == rttp_optimization_track_key("run-a")
    assert set(metrics["event_types"]) == set(RTTP_MILESTONE_EVENT_TYPES)
    for visible_idx, fr in enumerate(frames):
        assert fr["frame_index"] == visible_idx
        assert set(fr.keys()).isdisjoint(FORBIDDEN_MILESTONE_MAP_KEYS)
        assert fr["event_type"] in RTTP_MILESTONE_EVENT_TYPES
        assert isinstance(fr["metrics"], dict)


def test_milestone_payload_allows_overlay_in_write_buffer_not_in_section_b() -> None:
    project = m.AsteroidProject.objects.create(name="OverlayBuf", slug="overlay-buf")
    run = m.SolverRun.objects.create(
        project=project,
        run_key="run-ov",
        algorithm_label="rttp_v0.1",
        config_json={},
    )
    track = m.ReplayTrack.objects.create(
        project=project,
        track_key=rttp_optimization_track_key("run-ov"),
        solver_run=run,
    )
    rec = ReplayRecorder(track.id)
    rec.record_event(
        SnapshotEventDTO(
            event_key="ov",
            phase="rttp_pipeline",
            event_type=et.EVENT_TYPE_ROUTING_PROBE_STARTED,
            title="RTTP started",
            description="route domain snapshot",
            cell_overlay_json={"cells": [{"x": 1, "y": 0, "kind": "probe.start"}]},
        )
    )
    frames, metrics = build_lab_optimization_milestone_frames_for_project(
        int(project.pk),
        run_key="run-ov",
    )
    assert len(frames) == 1
    assert metrics["frame_count"] == 1
    assert frames[0]["description"] == "route domain snapshot"
    assert set(frames[0].keys()).isdisjoint(FORBIDDEN_MILESTONE_MAP_KEYS)


def test_skips_payload_with_forbidden_map_keys() -> None:
    project = m.AsteroidProject.objects.create(name="MapKey", slug="map-key")
    run = m.SolverRun.objects.create(
        project=project,
        run_key="run-map",
        algorithm_label="rttp_v0.1",
        config_json={},
    )
    track = m.ReplayTrack.objects.create(
        project=project,
        track_key=rttp_optimization_track_key("run-map"),
        solver_run=run,
    )
    rec = ReplayRecorder(track.id)
    rec.record_event(_rttp_event(et.EVENT_TYPE_ROUTING_PROBE_STARTED, frame_key="ok"))
    bad = _rttp_event(et.EVENT_TYPE_CANDIDATE_GENERATED, frame_key="bad")
    rec.record_event(
        SnapshotEventDTO(
            event_key=bad.event_key,
            phase=bad.phase,
            event_type=bad.event_type,
            title=bad.title,
            full_map=[{"x": 1, "y": 0}],
        )
    )
    frames, _metrics = build_lab_optimization_milestone_frames_for_project(
        int(project.pk),
        run_key="run-map",
    )
    assert len(frames) == 1
    assert frames[0]["event_type"] == et.EVENT_TYPE_RTTP_ROUTE_DOMAIN_SNAPSHOT


def test_skips_non_milestone_registered_event_type() -> None:
    project = m.AsteroidProject.objects.create(name="NonMile", slug="non-mile")
    run = m.SolverRun.objects.create(
        project=project,
        run_key="run-x",
        algorithm_label="rttp_v0.1",
        config_json={},
    )
    track = m.ReplayTrack.objects.create(
        project=project,
        track_key=rttp_optimization_track_key("run-x"),
        solver_run=run,
    )
    rec = ReplayRecorder(track.id)
    rec.record_event(_rttp_event(et.EVENT_TYPE_ROUTING_PROBE_STARTED, frame_key="mile"))
    rec.record_event(
        SnapshotEventDTO(
            event_key="recon",
            phase="reconstruction",
            event_type=et.EVENT_TYPE_RECONSTRUCTION_MAP_COMPLETE,
            title="should not appear in Section B",
            is_decision_point=True,
            full_map=[{"x": 1, "y": 0, "cell_kind": "asteroid_shape_field"}],
        )
    )
    frames, metrics = build_lab_optimization_milestone_frames_for_project(
        int(project.pk),
        run_key="run-x",
    )
    assert len(frames) == 1
    assert metrics["frame_count"] == 1


def test_missing_rttp_track_diagnostic() -> None:
    project = m.AsteroidProject.objects.create(name="NoRttp", slug="no-rttp")
    frames, metrics = build_lab_optimization_milestone_frames_for_project(
        int(project.pk),
        run_key="missing",
    )
    assert frames == []
    assert metrics["diagnostic_reason"] == DIAGNOSTIC_MISSING_OPTIMIZATION_MILESTONE_TRACK


def test_missing_rttp_track_includes_run_context() -> None:
    project = m.AsteroidProject.objects.create(name="RunNoTrack", slug="run-no-track")
    run = m.SolverRun.objects.create(
        project=project,
        run_key="orphan",
        algorithm_label="rttp_v0.1",
        config_json={},
    )
    track_key = rttp_optimization_track_key("orphan")
    frames, metrics = build_lab_optimization_milestone_frames_for_project(
        int(project.pk),
        run_key="orphan",
    )
    assert frames == []
    assert metrics["diagnostic_reason"] == DIAGNOSTIC_MISSING_OPTIMIZATION_MILESTONE_TRACK
    assert metrics["track_key"] == track_key
    assert metrics["source_solver_run_id"] == int(run.pk)


def test_empty_rttp_track_diagnostic() -> None:
    project = m.AsteroidProject.objects.create(name="Empty", slug="empty-rttp")
    run = m.SolverRun.objects.create(
        project=project,
        run_key="empty",
        algorithm_label="rttp_v0.1",
        config_json={},
    )
    track_key = rttp_optimization_track_key("empty")
    m.ReplayTrack.objects.create(
        project=project,
        track_key=track_key,
        solver_run=run,
    )
    frames, metrics = build_lab_optimization_milestone_frames_for_project(
        int(project.pk),
        run_key="empty",
    )
    assert frames == []
    assert metrics["diagnostic_reason"] == DIAGNOSTIC_EMPTY_OPTIMIZATION_MILESTONE_FRAMES
    assert metrics["track_key"] == track_key
    assert metrics["source_solver_run_id"] == int(run.pk)
