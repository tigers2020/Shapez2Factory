"""Optimization replay persist to SolverRun.config_json (PR7)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.enums import OptimizationReplayEventType
from django_apps.asteroid_lab.optimization.replay_frame import OptimizationReplayFrame
from django_apps.asteroid_lab.services.optimization_replay_persist import (
    persist_optimization_replay_frames_to_solver_run,
)
from django_apps.asteroid_lab.services.optimization_ui_payload import (
    SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
    deserialize_optimization_replay_frames_from_json,
)

pytestmark = pytest.mark.django_db


def test_persist_merges_frames_and_preserves_other_config_keys() -> None:
    proj = m.AsteroidProject.objects.create(name="ReplayPersist", slug="replay-persist")
    run = m.SolverRun.objects.create(
        project=proj,
        run_key="rk1",
        config_json={"existing_flag": True},
    )
    frames = (
        OptimizationReplayFrame(
            frame_index=0,
            event_type=OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED,
            title="loaded",
            description="",
        ),
    )
    summary = {"validation_passed": True, "confirmed_count": 0}

    ok = persist_optimization_replay_frames_to_solver_run(
        int(run.pk),
        frames,
        solver_summary=summary,
    )
    assert ok is True

    run.refresh_from_db()
    assert run.config_json["existing_flag"] is True
    assert SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY in run.config_json
    assert run.config_json[SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY]["validation_passed"] is True

    raw = run.config_json[SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY]
    restored = deserialize_optimization_replay_frames_from_json(raw)
    assert restored is not None
    assert len(restored) == 1
    assert restored[0].event_type is OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED


def test_persist_skips_invalid_payload() -> None:
    proj = m.AsteroidProject.objects.create(name="ReplaySkip", slug="replay-skip")
    run = m.SolverRun.objects.create(project=proj, run_key="rk2", config_json={})
    bad = (
        OptimizationReplayFrame(
            frame_index=5,
            event_type=OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED,
            title="bad index",
            description="",
        ),
    )
    ok = persist_optimization_replay_frames_to_solver_run(int(run.pk), bad)
    assert ok is False
    run.refresh_from_db()
    assert SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY not in run.config_json
