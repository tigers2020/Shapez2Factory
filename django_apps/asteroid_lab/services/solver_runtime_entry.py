"""Solver runtime entry — reconstruction + optional RTTP optimization (v0.1)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from django.conf import settings
from django.db import transaction

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.catalog_transport_policy import (
    CatalogTransportUnresolvedError,
)
from django_apps.asteroid_lab.adapters.decode_adapter import AsteroidLabCopyDecodeError
from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    BuildingCatalogSlice,
    catalog_slice_from_snapshot,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice_hash import (
    catalog_slice_hash,
)
from django_apps.asteroid_lab.contracts.deferred_retry_shadow import DeferredRetryShadowConfig
from django_apps.asteroid_lab.contracts.game_data_snapshot import AsteroidGameDataSnapshot
from django_apps.asteroid_lab.contracts.game_data_snapshot_provenance import (
    GameDataSnapshotProvenance,
    ProvenanceParseError,
    ProvenanceParseErrorCode,
    parse_provenance_config,
    provenance_to_config_dict,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    RttpPipelineConfig,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.pipeline import PipelineResult, run_rttp_pipeline
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_reconstruction,
)
from django_apps.asteroid_lab.optimization.replay_sink import (
    DbRttpReplaySink,
    NullRttpReplaySink,
)
from django_apps.asteroid_lab.optimization.replay_track_keys import rttp_optimization_track_key
from django_apps.asteroid_lab.optimization.rttp_solver_summary import (
    RTTP_ALGORITHM_LABEL,
    build_rttp_solver_summary,
    catalog_slice_step_from_slice,
    reconstruction_step_from_result,
)
from django_apps.asteroid_lab.optimization.validation.catalog_layout_validation import (
    catalog_error_issue_codes_from_algorithm_steps,
)
from django_apps.asteroid_lab.services.committed_throughput_summary import (
    build_actual_committed_output_per_min_from_factors,
)
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
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import (
    build_reconstruction_capacity_envelope,
    build_reconstruction_observability,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_PROVENANCE_KEY,
    SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY,
    SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY,
    SOLVER_RUN_CONFIG_RTTP_MAX_MACRO_CANDIDATES_KEY,
    SOLVER_RUN_CONFIG_RTTP_RECORD_REPLAY_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
    SOLVER_RUN_CONFIG_THROUGHPUT_TARGET_PERCENT_KEY,
)
from django_apps.asteroid_lab.services.solver_run_lab_summary import (
    lab_run_summary_from_solver_summary,
)
from django_apps.asteroid_lab.services.throughput_target import (
    build_throughput_budget_summary,
    parse_throughput_target_percent,
)
from django_apps.asteroid_lab.snapshots.coord_proof_policy import (
    lab_solver_optimization_coord_frame,
)

SOLVER_NOT_AVAILABLE_MESSAGE = (
    "Solver runtime entry is not wired to RTTP yet; reconstruction is still available."
)


def _actual_committed_output_per_min_from_pipeline(
    *,
    pipeline_result: PipelineResult,
    transport_kind: TransportKind,
) -> str:
    return build_actual_committed_output_per_min_from_factors(
        throughput_factors=pipeline_result.committed_throughput_factors,
        transport_kind=transport_kind,
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


def _require_bool(value: object, *, field: str) -> bool:
    if isinstance(value, bool):
        return value
    msg = f"deferred_retry_shadow.{field} must be a boolean"
    raise ValueError(msg)


def _deferred_retry_shadow_config_from_run_config(
    config: dict[str, Any],
) -> DeferredRetryShadowConfig:
    """Map ``config_json`` shadow policy (PR-2); never reads solver_summary."""

    raw = config.get(SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY)
    if raw is None:
        return DeferredRetryShadowConfig()
    if not isinstance(raw, dict):
        msg = "deferred_retry_shadow must be an object"
        raise ValueError(msg)
    observe_only = _require_bool(raw.get("observe_only", True), field="observe_only")
    enabled = _require_bool(raw.get("enabled", True), field="enabled")
    max_rounds_raw = raw.get("max_retry_rounds", 1)
    if not isinstance(max_rounds_raw, int):
        msg = "deferred_retry_shadow.max_retry_rounds must be an integer"
        raise ValueError(msg)
    max_candidates_raw = raw.get("max_candidates")
    if max_candidates_raw is None:
        max_candidates: int | None = None
    elif isinstance(max_candidates_raw, int):
        max_candidates = max_candidates_raw
    else:
        msg = "deferred_retry_shadow.max_candidates must be an integer or null"
        raise ValueError(msg)
    expansions_raw = raw.get("route_probe_max_expansions", 500)
    if not isinstance(expansions_raw, int):
        msg = "deferred_retry_shadow.route_probe_max_expansions must be an integer"
        raise ValueError(msg)
    return DeferredRetryShadowConfig(
        enabled=enabled,
        observe_only=observe_only,
        max_retry_rounds=max_rounds_raw,
        max_candidates=max_candidates,
        route_probe_max_expansions=expansions_raw,
    )


def _rttp_pipeline_config_from_run_config(config: dict[str, Any]) -> RttpPipelineConfig:
    """Map ``SolverRun.config_json`` RTTP keys to ``RttpPipelineConfig`` (PR-I)."""

    macro_only = bool(config.get(SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY, False))
    max_raw = config.get(SOLVER_RUN_CONFIG_RTTP_MAX_MACRO_CANDIDATES_KEY, 64)
    max_macro = int(max_raw) if max_raw is not None else 64
    shadow = _deferred_retry_shadow_config_from_run_config(config)
    return RttpPipelineConfig(
        macro_only_mode=macro_only,
        max_macro_candidates=max_macro,
        deferred_retry_shadow=shadow,
    )


def _validate_catalog_slice_for_run(
    *,
    snapshot: AsteroidGameDataSnapshot,
    provenance: GameDataSnapshotProvenance,
    catalog_slice: BuildingCatalogSlice,
) -> None:
    expected_hash = catalog_slice_hash(catalog_slice)
    if provenance.catalog_slice_hash != expected_hash:
        msg = "game_data provenance catalog_slice_hash does not match catalog slice"
        raise ValueError(msg)
    extracted = catalog_slice_from_snapshot(snapshot)
    if catalog_slice_hash(extracted) != expected_hash:
        msg = "catalog slice extract hash does not match expected catalog_slice_hash"
        raise ValueError(msg)


def _prepare_rttp_run_config_with_provenance(
    run_config: dict[str, Any],
    *,
    snapshot: AsteroidGameDataSnapshot,
    provenance: GameDataSnapshotProvenance,
    catalog_slice: BuildingCatalogSlice,
) -> dict[str, Any]:
    if provenance.content_hash != snapshot.meta.content_hash:
        msg = "game_data provenance content_hash does not match snapshot.meta.content_hash"
        raise ValueError(msg)
    _validate_catalog_slice_for_run(
        snapshot=snapshot,
        provenance=provenance,
        catalog_slice=catalog_slice,
    )
    out = dict(run_config)
    wire = provenance_to_config_dict(provenance)
    parse_provenance_config(wire)
    out[SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_PROVENANCE_KEY] = wire
    return out


def _readback_solver_run_provenance(
    run_id: int,
    *,
    expected: GameDataSnapshotProvenance,
) -> None:
    run = m.SolverRun.objects.get(pk=int(run_id))
    config = dict(run.config_json or {})
    raw = config.get(SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_PROVENANCE_KEY)
    if raw is None:
        msg = "SolverRun.config_json missing game_data_snapshot_provenance after persist"
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.MISSING_FIELD,
            msg,
        )
    parsed = parse_provenance_config(raw)
    if parsed != expected:
        msg = "SolverRun provenance readback does not match expected build"
        raise ValueError(msg)


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


@transaction.atomic  # type: ignore[untyped-decorator]
def _run_rttp_solver_for_map_input(
    project_id: int,
    inp: m.AsteroidMapInput,
    *,
    run_key: str | None,
    replace_existing_run: bool,
    config: dict[str, Any] | None,
    game_data_snapshot: AsteroidGameDataSnapshot | None,
    game_data_provenance: GameDataSnapshotProvenance | None,
    catalog_slice: BuildingCatalogSlice | None,
) -> SolverRuntimeEntryResult:
    decode_err = _ensure_map_input_decoded(inp, int(project_id))
    if decode_err is not None:
        return decode_err

    if game_data_snapshot is None or game_data_provenance is None:
        return _failure_result(
            int(project_id),
            error_code=SolverRuntimeEntryErrorCode.PROVENANCE_INCOMPLETE,
            message="RTTP run requires game_data snapshot and provenance.",
        )
    if catalog_slice is None:
        return _failure_result(
            int(project_id),
            error_code=SolverRuntimeEntryErrorCode.CATALOG_SLICE_REQUIRED,
            message="RTTP run requires BuildingCatalogSlice.",
        )

    rk = (run_key or f"rttp-{uuid.uuid4().hex[:12]}").strip()
    run_config = dict(config or {})
    run_config["rttp_enabled"] = True
    try:
        run_config = _prepare_rttp_run_config_with_provenance(
            run_config,
            snapshot=game_data_snapshot,
            provenance=game_data_provenance,
            catalog_slice=catalog_slice,
        )
    except (ProvenanceParseError, ValueError) as exc:
        msg = str(exc)
        if "catalog_slice_hash" in msg:
            return _failure_result(
                int(project_id),
                error_code=SolverRuntimeEntryErrorCode.CATALOG_SLICE_HASH_MISMATCH,
                message=msg,
            )
        return _failure_result(
            int(project_id),
            error_code=SolverRuntimeEntryErrorCode.PROVENANCE_INCOMPLETE,
            message=msg,
        )

    cleanup, recon = run_reconstruction_for_map_input(
        int(inp.pk),
        boundary_run_id=rk,
    )
    try:
        opt_inp = optimization_input_from_reconstruction(
            recon,
            coord_frame=lab_solver_optimization_coord_frame(run_config),
            catalog_slice=catalog_slice,
        )
    except CatalogTransportUnresolvedError as exc:
        return _failure_result(
            int(project_id),
            error_code=SolverRuntimeEntryErrorCode.CATALOG_TRANSPORT_UNRESOLVED,
            message=str(exc),
        )

    try:
        throughput_percent = parse_throughput_target_percent(run_config)
    except ValueError as exc:
        return _failure_result(
            int(project_id),
            error_code=SolverRuntimeEntryErrorCode.INVALID_THROUGHPUT_TARGET_PERCENT,
            message=str(exc),
        )
    run_config[SOLVER_RUN_CONFIG_THROUGHPUT_TARGET_PERCENT_KEY] = throughput_percent

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
    try:
        _readback_solver_run_provenance(run_id, expected=game_data_provenance)
    except (ProvenanceParseError, ValueError) as exc:
        transaction.set_rollback(True)
        return _failure_result(
            int(project_id),
            error_code=SolverRuntimeEntryErrorCode.PROVENANCE_INCOMPLETE,
            message=str(exc),
        )

    replay_sink: DbRttpReplaySink | NullRttpReplaySink = NullRttpReplaySink()
    if _rttp_record_replay_enabled(run_config):
        rttp_track = ensure_default_replay_track(
            int(project_id),
            run_id,
            track_key=rttp_optimization_track_key(rk),
            title="RTTP optimization replay",
        )
        replay_sink = DbRttpReplaySink(int(rttp_track.track_id))
    pipeline_config = _rttp_pipeline_config_from_run_config(run_config)
    pipeline_result = run_rttp_pipeline(
        opt_inp,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        replay_sink=replay_sink,
        pipeline_config=pipeline_config,
    )

    persist_reconstructed_asteroid_map(
        map_input_id=int(inp.pk),
        run_key=rk,
        recon=recon,
        cleanup=cleanup,
        solver_run_id=run_id,
    )

    committed = pipeline_result.commit_result.committed_ids
    catalog_error_issue_codes = catalog_error_issue_codes_from_algorithm_steps(
        pipeline_result.algorithm_steps
    )
    capacity_env = build_reconstruction_capacity_envelope(recon=recon)
    actual_str = _actual_committed_output_per_min_from_pipeline(
        pipeline_result=pipeline_result,
        transport_kind=opt_inp.transport_kind,
    )
    budget_fields = None
    if actual_str is not None:
        budget_fields = build_throughput_budget_summary(
            reconstruction_capacity=capacity_env,
            throughput_target_percent=throughput_percent,
            actual_committed_output_per_min=actual_str,
        )
    summary = build_rttp_solver_summary(
        pipeline_ok=pipeline_result.validation_passed,
        committed_count=len(committed),
        normal_count=pipeline_result.normal_count,
        commit_order=pipeline_result.genome.commit_order,
        algorithm_steps=pipeline_result.algorithm_steps,
        macro_only_mode=pipeline_config.macro_only_mode,
        reconstruction_step=reconstruction_step_from_result(recon),
        catalog_slice_step=catalog_slice_step_from_slice(catalog_slice),
        catalog_error_issue_codes=catalog_error_issue_codes,
        reconstruction_capacity=capacity_env,
        reconstruction_observability=build_reconstruction_observability(
            recon=recon,
            cleanup=cleanup,
        ),
        actual_committed_output_per_min=actual_str,
        throughput_budget_fields=budget_fields,
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
    game_data_provenance: GameDataSnapshotProvenance | None = None,
    catalog_slice: BuildingCatalogSlice | None = None,
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
        game_data_provenance=game_data_provenance,
        catalog_slice=catalog_slice,
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
    if result.solver_run_id is not None and result.solver_summary:
        ui_status = "completed" if result.ok else "failed"
        body["run_summary"] = lab_run_summary_from_solver_summary(
            run_id=int(result.solver_run_id),
            status=ui_status,
            solver_summary=result.solver_summary,
        )
    return body


__all__ = [
    "RTTP_ALGORITHM_LABEL",
    "SOLVER_NOT_AVAILABLE_MESSAGE",
    "SolverRuntimeEntryErrorCode",
    "SolverRuntimeEntryResult",
    "entry_result_to_json_dict",
    "run_solver_runtime_for_project",
]
