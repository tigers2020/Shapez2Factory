"""HTTP / Run Solver entry: reconstruction → runtime pipeline → persist (PR8)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.loaded_snapshot import (
    loaded_reconstruction_snapshot_from_result,
)
from django_apps.asteroid_lab.replay.solver_runtime_unified_recorder import (
    SolverRuntimeReplayRecorder,
)
from django_apps.asteroid_lab.replay.unified_serialization import unified_replay_frame_to_json_dict
from django_apps.asteroid_lab.services.experiment_service import create_solver_run
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    build_lab_replay_frames_for_project,
)
from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
    run_reconstruction_for_map_input,
)
from django_apps.asteroid_lab.services.runtime_gene_template_resolver import (
    resolve_runtime_gene_templates_from_db,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_GENE_TEMPLATE_SOURCE_KEY,
    SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY,
    SOLVER_RUN_CONFIG_SERVER_XY_PARAMS_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)
from django_apps.asteroid_lab.services.solver_run_lab_summary import (
    lab_run_summary_from_solver_summary,
)
from django_apps.asteroid_lab.services.solver_runtime_pipeline import run_solver_runtime_pipeline


class SolverRuntimeEntryErrorCode(StrEnum):
    """Structured failure codes for solver runtime entry (no free-form strings)."""

    PROJECT_NOT_FOUND = "project_not_found"
    NO_MAP_INPUT = "no_map_input"
    NO_GENE_TEMPLATES_IN_DB = "no_gene_templates_in_db"


@dataclass(frozen=True, slots=True)
class SolverRuntimeEntryResult:
    """Outcome of one solver runtime entry invocation."""

    ok: bool
    solver_run_id: int | None
    lab_replay_frames_json: list[dict[str, Any]]
    replay_track_metrics: dict[str, Any]
    solver_summary: dict[str, Any]
    validation_passed: bool
    gene_template_source: dict[str, Any] = field(default_factory=dict)
    error_code: SolverRuntimeEntryErrorCode | None = None


def _empty_replay_for_project(project_id: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return build_lab_replay_frames_for_project(int(project_id))


def _persist_solver_run_outcome(
    run_id: int,
    *,
    solver_summary: dict[str, Any],
    server_xy_params: tuple[int, int],
    runtime_replay_frames_json: list[dict[str, Any]] | None = None,
) -> None:
    run = m.SolverRun.objects.get(pk=int(run_id))
    config = dict(run.config_json or {})
    config[SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY] = dict(solver_summary)
    config[SOLVER_RUN_CONFIG_SERVER_XY_PARAMS_KEY] = [
        int(server_xy_params[0]),
        int(server_xy_params[1]),
    ]
    if runtime_replay_frames_json is not None:
        config[SOLVER_RUN_CONFIG_RUNTIME_REPLAY_FRAMES_KEY] = runtime_replay_frames_json
    m.SolverRun.objects.filter(pk=int(run_id)).update(config_json=config)


def run_solver_runtime_for_project(
    project_id: int,
    *,
    run_key: str | None = None,
    config: dict[str, Any] | None = None,
    generator_version: str = "exhaustive_sample_gene_v1",
) -> SolverRuntimeEntryResult:
    """Execute Phase A→M for the latest map input."""

    if not m.AsteroidProject.objects.filter(pk=int(project_id)).exists():
        frames, metrics = _empty_replay_for_project(int(project_id))
        return SolverRuntimeEntryResult(
            ok=False,
            solver_run_id=None,
            lab_replay_frames_json=frames,
            replay_track_metrics=metrics,
            solver_summary={},
            validation_passed=False,
            error_code=SolverRuntimeEntryErrorCode.PROJECT_NOT_FOUND,
        )

    inp = (
        m.AsteroidMapInput.objects.filter(project_id=int(project_id))
        .order_by("-created_at", "-id")
        .first()
    )
    if inp is None:
        frames, metrics = _empty_replay_for_project(int(project_id))
        return SolverRuntimeEntryResult(
            ok=False,
            solver_run_id=None,
            lab_replay_frames_json=frames,
            replay_track_metrics=metrics,
            solver_summary={},
            validation_passed=False,
            error_code=SolverRuntimeEntryErrorCode.NO_MAP_INPUT,
        )

    gene_templates, gene_meta, gene_err = resolve_runtime_gene_templates_from_db(
        generator_version=generator_version,
    )
    if gene_err is not None or gene_templates is None:
        frames, metrics = _empty_replay_for_project(int(project_id))
        return SolverRuntimeEntryResult(
            ok=False,
            solver_run_id=None,
            lab_replay_frames_json=frames,
            replay_track_metrics=metrics,
            solver_summary={},
            validation_passed=False,
            error_code=SolverRuntimeEntryErrorCode.NO_GENE_TEMPLATES_IN_DB,
        )

    rk = run_key or f"runtime-{uuid.uuid4().hex[:12]}"
    gene_source_dict = gene_meta.to_json_dict() if gene_meta is not None else {}

    _cleanup, recon = run_reconstruction_for_map_input(int(inp.pk))
    loaded = loaded_reconstruction_snapshot_from_result(recon)

    run_config = dict(config or {})
    run_config[SOLVER_RUN_CONFIG_GENE_TEMPLATE_SOURCE_KEY] = gene_source_dict

    run_dto = create_solver_run(
        int(project_id),
        run_key=rk,
        algorithm_label="runtime_v0",
        config=run_config,
    )
    run_id = int(run_dto.id)

    server_xy_params = loaded.server_xy_params
    recorder: SolverRuntimeReplayRecorder | None = (
        SolverRuntimeReplayRecorder(loaded, server_xy_params)
        if server_xy_params is not None
        else None
    )

    try:
        result = run_solver_runtime_pipeline(
            loaded=loaded,
            gene_templates=gene_templates,
            run_key=rk,
            recorder=recorder,
        )
        runtime_replay_frames_json: list[dict[str, Any]] | None = None
        if recorder is not None:
            frames = recorder.build_frames()
            if frames:
                runtime_replay_frames_json = [
                    unified_replay_frame_to_json_dict(f) for f in frames
                ]
        _persist_solver_run_outcome(
            run_id,
            solver_summary=result.solver_summary,
            server_xy_params=loaded.server_xy_params,
            runtime_replay_frames_json=runtime_replay_frames_json,
        )

        validation_passed = bool(result.solver_summary.get("validation_passed"))
        status = (
            m.SolverRun.RunStatus.COMPLETED if validation_passed else m.SolverRun.RunStatus.FAILED
        )
        m.SolverRun.objects.filter(pk=run_id).update(status=status)

        frames, metrics = build_lab_replay_frames_for_project(int(project_id))
        return SolverRuntimeEntryResult(
            ok=True,
            solver_run_id=run_id,
            lab_replay_frames_json=frames,
            replay_track_metrics=metrics,
            solver_summary=dict(result.solver_summary),
            validation_passed=validation_passed,
            gene_template_source=gene_source_dict,
        )
    except Exception:
        m.SolverRun.objects.filter(pk=run_id).update(status=m.SolverRun.RunStatus.FAILED)
        raise


def entry_result_to_json_dict(result: SolverRuntimeEntryResult) -> dict[str, Any]:
    """JSON-serializable body for Lab POST responses."""

    summary = dict(result.solver_summary)
    body: dict[str, Any] = {
        "ok": result.ok,
        "solver_run_id": result.solver_run_id,
        "lab_replay_frames_json": result.lab_replay_frames_json,
        "replay_track_metrics": result.replay_track_metrics,
        "solver_summary": summary,
        "validation_passed": result.validation_passed,
        "validation_issue_codes": list(summary.get("issue_codes") or []),
        "validation_issue_details": list(summary.get("issue_details") or []),
        "gene_template_source": dict(result.gene_template_source),
    }
    if result.solver_run_id is not None:
        ui_status = "completed" if result.validation_passed else "failed"
        body["run_summary"] = lab_run_summary_from_solver_summary(
            run_id=int(result.solver_run_id),
            status=ui_status,
            solver_summary=summary,
        )
    if result.error_code is not None:
        body["error_code"] = result.error_code.value
    return body


__all__ = [
    "SolverRuntimeEntryErrorCode",
    "SolverRuntimeEntryResult",
    "entry_result_to_json_dict",
    "run_solver_runtime_for_project",
]
