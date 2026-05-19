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
from django_apps.asteroid_lab.optimization.replay_attach import OptimizationReplayAttachReason
from django_apps.asteroid_lab.services.experiment_service import create_solver_run
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    build_lab_replay_frames_for_project,
    optimization_replay_read_meta_for_project,
)
from django_apps.asteroid_lab.services.optimization_replay_persist import (
    persist_optimization_replay_frames_to_solver_run,
)
from django_apps.asteroid_lab.services.optimization_ui_payload import (
    SOLVER_RUN_CONFIG_GENE_TEMPLATE_SOURCE_KEY,
)
from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
    run_reconstruction_for_map_input,
)
from django_apps.asteroid_lab.services.runtime_gene_template_resolver import (
    resolve_runtime_gene_templates_from_db,
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
    PERSIST_REJECTED = "persist_rejected"


@dataclass(frozen=True, slots=True)
class SolverRuntimeEntryResult:
    """Outcome of one solver runtime entry invocation."""

    ok: bool
    solver_run_id: int | None
    lab_replay_frames_json: list[dict[str, Any]]
    replay_track_metrics: dict[str, Any]
    solver_summary: dict[str, Any]
    validation_passed: bool
    optimization_replay_attach: dict[str, Any]
    optimization_replay_read: dict[str, Any]
    gene_template_source: dict[str, Any] = field(default_factory=dict)
    error_code: SolverRuntimeEntryErrorCode | None = None


def _empty_replay_for_project(project_id: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return build_lab_replay_frames_for_project(int(project_id))


def run_solver_runtime_for_project(
    project_id: int,
    *,
    run_key: str | None = None,
    config: dict[str, Any] | None = None,
    generator_version: str = "exhaustive_sample_gene_v1",
) -> SolverRuntimeEntryResult:
    """Execute Phase A→M for the latest map input and persist optimization replay output."""

    empty_attach = {
        "attached": False,
        "reason": OptimizationReplayAttachReason.EMPTY_FRAMES.value,
    }
    empty_read = optimization_replay_read_meta_for_project(int(project_id))

    if not m.AsteroidProject.objects.filter(pk=int(project_id)).exists():
        frames, metrics = _empty_replay_for_project(int(project_id))
        return SolverRuntimeEntryResult(
            ok=False,
            solver_run_id=None,
            lab_replay_frames_json=frames,
            replay_track_metrics=metrics,
            solver_summary={},
            validation_passed=False,
            optimization_replay_attach=empty_attach,
            optimization_replay_read=empty_read,
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
            optimization_replay_attach=empty_attach,
            optimization_replay_read=empty_read,
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
            optimization_replay_attach=empty_attach,
            optimization_replay_read=empty_read,
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

    try:
        result = run_solver_runtime_pipeline(
            loaded=loaded,
            gene_templates=gene_templates,
            run_key=rk,
        )
        attach = persist_optimization_replay_frames_to_solver_run(
            run_id,
            result.replay_frames,
            solver_summary=result.solver_summary,
            server_xy_params=loaded.server_xy_params,
        )
        if not attach.attached:
            m.SolverRun.objects.filter(pk=run_id).update(status=m.SolverRun.RunStatus.FAILED)
            frames, metrics = _empty_replay_for_project(int(project_id))
            read_meta = optimization_replay_read_meta_for_project(int(project_id))
            return SolverRuntimeEntryResult(
                ok=False,
                solver_run_id=run_id,
                lab_replay_frames_json=frames,
                replay_track_metrics=metrics,
                solver_summary={},
                validation_passed=False,
                optimization_replay_attach=attach.to_json_dict(),
                optimization_replay_read=read_meta,
                gene_template_source=gene_source_dict,
                error_code=SolverRuntimeEntryErrorCode.PERSIST_REJECTED,
            )

        validation_passed = bool(result.solver_summary.get("validation_passed"))
        status = (
            m.SolverRun.RunStatus.COMPLETED if validation_passed else m.SolverRun.RunStatus.FAILED
        )
        m.SolverRun.objects.filter(pk=run_id).update(status=status)

        frames, metrics = build_lab_replay_frames_for_project(int(project_id))
        read_meta = optimization_replay_read_meta_for_project(int(project_id))
        return SolverRuntimeEntryResult(
            ok=True,
            solver_run_id=run_id,
            lab_replay_frames_json=frames,
            replay_track_metrics=metrics,
            solver_summary=dict(result.solver_summary),
            validation_passed=validation_passed,
            optimization_replay_attach=attach.to_json_dict(),
            optimization_replay_read=read_meta,
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
        "optimization_replay_attach": dict(result.optimization_replay_attach),
        "optimization_replay_read": dict(result.optimization_replay_read),
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
