"""Persist optimization replay output to SolverRun.config_json (12C/PR7)."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.replay_frame import OptimizationReplayFrame
from django_apps.asteroid_lab.services.optimization_ui_payload import (
    SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
    optimization_replay_frames_to_json_list,
    validate_optimization_replay_frame_list_payload,
)


def merge_solver_summary_into_config(
    config_json: dict[str, Any],
    solver_summary: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(config_json)
    merged[SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY] = dict(solver_summary)
    return merged


def persist_optimization_replay_frames_to_solver_run(
    solver_run_id: int,
    frames: tuple[OptimizationReplayFrame, ...],
    *,
    solver_summary: dict[str, Any] | None = None,
) -> bool:
    """Merge replay frames into ``SolverRun.config_json``; return False if guard rejects."""

    json_list = optimization_replay_frames_to_json_list(frames)
    reject = validate_optimization_replay_frame_list_payload(json_list)
    if reject is not None:
        return False

    run = m.SolverRun.objects.filter(pk=int(solver_run_id)).first()
    if run is None:
        return False

    config = dict(run.config_json or {})
    config[SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY] = json_list
    if solver_summary is not None:
        config = merge_solver_summary_into_config(config, solver_summary)
    run.config_json = config
    run.save(update_fields=["config_json"])
    return True
