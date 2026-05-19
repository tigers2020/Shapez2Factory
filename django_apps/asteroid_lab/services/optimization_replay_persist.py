"""Persist optimization replay output to SolverRun.config_json (12C/PR7)."""

from __future__ import annotations

import logging
from typing import Any

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.replay_attach import (
    OptimizationReplayAttachReason,
    OptimizationReplayAttachResult,
)
from django_apps.asteroid_lab.optimization.replay_frame import OptimizationReplayFrame
from django_apps.asteroid_lab.services.optimization_ui_payload import (
    SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY,
    SOLVER_RUN_CONFIG_SERVER_XY_PARAMS_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
    optimization_replay_frames_to_json_list,
    validate_optimization_replay_frame_list_payload,
)

logger = logging.getLogger(__name__)


def merge_solver_summary_into_config(
    config_json: dict[str, Any],
    solver_summary: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(config_json)
    merged[SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY] = dict(solver_summary)
    return merged


def _finalize_attach(result: OptimizationReplayAttachResult, *, solver_run_id: int) -> None:
    logger.info(
        "optimization_replay_attach run_id=%s attached=%s reason=%s diagnostic=%s",
        solver_run_id,
        result.attached,
        result.reason.value,
        result.diagnostic,
    )


def persist_optimization_replay_frames_to_solver_run(
    solver_run_id: int,
    frames: tuple[OptimizationReplayFrame, ...],
    *,
    solver_summary: dict[str, Any] | None = None,
    server_xy_params: tuple[int, int] | None = None,
) -> OptimizationReplayAttachResult:
    """Merge replay frames into ``SolverRun.config_json``; return attach outcome."""

    if not frames:
        result = OptimizationReplayAttachResult(
            attached=False,
            reason=OptimizationReplayAttachReason.EMPTY_FRAMES,
        )
        _finalize_attach(result, solver_run_id=int(solver_run_id))
        return result

    json_list = optimization_replay_frames_to_json_list(frames)
    reject = validate_optimization_replay_frame_list_payload(json_list)
    if reject is not None:
        result = OptimizationReplayAttachResult(
            attached=False,
            reason=OptimizationReplayAttachReason.INVALID_REPLAY_PAYLOAD,
            diagnostic=reject,
        )
        _finalize_attach(result, solver_run_id=int(solver_run_id))
        return result

    run = m.SolverRun.objects.filter(pk=int(solver_run_id)).first()
    if run is None:
        result = OptimizationReplayAttachResult(
            attached=False,
            reason=OptimizationReplayAttachReason.INVALID_REPLAY_PAYLOAD,
            diagnostic="solver_run_not_found",
        )
        _finalize_attach(result, solver_run_id=int(solver_run_id))
        return result

    config = dict(run.config_json or {})
    config[SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY] = json_list
    if server_xy_params is not None:
        config[SOLVER_RUN_CONFIG_SERVER_XY_PARAMS_KEY] = [
            int(server_xy_params[0]),
            int(server_xy_params[1]),
        ]
    if solver_summary is not None:
        config = merge_solver_summary_into_config(config, solver_summary)
    run.config_json = config
    run.save(update_fields=["config_json"])
    result = OptimizationReplayAttachResult(
        attached=True,
        reason=OptimizationReplayAttachReason.ATTACHED,
    )
    _finalize_attach(result, solver_run_id=int(solver_run_id))
    return result
