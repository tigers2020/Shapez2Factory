"""Solver runtime entry — reconstruction + optional RTTP optimization (v0.1)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field, replace
from decimal import Decimal
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
from django_apps.asteroid_lab.contracts.ga_evolution_shadow import GaEvolutionShadowConfig
from django_apps.asteroid_lab.contracts.game_data_snapshot import AsteroidGameDataSnapshot
from django_apps.asteroid_lab.contracts.game_data_snapshot_provenance import (
    GameDataSnapshotProvenance,
    ProvenanceParseError,
    ProvenanceParseErrorCode,
    parse_provenance_config,
    provenance_to_config_dict,
)
from django_apps.asteroid_lab.contracts.selection_mode import SelectionMode
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
    FixedOutputTransportPolicy,
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
from django_apps.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
    mineable_field_kind_by_coord,
)
from django_apps.asteroid_lab.reconstruction.field_cells import (
    asteroid_field_cell_count_for_placement,
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
from django_apps.asteroid_lab.services.lab_replay_lazy_handle import (
    build_lab_replay_lazy_handle,
    lab_replay_payload_mode,
)
from django_apps.asteroid_lab.services.lab_replay_timeline_payload import (
    build_lab_replay_frames_for_project,
)
from django_apps.asteroid_lab.services.placement_goal import (
    attribute_throughput_shortfall,
    resolve_max_placement_goal_count,
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
    SOLVER_RUN_CONFIG_MAX_PLACEMENT_GOAL_COUNT_KEY,
    SOLVER_RUN_CONFIG_RTTP_DEFERRED_RETRY_SHADOW_KEY,
    SOLVER_RUN_CONFIG_RTTP_GA_EVOLUTION_SHADOW_KEY,
    SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY,
    SOLVER_RUN_CONFIG_RTTP_MAX_MACRO_CANDIDATES_KEY,
    SOLVER_RUN_CONFIG_RTTP_RECORD_REPLAY_KEY,
    SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY,
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
    SOLVER_RUN_CONFIG_THROUGHPUT_TARGET_PERCENT_KEY,
)
from django_apps.asteroid_lab.services.solver_run_lab_summary import (
    lab_run_summary_from_solver_summary,
)
from django_apps.asteroid_lab.services.throughput_target import (
    build_throughput_budget_summary,
    compute_target_throughput_per_min,
    parse_throughput_target_percent,
    primary_reconstruction_max_per_min,
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
    INVALID_MAX_PLACEMENT_GOAL_COUNT = "invalid_max_placement_goal_count"
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


def _ga_shadow_require_bool(value: object, *, field: str) -> bool:
    if isinstance(value, bool):
        return value
    msg = f"ga_evolution_shadow.{field} must be a boolean"
    raise ValueError(msg)


def _ga_shadow_require_int(value: object, *, field: str) -> int:
    if isinstance(value, int) and not isinstance(value, bool):
        return value
    msg = f"ga_evolution_shadow.{field} must be an integer"
    raise ValueError(msg)


def _ga_shadow_require_float(value: object, *, field: str) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    msg = f"ga_evolution_shadow.{field} must be a number"
    raise ValueError(msg)


_VALID_SELECTION_MODES = frozenset(
    {
        SelectionMode.GREEDY_REGRET.value,
        SelectionMode.GREEDY_REGRET_OVERLAP_PACK.value,
        SelectionMode.EVOLUTION.value,
    }
)


def _selection_mode_from_run_config(config: dict[str, Any]) -> SelectionMode:
    """Map ``config_json.selection.mode`` (PR-GA-2); never reads solver_summary."""

    raw = config.get(SOLVER_RUN_CONFIG_RTTP_SELECTION_KEY)
    if raw is None:
        return SelectionMode.GREEDY_REGRET
    if not isinstance(raw, dict):
        msg = "selection must be an object"
        raise ValueError(msg)
    mode_raw = raw.get("mode", SelectionMode.GREEDY_REGRET.value)
    if not isinstance(mode_raw, str):
        msg = "selection.mode must be a string"
        raise ValueError(msg)
    if mode_raw not in _VALID_SELECTION_MODES:
        msg = f"selection.mode must be one of {sorted(_VALID_SELECTION_MODES)}"
        raise ValueError(msg)
    return SelectionMode(mode_raw)


def _ga_evolution_shadow_config_from_run_config(
    config: dict[str, Any],
) -> GaEvolutionShadowConfig:
    """Map ``config_json`` GA shadow policy (PR-GA-1); never reads solver_summary."""

    raw = config.get(SOLVER_RUN_CONFIG_RTTP_GA_EVOLUTION_SHADOW_KEY)
    if raw is None:
        return GaEvolutionShadowConfig()
    if not isinstance(raw, dict):
        msg = "ga_evolution_shadow must be an object"
        raise ValueError(msg)
    observe_only = _ga_shadow_require_bool(raw.get("observe_only", True), field="observe_only")
    enabled = _ga_shadow_require_bool(raw.get("enabled", False), field="enabled")
    return GaEvolutionShadowConfig(
        enabled=enabled,
        observe_only=observe_only,
        population_size=_ga_shadow_require_int(
            raw.get("population_size", 24),
            field="population_size",
        ),
        generations=_ga_shadow_require_int(raw.get("generations", 8), field="generations"),
        mutation_rate=_ga_shadow_require_float(
            raw.get("mutation_rate", 0.15),
            field="mutation_rate",
        ),
        tournament_size=_ga_shadow_require_int(
            raw.get("tournament_size", 3),
            field="tournament_size",
        ),
        elite_count=_ga_shadow_require_int(raw.get("elite_count", 2), field="elite_count"),
        random_seed=_ga_shadow_require_int(raw.get("random_seed", 0), field="random_seed"),
    )


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


def _rttp_pipeline_config_from_run_config(
    config: dict[str, Any],
    *,
    target_throughput_per_min: Decimal | None = None,
    max_placement_goal_count: int | None = None,
) -> RttpPipelineConfig:
    """Map ``SolverRun.config_json`` RTTP keys to ``RttpPipelineConfig`` (PR-I + PR-2d)."""

    macro_only = bool(config.get(SOLVER_RUN_CONFIG_RTTP_MACRO_ONLY_MODE_KEY, False))
    max_raw = config.get(SOLVER_RUN_CONFIG_RTTP_MAX_MACRO_CANDIDATES_KEY, 64)
    max_macro = int(max_raw) if max_raw is not None else 64
    shadow = _deferred_retry_shadow_config_from_run_config(config)
    ga_shadow = _ga_evolution_shadow_config_from_run_config(config)
    selection_mode = _selection_mode_from_run_config(config)
    if max_placement_goal_count is not None:
        resolved_max_goal = max_placement_goal_count
    elif SOLVER_RUN_CONFIG_MAX_PLACEMENT_GOAL_COUNT_KEY in config:
        resolved_max_goal = int(config[SOLVER_RUN_CONFIG_MAX_PLACEMENT_GOAL_COUNT_KEY])
    else:
        resolved_max_goal = 0
    return RttpPipelineConfig(
        macro_only_mode=macro_only,
        max_macro_candidates=max_macro,
        deferred_retry_shadow=shadow,
        ga_evolution_shadow=ga_shadow,
        selection_mode=selection_mode,
        target_throughput_per_min=target_throughput_per_min,
        max_placement_goal_count=resolved_max_goal,
    )


def _pipeline_config_with_field_kinds(
    config: RttpPipelineConfig,
    complete_map: ReconstructionCompleteMap,
) -> RttpPipelineConfig:
    entries = tuple(
        (int(x), int(y), kind)
        for (x, y), kind in sorted(mineable_field_kind_by_coord(complete_map).items())
    )
    if not entries:
        return config
    return replace(config, mineable_field_kind_by_coord=entries)


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
    from django_apps.asteroid_lab.reconstruction.complete_map import (
        build_reconstruction_complete_map,
    )

    opt_coord_frame = lab_solver_optimization_coord_frame(run_config)
    complete_map = build_reconstruction_complete_map(
        cleanup=cleanup,
        recon=recon,
        coord_frame=opt_coord_frame,
    )
    try:
        opt_inp = optimization_input_from_reconstruction(
            recon,
            cleanup=cleanup,
            coord_frame=opt_coord_frame,
            catalog_slice=catalog_slice,
            complete_map=complete_map,
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
    try:
        field_cell_count = asteroid_field_cell_count_for_placement(
            complete_map,
            opt_inp.transport_kind,
        )
        max_placement_goal = resolve_max_placement_goal_count(
            run_config,
            asteroid_field_cell_count=field_cell_count,
            placement_target_percent=throughput_percent,
        )
    except ValueError as exc:
        return _failure_result(
            int(project_id),
            error_code=SolverRuntimeEntryErrorCode.INVALID_MAX_PLACEMENT_GOAL_COUNT,
            message=str(exc),
        )
    run_config[SOLVER_RUN_CONFIG_THROUGHPUT_TARGET_PERCENT_KEY] = throughput_percent
    run_config[SOLVER_RUN_CONFIG_MAX_PLACEMENT_GOAL_COUNT_KEY] = max_placement_goal

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
    project_slug: str | None = (
        m.AsteroidProject.objects.filter(pk=int(project_id)).values_list("slug", flat=True).first()
    )
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
    capacity_env = build_reconstruction_capacity_envelope(complete_map=complete_map)
    target_throughput = compute_target_throughput_per_min(
        reconstruction_max=primary_reconstruction_max_per_min(capacity_env),
        percent=throughput_percent,
    )
    pipeline_config = _pipeline_config_with_field_kinds(
        replace(
            _rttp_pipeline_config_from_run_config(
                run_config,
                target_throughput_per_min=target_throughput,
                max_placement_goal_count=max_placement_goal,
            ),
            reconstruction_max_throughput_per_min=primary_reconstruction_max_per_min(capacity_env),
        ),
        complete_map,
    )
    # PR-2 OUTWARD_FROM_RIM applies to normal RTTP; macro-only stays PR-1 until PR-B alignment.
    fot_policy = (
        FixedOutputTransportPolicy.OUTSIDE_MINEABLE
        if pipeline_config.macro_only_mode
        else FixedOutputTransportPolicy.OUTWARD_FROM_RIM
    )
    pipeline_result = run_rttp_pipeline(
        opt_inp,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        replay_sink=replay_sink,
        pipeline_config=pipeline_config,
        fixed_output_transport_policy=fot_policy,
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
    throughput_goal_payload: dict[str, Any] | None = None
    shortfall_reason: str | None = None
    placement_plan = pipeline_result.placement_goal_plan
    if placement_plan is not None:
        throughput_goal_payload = placement_plan.to_summary_dict()
        throughput_goal_payload["selected_count"] = len(pipeline_result.genome.commit_order)
        throughput_goal_payload["committed_count"] = len(committed)
    if budget_fields is not None and placement_plan is not None:
        reason = attribute_throughput_shortfall(
            plan=placement_plan,
            selected_count=len(pipeline_result.genome.commit_order),
            committed_count=len(committed),
            conflict_count=len(pipeline_result.commit_result.conflicts),
            budget_satisfied=bool(budget_fields["throughput_budget_satisfied"]),
            actual=Decimal(str(budget_fields["actual_committed_output_per_min"])),
            target=Decimal(str(budget_fields["target_throughput_per_min"])),
            normal_count=pipeline_result.normal_count,
        )
        shortfall_reason = reason.value
        if throughput_goal_payload is not None:
            throughput_goal_payload["throughput_shortfall_reason"] = shortfall_reason
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
            complete_map=complete_map,
        ),
        actual_committed_output_per_min=actual_str,
        throughput_budget_fields=budget_fields,
        throughput_goal=throughput_goal_payload,
        throughput_shortfall_reason=shortfall_reason,
        project_slug=project_slug,
    )
    _persist_solver_run_outcome(
        run_id,
        solver_summary=summary,
    )

    frames, metrics = build_lab_replay_frames_for_project(
        int(project_id),
        solver_run_id=int(run_id),
    )
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
