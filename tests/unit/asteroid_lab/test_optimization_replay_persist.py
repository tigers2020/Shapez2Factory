"""Optimization replay persist to SolverRun.config_json (PR7)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.enums import OptimizationReplayEventType
from django_apps.asteroid_lab.optimization.replay_attach import OptimizationReplayAttachReason
from django_apps.asteroid_lab.optimization.replay_frame import OptimizationReplayFrame
from django_apps.asteroid_lab.services.optimization_replay_persist import (
    persist_optimization_replay_frames_to_solver_run,
)
from django_apps.asteroid_lab.services.optimization_ui_payload import (
    SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY,
    SOLVER_RUN_CONFIG_SERVER_XY_PARAMS_KEY,
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

    attach = persist_optimization_replay_frames_to_solver_run(
        int(run.pk),
        frames,
        solver_summary=summary,
        server_xy_params=(1, 0),
    )
    assert attach.attached is True
    assert attach.reason is OptimizationReplayAttachReason.ATTACHED

    run.refresh_from_db()
    assert run.config_json["existing_flag"] is True
    assert SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY in run.config_json
    assert run.config_json[SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY]["validation_passed"] is True
    assert run.config_json[SOLVER_RUN_CONFIG_SERVER_XY_PARAMS_KEY] == [1, 0]

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
    attach = persist_optimization_replay_frames_to_solver_run(int(run.pk), bad)
    assert attach.attached is False
    assert attach.reason is OptimizationReplayAttachReason.INVALID_REPLAY_PAYLOAD
    assert attach.diagnostic == "frame_index_not_contiguous"
    run.refresh_from_db()
    assert SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY not in run.config_json


def test_persist_empty_frames_attach_reason() -> None:
    proj = m.AsteroidProject.objects.create(name="ReplayEmpty", slug="replay-empty")
    run = m.SolverRun.objects.create(project=proj, run_key="rk3", config_json={})
    attach = persist_optimization_replay_frames_to_solver_run(int(run.pk), ())
    assert attach.attached is False
    assert attach.reason is OptimizationReplayAttachReason.EMPTY_FRAMES
