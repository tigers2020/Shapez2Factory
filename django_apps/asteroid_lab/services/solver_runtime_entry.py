"""HTTP / Run Solver entry: reconstruction → runtime pipeline → persist (PR8)."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.optimization.game_data_contracts import AsteroidGameDataSnapshot
from django_apps.asteroid_lab.optimization.loaded_snapshot import (
    loaded_reconstruction_snapshot_from_run,
)
from django_apps.asteroid_lab.replay.solver_runtime_replay_recorder import (
    SolverRuntimeReplayRecorder,
)
from django_apps.asteroid_lab.replay.timeline_serialization import (
    replay_timeline_frame_to_json_dict,
)
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
from django_apps.asteroid_lab.services.solver_generation_config import (
    generation_config_from_run_config,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_META_KEY,
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


def _snapshot_meta_for_config(snapshot: AsteroidGameDataSnapshot) -> dict[str, str]:
    meta = snapshot.meta
    return {
        "schema_version": meta.schema_version,
        "data_revision": meta.data_revision,
        "content_hash": meta.content_hash,
    }


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
    game_data_snapshot: AsteroidGameDataSnapshot | None = None,
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

    cleanup, recon = run_reconstruction_for_map_input(int(inp.pk))
    loaded = loaded_reconstruction_snapshot_from_run(cleanup, recon)

    run_config = dict(config or {})
    run_config[SOLVER_RUN_CONFIG_GENE_TEMPLATE_SOURCE_KEY] = gene_source_dict
    if game_data_snapshot is not None:
        run_config[SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_META_KEY] = _snapshot_meta_for_config(
            game_data_snapshot
        )

    run_dto = create_solver_run(
        int(project_id),
        run_key=rk,
        algorithm_label="runtime_v0",
        config=run_config,
    )
    run_id = int(run_dto.id)

    server_xy_params = loaded.server_xy_params
    gene_templates_by_id = {g.gene_id: g for g in gene_templates}
    recorder: SolverRuntimeReplayRecorder | None = (
        SolverRuntimeReplayRecorder(
            loaded,
            server_xy_params,
            gene_templates_by_id=gene_templates_by_id,
        )
        if server_xy_params is not None
        else None
    )

    generation_config = generation_config_from_run_config(run_config)

    try:
        result = run_solver_runtime_pipeline(
            loaded=loaded,
            gene_templates=gene_templates,
            run_key=rk,
            generation_config=generation_config,
            run_config=run_config,
            recorder=recorder,
        )
        runtime_replay_frames_json: list[dict[str, Any]] | None = None
        replay_build_ms = 0.0
        json_serialize_ms = 0.0
        if recorder is not None:
            replay_start = time.perf_counter()
            frames = recorder.build_frames()
            replay_build_ms = (time.perf_counter() - replay_start) * 1000.0
            if frames:
                ser_start = time.perf_counter()
                runtime_replay_frames_json = [replay_timeline_frame_to_json_dict(f) for f in frames]
                json_serialize_ms = (time.perf_counter() - ser_start) * 1000.0
        timing_dict = dict(result.solver_summary.get("timing") or {})
        timing_dict["replay_build_ms"] = round(replay_build_ms, 3)
        timing_dict["json_serialize_ms"] = round(json_serialize_ms, 3)
        result_summary = dict(result.solver_summary)
        result_summary["timing"] = timing_dict
        _persist_solver_run_outcome(
            run_id,
            solver_summary=result_summary,
            server_xy_params=loaded.server_xy_params,
            runtime_replay_frames_json=runtime_replay_frames_json,
        )

        validation_passed = bool(result.solver_summary.get("validation_passed"))
        capacity_satisfied = bool(result.solver_summary.get("capacity_satisfied"))
        run_success = validation_passed and capacity_satisfied
        if run_success:
            status = m.SolverRun.RunStatus.COMPLETED
        elif validation_passed:
            status = m.SolverRun.RunStatus.PARTIAL
        else:
            status = m.SolverRun.RunStatus.FAILED
        m.SolverRun.objects.filter(pk=run_id).update(status=status)

        frames, metrics = build_lab_replay_frames_for_project(int(project_id))
        return SolverRuntimeEntryResult(
            ok=True,
            solver_run_id=run_id,
            lab_replay_frames_json=frames,
            replay_track_metrics=metrics,
            solver_summary=result_summary,
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
        run_success = bool(summary.get("run_success"))
        validation_passed = bool(summary.get("validation_passed"))
        if run_success:
            ui_status = "completed"
        elif validation_passed:
            ui_status = "partial"
        else:
            ui_status = "failed"
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
