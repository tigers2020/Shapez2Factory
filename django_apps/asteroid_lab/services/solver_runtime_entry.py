"""Solver runtime entry — fail-closed stub (RTTP removed in decontamination PR-A)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.lab_replay_lazy_handle import (
    build_lab_replay_lazy_handle,
    lab_replay_payload_mode,
)
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    build_lab_replay_frames_for_project,
)

SOLVER_NOT_AVAILABLE_MESSAGE = (
    "Solver runtime has been removed; reconstruction is still available."
)


class SolverRuntimeEntryErrorCode(StrEnum):
    """Structured failure codes for solver runtime entry (no free-form strings)."""

    PROJECT_NOT_FOUND = "project_not_found"
    NO_MAP_INPUT = "no_map_input"
    DECODE_FAILED = "decode_failed"
    SOLVER_NOT_AVAILABLE = "SOLVER_NOT_AVAILABLE"
    PROVENANCE_INCOMPLETE = "provenance_incomplete"
    CATALOG_SLICE_REQUIRED = "catalog_slice_required"
    CATALOG_SLICE_HASH_MISMATCH = "catalog_slice_hash_mismatch"
    CATALOG_TRANSPORT_UNRESOLVED = "catalog_transport_unresolved"
    INVALID_THROUGHPUT_TARGET_PERCENT = "invalid_throughput_target_percent"
    INVALID_MAX_PLACEMENT_GOAL_COUNT = "invalid_max_placement_goal_count"
    RTTP_VALIDATION_FAILED = "rttp_validation_failed"


def _empty_milestone_track_metrics() -> dict[str, Any]:
    return {
        "track_key": None,
        "frame_count": 0,
        "event_types": [],
        "replay_truncated": False,
        "truncation_reason": None,
        "dropped_frame_count": None,
        "diagnostic_reason": None,
        "source_solver_run_id": None,
    }


@dataclass(frozen=True, slots=True)
class SolverRuntimeEntryResult:
    ok: bool
    solver_run_id: int | None
    lab_replay_frames_json: list[dict[str, Any]]
    replay_track_metrics: dict[str, Any]
    solver_summary: dict[str, Any]
    validation_passed: bool
    gene_template_source: dict[str, Any] = field(default_factory=dict)
    error_code: SolverRuntimeEntryErrorCode | None = None
    message: str | None = None
    lab_optimization_milestone_frames_json: list[dict[str, Any]] = field(default_factory=list)
    lab_optimization_milestone_track_metrics: dict[str, Any] = field(
        default_factory=_empty_milestone_track_metrics
    )


def _solver_not_available_result(project_id: int) -> SolverRuntimeEntryResult:
    frames, metrics = build_lab_replay_frames_for_project(int(project_id))
    return SolverRuntimeEntryResult(
        ok=False,
        solver_run_id=None,
        lab_replay_frames_json=frames,
        replay_track_metrics=metrics,
        solver_summary={},
        validation_passed=False,
        error_code=SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE,
        message=SOLVER_NOT_AVAILABLE_MESSAGE,
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
    """Always return ``SOLVER_NOT_AVAILABLE`` (``ASTEROID_LAB_RTTP_ENABLED`` ignored)."""

    del run_key, replace_existing_run, config, generator_version
    del game_data_snapshot, game_data_provenance, catalog_slice

    if not m.AsteroidProject.objects.filter(pk=int(project_id)).exists():
        frames, metrics = build_lab_replay_frames_for_project(int(project_id))
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
        frames, metrics = build_lab_replay_frames_for_project(int(project_id))
        return SolverRuntimeEntryResult(
            ok=False,
            solver_run_id=None,
            lab_replay_frames_json=frames,
            replay_track_metrics=metrics,
            solver_summary={},
            validation_passed=False,
            error_code=SolverRuntimeEntryErrorCode.NO_MAP_INPUT,
        )

    return _solver_not_available_result(int(project_id))


def _normalize_milestone_track_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    if metrics.get("frame_count") is not None:
        return dict(metrics)
    return _empty_milestone_track_metrics()


def entry_result_to_json_dict(
    result: SolverRuntimeEntryResult,
    *,
    project_slug: str | None = None,
) -> dict[str, Any]:
    frames = list(result.lab_replay_frames_json)
    milestone_frames = list(result.lab_optimization_milestone_frames_json)
    mode = lab_replay_payload_mode()
    body: dict[str, Any] = {
        "ok": result.ok,
        "solver_run_id": result.solver_run_id,
        "lab_replay_frame_count": len(frames),
        "replay_track_metrics": result.replay_track_metrics,
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
    handle = build_lab_replay_lazy_handle(
        mode=mode,
        frames=frames,
        project_slug=str(project_slug or ""),
        solver_run_id=result.solver_run_id,
    )
    if mode == "lazy":
        body["lab_replay"] = {
            "mode": handle.mode,
            "frame_count": handle.frame_count,
            "preview_frame_index": handle.preview_frame_index,
            "preview_frame": handle.preview_frame,
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
    return body


__all__ = [
    "SOLVER_NOT_AVAILABLE_MESSAGE",
    "SolverRuntimeEntryErrorCode",
    "SolverRuntimeEntryResult",
    "entry_result_to_json_dict",
    "run_solver_runtime_for_project",
]
