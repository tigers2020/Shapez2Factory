"""12C — Write optimization replay frames to ``SolverRun.config_json`` (output-only).

Callers that run the inspection replay pipeline via
:func:`~django_apps.asteroid_lab.services.replay_pipeline_service.build_initial_replay_for_map_input`
must not import this module from ``replay_pipeline_service`` (import boundary).

After a successful
:class:`~django_apps.asteroid_lab.services.dto.InitialReplayPipelineResultDTO`,
optimization runners may call
:func:`attach_optimization_replay_frames_after_successful_replay_build`
with recorded frames so Lab context (12B) can read them from ``config_json``.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Literal

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.dto import InitialReplayPipelineResultDTO
from django_apps.shapez_asteroid.optimization.dto import OptimizationReplayFrame
from django_apps.shapez_asteroid.optimization.optimization_replay import (
    optimization_replay_frames_to_json_list,
)
from django_apps.shapez_asteroid.optimization.optimization_ui_payload import (
    SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY,
)

OptimizationReplayAttachReason = Literal[
    "attached",
    "empty_frames",
    "non_ok_result",
    "missing_solver_run_id",
    "solver_run_not_found",
    "evolution_failed",
]


@dataclass(frozen=True, slots=True)
class OptimizationReplayAttachResult:
    """Outcome of attaching optimization replay frames to a ``SolverRun`` (or skipping)."""

    attached: bool
    reason: OptimizationReplayAttachReason


def persist_optimization_replay_frames_to_solver_run(
    solver_run: m.SolverRun,
    frames: Sequence[OptimizationReplayFrame],
) -> None:
    """Merge serialized frames into ``solver_run.config_json``; preserves other keys.

    Empty ``frames`` is a no-op (does not clear a previous persisted track).
    """

    if not frames:
        return
    merged = dict(solver_run.config_json or {})
    key = SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY
    merged[key] = optimization_replay_frames_to_json_list(frames)
    solver_run.config_json = merged
    solver_run.save(update_fields=["config_json"])


def attach_optimization_replay_frames_after_successful_replay_build(
    result: InitialReplayPipelineResultDTO,
    frames: Sequence[OptimizationReplayFrame] | None,
) -> OptimizationReplayAttachResult:
    """Persist frames onto the ``SolverRun`` created by a successful inspection replay build."""

    if result.status != "ok":
        return OptimizationReplayAttachResult(attached=False, reason="non_ok_result")
    if result.solver_run_id is None:
        return OptimizationReplayAttachResult(attached=False, reason="missing_solver_run_id")
    if not frames:
        return OptimizationReplayAttachResult(attached=False, reason="empty_frames")
    run = m.SolverRun.objects.filter(pk=int(result.solver_run_id)).first()
    if run is None:
        return OptimizationReplayAttachResult(attached=False, reason="solver_run_not_found")
    persist_optimization_replay_frames_to_solver_run(run, frames)
    return OptimizationReplayAttachResult(attached=True, reason="attached")


__all__ = [
    "OptimizationReplayAttachReason",
    "OptimizationReplayAttachResult",
    "attach_optimization_replay_frames_after_successful_replay_build",
    "persist_optimization_replay_frames_to_solver_run",
]
