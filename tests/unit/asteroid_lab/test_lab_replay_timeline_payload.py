"""Product replay timeline payload (Lab ORM + persisted optimization)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.enums import OptimizationReplayEventType
from django_apps.asteroid_lab.optimization.replay_frame import OptimizationReplayFrame
from django_apps.asteroid_lab.replay.unified_enums import ReplayPhase
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    build_lab_replay_frames_for_project,
    resolve_replay_projection_context_for_project,
)
from django_apps.asteroid_lab.services.optimization_replay_persist import (
    persist_optimization_replay_frames_to_solver_run,
)


def _decode_lab_frame(
    track: m.ReplayTrack,
    *,
    frame_index: int,
    x: int,
    y: int,
) -> m.ReplayFrame:
    return m.ReplayFrame.objects.create(
        replay_track=track,
        frame_index=frame_index,
        frame_key=f"lab-{frame_index}",
        phase="decode",
        title="Decode",
        description="",
        frame_payload={
            "event_type": "decode.raw_loaded",
            "phase": "decode",
            "phase_step": "raw",
            "event_key": f"step{frame_index}",
            "full_map": [
                {
                    "x": x,
                    "y": y,
                    "cell_kind": "asteroid",
                    "transport_kind": "none",
                }
            ],
        },
        cell_overlay_json={},
    )


@pytest.mark.django_db
def test_build_lab_replay_lab_only_monotonic_frame_indices() -> None:
    p = m.AsteroidProject.objects.create(name="UniLab", slug="uni-lab-payload")
    t = m.ReplayTrack.objects.create(project=p, track_key="uni-tr")
    _decode_lab_frame(t, frame_index=0, x=1, y=0)
    _decode_lab_frame(t, frame_index=1, x=2, y=0)

    frames, metrics = build_lab_replay_frames_for_project(int(p.pk))
    assert [f["frame_index"] for f in frames] == [0, 1]
    assert frames[0]["phase"] == ReplayPhase.DECODE.value
    assert metrics["frame_count"] == 2


@pytest.mark.django_db
def test_build_lab_replay_lab_precedes_optimization() -> None:
    p = m.AsteroidProject.objects.create(name="UniBoth", slug="uni-both-payload")
    t = m.ReplayTrack.objects.create(project=p, track_key="both-tr")
    _decode_lab_frame(t, frame_index=0, x=1, y=0)

    run = m.SolverRun.objects.create(
        project=p,
        run_key="uni-run",
        algorithm_label="runtime_v0",
        config_json={},
    )
    opt_frame = OptimizationReplayFrame(
        frame_index=0,
        event_type=OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED,
        title="input",
        description="",
        metrics={},
        visible_cells=(
            {
                "server_x": 0,
                "server_y": 0,
                "cell_kind": "asteroid",
                "transport_kind": "none",
            },
        ),
        overlay_cells=(),
    )
    persist_optimization_replay_frames_to_solver_run(int(run.pk), (opt_frame,))

    frames, _metrics = build_lab_replay_frames_for_project(int(p.pk))
    assert len(frames) == 2
    assert frames[0]["phase"] == ReplayPhase.DECODE.value
    assert frames[1]["phase"] == ReplayPhase.OPTIMIZATION_INPUT.value
    assert frames[1]["inspector"]["source_frame_index"] == 0


@pytest.mark.django_db
def test_resolve_projection_context_from_lab_cells() -> None:
    p = m.AsteroidProject.objects.create(name="Proj", slug="proj-params")
    t = m.ReplayTrack.objects.create(project=p, track_key="tr")
    _decode_lab_frame(t, frame_index=0, x=1, y=2)

    ctx = resolve_replay_projection_context_for_project(int(p.pk))
    assert ctx is not None
    assert ctx.server_xy_params[0] >= 0


@pytest.mark.django_db
def test_build_lab_replay_skips_unsupported_lab_frames() -> None:
    p = m.AsteroidProject.objects.create(name="Skip", slug="uni-skip-lab")
    t = m.ReplayTrack.objects.create(project=p, track_key="skip-tr")
    m.ReplayFrame.objects.create(
        replay_track=t,
        frame_index=0,
        frame_key="bad",
        phase="existing_layout",
        title="Bad",
        description="",
        frame_payload={"event_type": "existing_layout.begin"},
        cell_overlay_json={},
    )
    _decode_lab_frame(t, frame_index=1, x=1, y=0)

    frames, _metrics = build_lab_replay_frames_for_project(int(p.pk))
    assert len(frames) == 1
    assert frames[0]["frame_index"] == 0


@pytest.mark.django_db
def test_build_lab_replay_truncation_surfaces_track_metrics(monkeypatch: pytest.MonkeyPatch) -> None:
    from django_apps.asteroid_lab.replay import replay_limits

    monkeypatch.setattr(replay_limits, "MAX_UNIFIED_LAB_REPLAY_FRAMES", 2)

    p = m.AsteroidProject.objects.create(name="Trunc", slug="uni-trunc")
    t = m.ReplayTrack.objects.create(project=p, track_key="trunc-tr")
    for i in range(3):
        _decode_lab_frame(t, frame_index=i, x=i + 1, y=0)

    frames, metrics = build_lab_replay_frames_for_project(int(p.pk))
    assert len(frames) == 2
    assert metrics["replay_truncated"] is True
    assert metrics["dropped_frame_count"] == 1
