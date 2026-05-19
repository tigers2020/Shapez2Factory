"""Read-only optimization replay track from SolverRun.config_json (12G, PR8)."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.optimization_ui_payload import (
    OPTIMIZATION_REPLAY_DIAGNOSTIC_REASON_METRIC_KEY,
    SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY,
    build_optimization_replay_track_payload,
    deserialize_optimization_replay_frames_from_json,
    empty_optimization_replay_track_payload,
)


class OptimizationReplayDiagnosticReason(StrEnum):
    """Read-path diagnostic codes (metadata only; never solver input)."""

    MISSING_OPTIMIZATION_REPLAY = "missing_optimization_replay"
    EMPTY_OPTIMIZATION_REPLAY_FRAMES = "empty_optimization_replay_frames"
    INVALID_OPTIMIZATION_REPLAY_PAYLOAD = "invalid_optimization_replay_payload"


def _track_with_diagnostic(reason: OptimizationReplayDiagnosticReason) -> dict[str, Any]:
    track = empty_optimization_replay_track_payload()
    metrics = dict(track["metrics"])
    metrics[OPTIMIZATION_REPLAY_DIAGNOSTIC_REASON_METRIC_KEY] = reason.value
    track["metrics"] = metrics
    return track


def optimization_replay_payload_for_project(project_id: int) -> dict[str, Any]:
    """Build Lab read-model track for the latest project ``SolverRun`` (output-only)."""

    run = (
        m.SolverRun.objects.filter(project_id=int(project_id))
        .order_by("-created_at", "-id")
        .first()
    )
    missing = OptimizationReplayDiagnosticReason.MISSING_OPTIMIZATION_REPLAY
    if run is None:
        return _track_with_diagnostic(missing)

    config = dict(run.config_json or {})
    raw = config.get(SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY)
    if raw is None:
        return _track_with_diagnostic(missing)
    if isinstance(raw, list) and len(raw) == 0:
        empty = OptimizationReplayDiagnosticReason.EMPTY_OPTIMIZATION_REPLAY_FRAMES
        return _track_with_diagnostic(empty)

    frames = deserialize_optimization_replay_frames_from_json(raw)
    if frames is None:
        return _track_with_diagnostic(
            OptimizationReplayDiagnosticReason.INVALID_OPTIMIZATION_REPLAY_PAYLOAD
        )
    return build_optimization_replay_track_payload(frames)


def empty_optimization_replay_track_with_missing_diagnostic() -> dict[str, Any]:
    """Neutral track when no project scope or no solver run yet."""

    return _track_with_diagnostic(OptimizationReplayDiagnosticReason.MISSING_OPTIMIZATION_REPLAY)


__all__ = [
    "OptimizationReplayDiagnosticReason",
    "empty_optimization_replay_track_with_missing_diagnostic",
    "optimization_replay_payload_for_project",
]
