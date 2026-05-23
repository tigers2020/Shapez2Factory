"""Solver runtime entry — reconstruction + optional RTTP optimization (v0.1)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from django.conf import settings
from django.db import transaction

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.decode_adapter import AsteroidLabCopyDecodeError
from django_apps.asteroid_lab.contracts.game_data_snapshot import AsteroidGameDataSnapshot
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.input_contracts import RttpPipelineConfig
from django_apps.asteroid_lab.optimization.pipeline import run_rttp_pipeline
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_reconstruction,
)
from django_apps.asteroid_lab.optimization.replay_sink import (
    DbRttpReplaySink,
    NullRttpReplaySink,
)
from django_apps.asteroid_lab.optimization.replay_track_keys import rttp_optimization_track_key
from django_apps.asteroid_lab.services.experiment_service import (
    create_or_replace_solver_run,
    create_solver_run,
    ensure_default_replay_track,
)
from django_apps.asteroid_lab.services.input_service import refresh_map_input_from_copy_code
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    _empty_track_metrics,
    build_lab_optimization_milestone_frames_for_project,
)
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    build_lab_replay_frames_for_project,
)
from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
    persist_reconstructed_asteroid_map,
    run_reconstruction_for_map_input,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_META_KEY,
    SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY,
    SOLVER_RUN_CONFIG_RTTP_MAX_MACRO_CANDIDATES_KEY,
    SOLVER_RUN_CONFIG_RTTP_RECORD_REPLAY_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)
from django_apps.asteroid_lab.snapshots.coord_proof_policy import (
    lab_solver_optimization_coord_frame,
)

SOLVER_NOT_AVAILABLE_MESSAGE = (
    "Solver runtime entry is not wired to RTTP yet; reconstruction is still available."
)

RTTP_ALGORITHM_LABEL = "rttp_v0.1"


class SolverRuntimeEntryErrorCode(StrEnum):
    """Structured failure codes for solver runtime entry (no free-form strings)."""

    PROJECT_NOT_FOUND = "project_not_found"
    NO_MAP_INPUT = "no_map_input"
    DECODE_FAILED = "decode_failed"
    SOLVER_NOT_AVAILABLE = "SOLVER_NOT_AVAILABLE"
    RTTP_VALIDATION_FAILED = "rttp_validation_failed"


def _default_lab_optimization_milestone_track_metrics() -> dict[str, Any]:
    return _empty_track_metrics()


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
        default_factory=_default_lab_optimization_milestone_track_metrics
    )


def _empty_replay_for_project(project_id: int) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return build_lab_replay_frames_for_project(int(project_id))


def _milestone_payload_for_project(
    project_id: int,
    *,
    run_key: str | None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    return build_lab_optimization_milestone_frames_for_project(
        int(project_id),
        run_key=run_key,
    )


def _rttp_enabled(config: dict[str, Any] | None) -> bool:
    if config is not None and "rttp_enabled" in config:
        return bool(config["rttp_enabled"])
    return bool(getattr(settings, "ASTEROID_LAB_RTTP_ENABLED", True))


def _rttp_record_replay_enabled(config: dict[str, Any]) -> bool:
    if SOLVER_RUN_CONFIG_RTTP_RECORD_REPLAY_KEY in config:
        return bool(config[SOLVER_RUN_CONFIG_RTTP_RECORD_REPLAY_KEY])
    return True


def _rttp_pipeline_config_from_run_config(config: dict[str, Any]) -> RttpPipelineConfig:
    """Map ``SolverRun.config_json`` RTTP keys to ``RttpPipelineConfig`` (PR-I)."""

    macro_only = bool(config.get(SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY, False))
    max_raw = config.get(SOLVER_RUN_CONFIG_RTTP_MAX_MACRO_CANDIDATES_KEY, 64)
    max_macro = int(max_raw) if max_raw is not None else 64
    return RttpPipelineConfig(
        macro_only_mode=macro_only,
        max_macro_candidates=max_macro,
    )


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
) -> None:
    run = m.SolverRun.objects.get(pk=int(run_id))
    config = dict(run.config_json or {})
    config[SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY] = dict(solver_summary)
    m.SolverRun.objects.filter(pk=int(run_id)).update(config_json=config)


def _solver_not_available_result(project_id: int) -> SolverRuntimeEntryResult:
    frames, metrics = _empty_replay_for_project(int(project_id))
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


def _failure_result(
    project_id: int,
    *,
    error_code: SolverRuntimeEntryErrorCode,
    message: str,
) -> SolverRuntimeEntryResult:
    frames, metrics = _empty_replay_for_project(int(project_id))
    return SolverRuntimeEntryResult(
        ok=False,
        solver_run_id=None,
        lab_replay_frames_json=frames,
        replay_track_metrics=metrics,
        solver_summary={},
        validation_passed=False,
        error_code=error_code,
        message=message,
    )


def _decoded_json_ready(inp: m.AsteroidMapInput) -> bool:
    raw = inp.decoded_json
    return isinstance(raw, dict) and isinstance(raw.get("BP"), dict)


def _ensure_map_input_decoded(
    inp: m.AsteroidMapInput,
    project_id: int,
) -> SolverRuntimeEntryResult | None:
    if _decoded_json_ready(inp):
        return None
    code = (inp.copy_code or "").strip()
    if not code:
        return _failure_result(
            int(project_id),
            error_code=SolverRuntimeEntryErrorCode.NO_MAP_INPUT,
            message="Map input has no decoded blueprint and no copy code.",
        )
    try:
        refresh_map_input_from_copy_code(int(inp.pk), code)
    except AsteroidLabCopyDecodeError as exc:
        return _failure_result(
            int(project_id),
            error_code=SolverRuntimeEntryErrorCode.DECODE_FAILED,
            message=str(exc),
        )
    return None


def _rttp_solver_summary(
    *,
    pipeline_ok: bool,
    committed_count: int,
    normal_count: int,
    commit_order: tuple[str, ...],
) -> dict[str, Any]:
    return {
        "algorithm": RTTP_ALGORITHM_LABEL,
        "validation_passed": pipeline_ok,
        "run_success": pipeline_ok,
        "capacity_satisfied": pipeline_ok,
        "placement_capacity_satisfied": pipeline_ok,
        "throughput_budget_satisfied": pipeline_ok,
        "confirmed_count": committed_count,
        "target_miner_bundle_count": len(commit_order),
        "target_placement_count": len(commit_order),
        "normal_candidate_count": normal_count,
        "commit_order": list(commit_order),
        "issue_codes": [] if pipeline_ok else ["rttp_validation_failed"],
        "issue_details": [] if pipeline_ok else [],
    }


@transaction.atomic  # type: ignore[untyped-decorator]
def _run_rttp_solver_for_map_input(
    project_id: int,
    inp: m.AsteroidMapInput,
    *,
    run_key: str | None,
    replace_existing_run: bool,
    config: dict[str, Any] | None,
    game_data_snapshot: AsteroidGameDataSnapshot | None,
) -> SolverRuntimeEntryResult:
    decode_err = _ensure_map_input_decoded(inp, int(project_id))
    if decode_err is not None:
        return decode_err

    rk = (run_key or f"rttp-{uuid.uuid4().hex[:12]}").strip()
    run_config = dict(config or {})
    run_config["rttp_enabled"] = True
    if game_data_snapshot is not None:
        run_config[SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_META_KEY] = _snapshot_meta_for_config(
            game_data_snapshot
        )

    cleanup, recon = run_reconstruction_for_map_input(
        int(inp.pk),
        boundary_run_id=rk,
    )
    opt_inp = optimization_input_from_reconstruction(
        recon,
        coord_frame=lab_solver_optimization_coord_frame(run_config),
    )

    if replace_existing_run:
        run_dto = create_or_replace_solver_run(
            int(project_id),
            run_key=rk,
            algorithm_label=RTTP_ALGORITHM_LABEL,
            config=run_config,
        )
    else:
        run_dto = create_solver_run(
            int(project_id),
            run_key=rk,
            algorithm_label=RTTP_ALGORITHM_LABEL,
            config=run_config,
        )
    run_id = int(run_dto.id)
    replay_sink: DbRttpReplaySink | NullRttpReplaySink = NullRttpReplaySink()
    if _rttp_record_replay_enabled(run_config):
        rttp_track = ensure_default_replay_track(
            int(project_id),
            run_id,
            track_key=rttp_optimization_track_key(rk),
            title="RTTP optimization replay",
        )
        replay_sink = DbRttpReplaySink(int(rttp_track.track_id))
    pipeline_result = run_rttp_pipeline(
        opt_inp,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        replay_sink=replay_sink,
        pipeline_config=_rttp_pipeline_config_from_run_config(run_config),
    )

    persist_reconstructed_asteroid_map(
        map_input_id=int(inp.pk),
        run_key=rk,
        recon=recon,
        cleanup=cleanup,
        solver_run_id=run_id,
    )

    committed = pipeline_result.commit_result.committed_ids
    summary = _rttp_solver_summary(
        pipeline_ok=pipeline_result.validation_passed,
        committed_count=len(committed),
        normal_count=pipeline_result.normal_count,
        commit_order=pipeline_result.genome.commit_order,
    )
    _persist_solver_run_outcome(
        run_id,
        solver_summary=summary,
    )

    frames, metrics = build_lab_replay_frames_for_project(int(project_id))
    milestone_frames, milestone_metrics = _milestone_payload_for_project(
        int(project_id),
        run_key=rk,
    )
    if not pipeline_result.validation_passed:
        return SolverRuntimeEntryResult(
            ok=False,
            solver_run_id=run_id,
            lab_replay_frames_json=frames,
            replay_track_metrics=metrics,
            solver_summary=summary,
            validation_passed=False,
            error_code=SolverRuntimeEntryErrorCode.RTTP_VALIDATION_FAILED,
            message="RTTP pipeline finished but final validation did not pass.",
            lab_optimization_milestone_frames_json=milestone_frames,
            lab_optimization_milestone_track_metrics=milestone_metrics,
        )

    return SolverRuntimeEntryResult(
        ok=True,
        solver_run_id=run_id,
        lab_replay_frames_json=frames,
        replay_track_metrics=metrics,
        solver_summary=summary,
        validation_passed=True,
        lab_optimization_milestone_frames_json=milestone_frames,
        lab_optimization_milestone_track_metrics=milestone_metrics,
    )


def run_solver_runtime_for_project(
    project_id: int,
    *,
    run_key: str | None = None,
    replace_existing_run: bool = False,
    config: dict[str, Any] | None = None,
    generator_version: str = "exhaustive_sample_gene_v1",
    game_data_snapshot: AsteroidGameDataSnapshot | None = None,
) -> SolverRuntimeEntryResult:
    """Run RTTP when enabled; otherwise return ``SOLVER_NOT_AVAILABLE``."""

    del generator_version

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

    if not _rttp_enabled(config):
        return _solver_not_available_result(int(project_id))

    return _run_rttp_solver_for_map_input(
        int(project_id),
        inp,
        run_key=run_key,
        replace_existing_run=replace_existing_run,
        config=config,
        game_data_snapshot=game_data_snapshot,
    )


def _normalize_milestone_track_metrics(metrics: dict[str, Any]) -> dict[str, Any]:
    """Ensure Run Solver JSON matches SSR neutral milestone metrics shape."""
    if metrics.get("frame_count") is not None:
        return dict(metrics)
    return _empty_track_metrics()


def entry_result_to_json_dict(result: SolverRuntimeEntryResult) -> dict[str, Any]:
    frames = list(result.lab_replay_frames_json)
    milestone_frames = list(result.lab_optimization_milestone_frames_json)
    body: dict[str, Any] = {
        "ok": result.ok,
        "solver_run_id": result.solver_run_id,
        "lab_replay_frame_count": len(frames),
        "lab_replay_frames_json": frames,
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
    if result.error_code is not None:
        body["error_code"] = result.error_code.value
    if result.message is not None:
        body["message"] = result.message
    return body


__all__ = [
    "RTTP_ALGORITHM_LABEL",
    "SOLVER_NOT_AVAILABLE_MESSAGE",
    "SolverRuntimeEntryErrorCode",
    "SolverRuntimeEntryResult",
    "entry_result_to_json_dict",
    "run_solver_runtime_for_project",
]
