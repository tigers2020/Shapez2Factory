"""HTTP / Run Solver entry: reconstruction → runtime pipeline → persist (PR8)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any

from django.conf import settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.loaded_snapshot import (
    loaded_reconstruction_snapshot_from_result,
)
from django_apps.asteroid_lab.services.experiment_service import create_solver_run
from django_apps.asteroid_lab.services.optimization_replay_persist import (
    persist_optimization_replay_frames_to_solver_run,
)
from django_apps.asteroid_lab.services.optimization_replay_read import (
    optimization_replay_payload_for_project,
)
from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
    run_reconstruction_for_map_input,
)
from django_apps.asteroid_lab.services.solver_runtime_pipeline import run_solver_runtime_pipeline


class SolverRuntimeEntryErrorCode(StrEnum):
    """Structured failure codes for solver runtime entry (no free-form strings)."""

    PROJECT_NOT_FOUND = "project_not_found"
    NO_MAP_INPUT = "no_map_input"
    PERSIST_REJECTED = "persist_rejected"


@dataclass(frozen=True, slots=True)
class SolverRuntimeEntryResult:
    """Outcome of one solver runtime entry invocation."""

    ok: bool
    solver_run_id: int | None
    optimization_replay: dict[str, Any]
    solver_summary: dict[str, Any]
    validation_passed: bool
    error_code: SolverRuntimeEntryErrorCode | None = None


def default_runtime_gene_templates_path() -> Path:
    return Path(settings.ASTEROID_LAB_RUNTIME_GENE_TEMPLATES_PATH)


def run_solver_runtime_for_project(
    project_id: int,
    *,
    run_key: str | None = None,
    gene_template_path: str | Path | None = None,
    config: dict[str, Any] | None = None,
) -> SolverRuntimeEntryResult:
    """Execute Phase A→M for the latest map input and persist optimization replay output."""

    if not m.AsteroidProject.objects.filter(pk=int(project_id)).exists():
        empty = optimization_replay_payload_for_project(int(project_id))
        return SolverRuntimeEntryResult(
            ok=False,
            solver_run_id=None,
            optimization_replay=empty,
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
        empty = optimization_replay_payload_for_project(int(project_id))
        return SolverRuntimeEntryResult(
            ok=False,
            solver_run_id=None,
            optimization_replay=empty,
            solver_summary={},
            validation_passed=False,
            error_code=SolverRuntimeEntryErrorCode.NO_MAP_INPUT,
        )

    rk = run_key or f"runtime-{uuid.uuid4().hex[:12]}"
    if gene_template_path is not None:
        template_path = Path(gene_template_path)
    else:
        template_path = default_runtime_gene_templates_path()

    _cleanup, recon = run_reconstruction_for_map_input(int(inp.pk))
    loaded = loaded_reconstruction_snapshot_from_result(recon)

    run_dto = create_solver_run(
        int(project_id),
        run_key=rk,
        algorithm_label="runtime_v0",
        config=dict(config or {}),
    )
    run_id = int(run_dto.id)

    try:
        result = run_solver_runtime_pipeline(
            loaded=loaded,
            gene_template_path=template_path,
            run_key=rk,
        )
        persisted = persist_optimization_replay_frames_to_solver_run(
            run_id,
            result.replay_frames,
            solver_summary=result.solver_summary,
        )
        if not persisted:
            m.SolverRun.objects.filter(pk=run_id).update(status=m.SolverRun.RunStatus.FAILED)
            return SolverRuntimeEntryResult(
                ok=False,
                solver_run_id=run_id,
                optimization_replay=optimization_replay_payload_for_project(int(project_id)),
                solver_summary={},
                validation_passed=False,
                error_code=SolverRuntimeEntryErrorCode.PERSIST_REJECTED,
            )

        validation_passed = bool(result.solver_summary.get("validation_passed"))
        status = (
            m.SolverRun.RunStatus.COMPLETED if validation_passed else m.SolverRun.RunStatus.FAILED
        )
        m.SolverRun.objects.filter(pk=run_id).update(status=status)

        return SolverRuntimeEntryResult(
            ok=True,
            solver_run_id=run_id,
            optimization_replay=optimization_replay_payload_for_project(int(project_id)),
            solver_summary=dict(result.solver_summary),
            validation_passed=validation_passed,
        )
    except Exception:
        m.SolverRun.objects.filter(pk=run_id).update(status=m.SolverRun.RunStatus.FAILED)
        raise


def entry_result_to_json_dict(result: SolverRuntimeEntryResult) -> dict[str, Any]:
    """JSON-serializable body for Lab POST responses."""

    body: dict[str, Any] = {
        "ok": result.ok,
        "solver_run_id": result.solver_run_id,
        "optimization_replay": result.optimization_replay,
        "solver_summary": result.solver_summary,
        "validation_passed": result.validation_passed,
    }
    if result.error_code is not None:
        body["error_code"] = result.error_code.value
    return body


__all__ = [
    "SolverRuntimeEntryErrorCode",
    "SolverRuntimeEntryResult",
    "default_runtime_gene_templates_path",
    "entry_result_to_json_dict",
    "run_solver_runtime_for_project",
]
