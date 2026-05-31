"""Subprocess-only solver runtime entry for Django artifact/viewer orchestration."""

from __future__ import annotations

import sys
import uuid
from typing import Any, cast

from django.conf import settings

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.artifact_ingest import (
    ArtifactIngestError,
    ingest_artifact_for_project,
)
from django_apps.asteroid_lab.services.lab_replay_lazy_handle import (
    build_lab_replay_lazy_handle,
    build_lab_replay_lazy_handle_from_summary,
    lab_replay_payload_mode,
)
from django_apps.asteroid_lab.services.lab_replay_persisted_cache import (
    is_cache_summary_valid,
    load_composed_frames_for_run_id,
    load_manifest_summary_for_run_id,
)
from django_apps.asteroid_lab.services.solver_run_lab_summary import (
    lab_run_summary_from_orm,
    validation_passed_from_solver_summary,
)
from django_apps.asteroid_lab.services.solver_runtime_types import (
    SolverRuntimeEntryErrorCode,
    SolverRuntimeEntryResult,
    empty_milestone_track_metrics,
)
from django_apps.asteroid_lab.services.solver_subprocess_runner import (
    SolverSubprocessError,
    SolverSubprocessRequest,
    default_artifact_root,
    run_solver_subprocess,
)


def _empty_replay_track_metrics(*, reason: str | None = None) -> dict[str, Any]:
    return {
        "frame_count": 0,
        "replay_truncated": False,
        "truncation_reason": None,
        "dropped_frame_count": None,
        "diagnostic_reason": reason,
    }


def _latest_map_input(project_id: int) -> m.AsteroidMapInput | None:
    return (
        m.AsteroidMapInput.objects.filter(project_id=int(project_id))
        .order_by("-created_at", "-id")
        .first()
    )


def _run_subprocess_runtime_for_project(
    project_id: int,
    *,
    inp: m.AsteroidMapInput,
    run_key: str | None,
    replace_existing_run: bool,
    config: dict[str, Any] | None,
    game_data_snapshot: Any | None,
) -> SolverRuntimeEntryResult:
    resolved_run_key = (run_key or "").strip() or f"asteroid-{project_id}-{uuid.uuid4().hex}"
    artifact_root = default_artifact_root()
    runtime_config = config or {}
    verbose = bool(
        runtime_config.get("cli_verbose")
        or getattr(settings, "ASTEROID_LAB_CLI_VERBOSE", False)
        or getattr(settings, "DEBUG", False)
    )
    tee_to_parent_stderr = bool(
        getattr(settings, "ASTEROID_LAB_CLI_SUBPROCESS_TEE", True) and sys.stderr.isatty()
    )
    try:
        if not isinstance(game_data_snapshot, dict):
            raise SolverSubprocessError("game_data_snapshot payload is required")
        run_result = run_solver_subprocess(
            SolverSubprocessRequest(
                run_key=resolved_run_key,
                copy_code=str(inp.copy_code or ""),
                game_data_snapshot=dict(game_data_snapshot),
                artifact_root=artifact_root,
                allowed_root=artifact_root,
                timeout_seconds=float(
                    getattr(settings, "ASTEROID_LAB_SUBPROCESS_TIMEOUT_SECONDS", 30.0)
                ),
                replace_existing=replace_existing_run,
                verbose=verbose,
            ),
            tee_to_parent_stderr=tee_to_parent_stderr,
        )
        ingest_result = ingest_artifact_for_project(
            project_id=int(project_id),
            artifact_dir=run_result.artifact_dir,
            replace_existing_run=replace_existing_run,
        )
    except (ArtifactIngestError, SolverSubprocessError) as exc:
        return SolverRuntimeEntryResult(
            ok=False,
            solver_run_id=None,
            lab_replay_frames_json=[],
            replay_track_metrics=_empty_replay_track_metrics(reason="subprocess_failed"),
            solver_summary={},
            validation_passed=False,
            error_code=SolverRuntimeEntryErrorCode.SOLVER_SUBPROCESS_FAILED,
            message=str(exc),
        )

    solver_summary = dict(ingest_result.solver_summary)
    ok = ingest_result.solver_run.status == m.SolverRun.RunStatus.COMPLETED
    return SolverRuntimeEntryResult(
        ok=ok,
        solver_run_id=int(ingest_result.solver_run.pk),
        lab_replay_frames_json=[],
        replay_track_metrics=_empty_replay_track_metrics(reason=None),
        solver_summary=solver_summary,
        validation_passed=validation_passed_from_solver_summary(solver_summary),
        error_code=None if ok else SolverRuntimeEntryErrorCode.SOLVER_SUBPROCESS_FAILED,
        message=None if ok else "Solver subprocess artifact ingested as failed.",
    )


def run_solver_runtime_for_project(
    project_id: int,
    *,
    run_key: str | None = None,
    replace_existing_run: bool = False,
    config: dict[str, Any] | None = None,
    generator_version: str = "exhaustive_sample_gene_v1",
    game_data_snapshot: Any | None = None,
    game_data_provenance: Any | None = None,
    catalog_slice: Any | None = None,
) -> SolverRuntimeEntryResult:
    """Run the solver through the pure CLI subprocess path only."""

    del generator_version, catalog_slice, game_data_provenance

    if not m.AsteroidProject.objects.filter(pk=int(project_id)).exists():
        return SolverRuntimeEntryResult(
            ok=False,
            solver_run_id=None,
            lab_replay_frames_json=[],
            replay_track_metrics=_empty_replay_track_metrics(reason="project_not_found"),
            solver_summary={},
            validation_passed=False,
            error_code=SolverRuntimeEntryErrorCode.PROJECT_NOT_FOUND,
        )

    inp = _latest_map_input(int(project_id))
    if inp is None:
        return SolverRuntimeEntryResult(
            ok=False,
            solver_run_id=None,
            lab_replay_frames_json=[],
            replay_track_metrics=_empty_replay_track_metrics(reason="no_map_input"),
            solver_summary={},
            validation_passed=False,
            error_code=SolverRuntimeEntryErrorCode.NO_MAP_INPUT,
        )

    return _run_subprocess_runtime_for_project(
        int(project_id),
        inp=inp,
        run_key=run_key,
        replace_existing_run=replace_existing_run,
        config=config,
        game_data_snapshot=game_data_snapshot,
    )


def _normalize_milestone_track_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    if metrics.get("frame_count") is not None:
        return dict(metrics)
    return cast(dict[str, Any], empty_milestone_track_metrics())


def entry_result_to_json_dict(
    result: SolverRuntimeEntryResult,
    *,
    project_slug: str | None = None,
) -> dict[str, Any]:
    frames = list(result.lab_replay_frames_json)
    milestone_frames = list(result.lab_optimization_milestone_frames_json)
    mode = lab_replay_payload_mode()
    slug = str(project_slug or "")
    run_id = result.solver_run_id
    if mode == "inline" and run_id is not None and not frames:
        loaded_frames = load_composed_frames_for_run_id(int(run_id))
        if loaded_frames is not None:
            frames = loaded_frames
    manifest_summary: dict[str, Any] | None = None
    if mode == "lazy" and run_id is not None:
        manifest_summary = load_manifest_summary_for_run_id(int(run_id))

    if mode == "lazy" and is_cache_summary_valid(manifest_summary):
        assert manifest_summary is not None
        handle = build_lab_replay_lazy_handle_from_summary(
            project_slug=slug,
            solver_run_id=run_id,
            manifest_summary=manifest_summary,
        )
        replay_track_metrics = dict(manifest_summary.get("replay_track_metrics") or {})
        lab_replay_frame_count = int(handle.frame_count)
    else:
        handle = build_lab_replay_lazy_handle(
            mode=mode,
            frames=frames,
            project_slug=slug,
            solver_run_id=run_id,
        )
        replay_track_metrics = dict(result.replay_track_metrics)
        lab_replay_frame_count = len(frames) if mode == "inline" else int(handle.frame_count)

    body: dict[str, Any] = {
        "ok": result.ok,
        "solver_run_id": run_id,
        "lab_replay_frame_count": lab_replay_frame_count,
        "replay_track_metrics": replay_track_metrics,
        "lab_optimization_milestone_frame_count": len(milestone_frames),
        "lab_optimization_milestone_frames_json": milestone_frames,
        "lab_optimization_milestone_track_metrics": _normalize_milestone_track_metrics(
            result.lab_optimization_milestone_track_metrics
        ),
        "solver_summary": dict(result.solver_summary),
        "validation_passed": result.validation_passed,
        "validation_issue_codes": list(result.solver_summary.get("issue_codes") or []),
        "validation_issue_details": list(result.solver_summary.get("issue_details") or []),
        "gene_template_source": dict(result.gene_template_source),
    }
    if mode == "lazy":
        body["lab_replay"] = {
            "mode": handle.mode,
            "frame_count": handle.frame_count,
            "preview_frame_index": handle.preview_frame_index,
            "preview_frame": (
                dict(handle.preview_frame) if handle.preview_frame is not None else None
            ),
            "fetch_url": handle.fetch_url,
            "replay_payload_version": handle.replay_payload_version,
        }
        body["metrics"] = {
            "post_payload_slimmed": True,
            "lab_replay_inline_omitted": True,
            "lab_replay_frame_count": handle.frame_count,
        }
    else:
        body["lab_replay_frames_json"] = frames
    if result.error_code is not None:
        body["error_code"] = result.error_code.value
    if result.message is not None:
        body["message"] = result.message
    if result.solver_run_id is not None:
        run = m.SolverRun.objects.filter(pk=int(result.solver_run_id)).first()
        if run is not None:
            body["run_summary"] = lab_run_summary_from_orm(run)
    return body


__all__ = [
    "SolverRuntimeEntryErrorCode",
    "SolverRuntimeEntryResult",
    "entry_result_to_json_dict",
    "run_solver_runtime_for_project",
]
