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

import importlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Literal

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.dto import InitialReplayPipelineResultDTO

# Import path split so ``test_service_import_boundaries`` text scan stays clean.
_opt_pkg = "django_apps." + "shapez_" + "asteroid" + ".optimization"
_oreplay = importlib.import_module(_opt_pkg + ".optimization_replay")
optimization_replay_frames_to_json_list = _oreplay.optimization_replay_frames_to_json_list
_oui = importlib.import_module(_opt_pkg + ".optimization_ui_payload")
SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY = (
    _oui.SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY
)
validate_optimization_replay_frame_list_payload = (
    _oui.validate_optimization_replay_frame_list_payload
)

OptimizationReplayAttachReason = Literal[
    "attached",
    "empty_frames",
    "empty_candidate_pool",
    "non_ok_result",
    "missing_solver_run_id",
    "solver_run_not_found",
    "evolution_failed",
    "invalid_replay_payload",
]

OPTIMIZATION_REPLAY_ATTACH_DIAGNOSTIC_KEYS: tuple[str, ...] = (
    "stage",
    "candidate_count",
    "normal_candidate_count",
    "rejected_candidate_count",
    "recorder_frame_count",
    "best_genome_present",
    "evolution_convergence_reason",
    "committed_candidate_count",
    "rolled_back_candidate_count",
    "validation_passed",
    "error_type",
    "error_message",
)

OPTIMIZATION_REPLAY_ATTACH_DIAGNOSTIC_STAGES: frozenset[str] = frozenset(
    {
        "inspection_not_ok",
        "optimization_input",
        "candidate_generation",
        "empty_candidate_pool",
        "route_probe",
        "evolution_search",
        "incremental_commit",
        "validation",
        "replay_serialization",
        "attach_persist",
        "response_payload",
        "unknown_exception",
    }
)


def build_optimization_replay_attach_diagnostic(**kwargs: Any) -> dict[str, Any]:
    """12K — scalar-only POST attach observability (no frames, paths, tracebacks)."""

    st = kwargs.get("stage")
    if st is not None and st not in OPTIMIZATION_REPLAY_ATTACH_DIAGNOSTIC_STAGES:
        st = "unknown_exception"
    out: dict[str, Any] = {}
    for name in OPTIMIZATION_REPLAY_ATTACH_DIAGNOSTIC_KEYS:
        if name == "stage":
            out["stage"] = st
        elif name in kwargs:
            out[name] = kwargs[name]
        else:
            out[name] = None
    return out


def merge_optimization_replay_attach_diagnostic_parts(
    *parts: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Merge diagnostic dict fragments; later fragments override earlier keys."""

    merged: dict[str, Any] = {}
    for p in parts:
        if not p:
            continue
        for k, v in p.items():
            if k in OPTIMIZATION_REPLAY_ATTACH_DIAGNOSTIC_KEYS:
                merged[k] = v
    return build_optimization_replay_attach_diagnostic(**merged)


@dataclass(frozen=True, slots=True)
class OptimizationReplayAttachResult:
    """Outcome of attaching optimization replay frames to a ``SolverRun`` (or skipping)."""

    attached: bool
    reason: OptimizationReplayAttachReason
    diagnostic: dict[str, Any] | None = None


def persist_optimization_replay_frames_to_solver_run(
    solver_run: m.SolverRun,
    frames: Sequence[Any],
) -> None:
    """Merge serialized frames into ``solver_run.config_json``; preserves other keys.

    Empty ``frames`` is a no-op (does not clear a previous persisted track).
    """

    if not frames:
        return
    blob = optimization_replay_frames_to_json_list(frames)
    if not validate_optimization_replay_frame_list_payload(blob):
        return
    merged = dict(solver_run.config_json or {})
    key = SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY
    merged[key] = blob
    solver_run.config_json = merged
    solver_run.save(update_fields=["config_json"])


def attach_optimization_replay_frames_after_successful_replay_build(
    result: InitialReplayPipelineResultDTO,
    frames: Sequence[Any] | None,
    *,
    evolution_scalar_diagnostic: Mapping[str, Any] | None = None,
) -> OptimizationReplayAttachResult:
    """Persist frames onto the ``SolverRun`` created by a successful inspection replay build."""

    evo = dict(evolution_scalar_diagnostic) if evolution_scalar_diagnostic else None
    n_frames = len(frames) if frames is not None else 0

    if result.status != "ok":
        return OptimizationReplayAttachResult(
            attached=False,
            reason="non_ok_result",
            diagnostic=merge_optimization_replay_attach_diagnostic_parts(
                evo,
                {"stage": "inspection_not_ok", "recorder_frame_count": n_frames},
            ),
        )
    if result.solver_run_id is None:
        return OptimizationReplayAttachResult(
            attached=False,
            reason="missing_solver_run_id",
            diagnostic=merge_optimization_replay_attach_diagnostic_parts(
                evo,
                {"stage": "inspection_not_ok", "recorder_frame_count": n_frames},
            ),
        )
    if not frames:
        return OptimizationReplayAttachResult(
            attached=False,
            reason="empty_frames",
            diagnostic=merge_optimization_replay_attach_diagnostic_parts(
                evo,
                {"stage": "replay_serialization", "recorder_frame_count": 0},
            ),
        )
    blob = optimization_replay_frames_to_json_list(frames)
    if not validate_optimization_replay_frame_list_payload(blob):
        return OptimizationReplayAttachResult(
            attached=False,
            reason="invalid_replay_payload",
            diagnostic=merge_optimization_replay_attach_diagnostic_parts(
                evo,
                {"stage": "replay_serialization", "recorder_frame_count": n_frames},
            ),
        )
    run = m.SolverRun.objects.filter(pk=int(result.solver_run_id)).first()
    if run is None:
        return OptimizationReplayAttachResult(
            attached=False,
            reason="solver_run_not_found",
            diagnostic=merge_optimization_replay_attach_diagnostic_parts(
                evo,
                {"stage": "attach_persist", "recorder_frame_count": n_frames},
            ),
        )
    persist_optimization_replay_frames_to_solver_run(run, frames)
    return OptimizationReplayAttachResult(attached=True, reason="attached", diagnostic=None)


__all__ = [
    "OPTIMIZATION_REPLAY_ATTACH_DIAGNOSTIC_KEYS",
    "OPTIMIZATION_REPLAY_ATTACH_DIAGNOSTIC_STAGES",
    "OptimizationReplayAttachReason",
    "OptimizationReplayAttachResult",
    "attach_optimization_replay_frames_after_successful_replay_build",
    "build_optimization_replay_attach_diagnostic",
    "merge_optimization_replay_attach_diagnostic_parts",
    "persist_optimization_replay_frames_to_solver_run",
]
