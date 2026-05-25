"""RTTP end-to-end pipeline wiring skeleton through validation (PR-5 + v1 macro)."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from django_apps.asteroid_lab.adapters.catalog_placement_audit import (
    audit_catalog_placements,
    catalog_placement_audit_metrics,
)
from django_apps.asteroid_lab.adapters.catalog_placement_validation import (
    validate_catalog_placements,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice_hash import catalog_slice_hash
from django_apps.asteroid_lab.contracts.catalog_placement import (
    CatalogPlacementIssueCode,
    CatalogValidationMode,
)
from django_apps.asteroid_lab.contracts.catalog_validation import CatalogValidationResult
from django_apps.asteroid_lab.contracts.deferred_retry_execute import (
    DeferredRetryExecuteResult,
    deferred_retry_execute_metrics,
)
from django_apps.asteroid_lab.contracts.deferred_retry_shadow import DeferredRetryShadowConfig
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    BundleCandidate,
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.commit.deferred_retry_execute import (
    run_bounded_deferred_retry,
)
from django_apps.asteroid_lab.optimization.commit.deferred_retry_shadow import (
    build_deferred_retry_shadow_summary,
    deferred_retry_shadow_metrics,
)
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitResult,
    incremental_commit,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.commit.incremental_macro_commit import (
    MacroCommitResult,
    incremental_commit_macro,
)
from django_apps.asteroid_lab.optimization.commit.local_lns import run_local_lns
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpPipelineConfig,
    RttpSkeletonConfig,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.macros.macro_compiler import (
    MacroCompileConfig,
    compile_macros,
)
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    mismatched_existing_transport_metrics,
    partition_existing_transport,
)
from django_apps.asteroid_lab.optimization.replay_sink import (
    RttpReplaySink,
    resolve_replay_sink,
)
from django_apps.asteroid_lab.optimization.rttp_replay_diagnostics import (
    build_candidates_replay_payload,
    build_commit_replay_payload,
    build_macro_commit_replay_payload,
    build_macro_selection_replay_payload,
    build_pipeline_start_replay_payload,
    build_selection_replay_payload,
    field_kind_map_from_entries,
)
from django_apps.asteroid_lab.optimization.rttp_solver_summary import (
    RttpAlgorithmStepId,
    algorithm_step_summary_to_json,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import (
    PlacementGenome,
    select_genome,
)
from django_apps.asteroid_lab.optimization.selection.macro_equivalence import dedupe_macros
from django_apps.asteroid_lab.optimization.selection.macro_greedy_regret import (
    select_macro_genome,
)
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from django_apps.asteroid_lab.optimization.validation.catalog_layout_validation import (
    validate_pipeline_layout,
)
from django_apps.asteroid_lab.optimization.validation.final_validation import validate_macro_layout
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.committed_throughput_summary import (
    collect_committed_throughput_factors,
)
from django_apps.asteroid_lab.services.dto import SnapshotEventDTO
from django_apps.asteroid_lab.services.placement_goal import (
    PlacementGoalPlan,
    build_placement_goal_plan,
)


@dataclass(frozen=True, slots=True)
class PipelineResult:
    genome: PlacementGenome
    commit_result: CommitResult
    normal_count: int
    validation_passed: bool
    algorithm_steps: tuple[dict[str, Any], ...] = ()
    committed_throughput_factors: tuple[int, ...] = ()
    placement_goal_plan: PlacementGoalPlan | None = None


def _selection_goal_for_pipeline(
    *,
    config: RttpPipelineConfig,
    skeleton_capacity_goals: int,
    normal_candidates: Sequence[BundleCandidate],
    transport_kind: TransportKind,
) -> tuple[int, PlacementGoalPlan | None]:
    if config.target_throughput_per_min is None:
        return max(0, skeleton_capacity_goals), None
    plan = build_placement_goal_plan(
        normal_candidates=normal_candidates,
        transport_kind=transport_kind,
        target_throughput_per_min=config.target_throughput_per_min,
        skeleton_capacity_goals=skeleton_capacity_goals,
        configured_max_placement_goal=config.max_placement_goal_count,
    )
    return plan.placement_goal_count, plan


def _record_replay(
    sink: RttpReplaySink,
    *,
    event_key: str,
    event_type: str,
    phase: str,
    title: str,
    description: str = "",
    metrics_json: dict[str, Any] | None = None,
    cell_overlay_json: dict[str, Any] | None = None,
) -> None:
    sink.record(
        SnapshotEventDTO(
            event_key=event_key,
            phase=phase,
            phase_step="",
            event_type=event_type,
            title=title,
            description=description,
            metrics_json=dict(metrics_json or {}),
            cell_overlay_json=dict(cell_overlay_json or {}),
            full_map=[],
            is_decision_point=True,
        )
    )


def _record_pipeline_step(
    sink: RttpReplaySink,
    steps: list[dict[str, Any]],
    *,
    step_id: RttpAlgorithmStepId,
    event_key: str,
    event_type: str,
    phase: str,
    title: str,
    description: str = "",
    metrics_json: dict[str, Any] | None = None,
    cell_overlay_json: dict[str, Any] | None = None,
    passed: bool | None = None,
) -> None:
    step_row = algorithm_step_summary_to_json(
        {
            "step_id": step_id.value,
            "phase": phase,
            "event_type": event_type,
            "title": title,
            "summary": description,
            "metrics": dict(metrics_json or {}),
            "passed": passed,
        }
    )
    steps.append(step_row)
    _record_replay(
        sink,
        event_key=event_key,
        event_type=event_type,
        phase=phase,
        title=title,
        description=description,
        metrics_json=metrics_json,
        cell_overlay_json=cell_overlay_json,
    )


def _append_deferred_retry_shadow_step(
    steps: list[dict[str, Any]],
    *,
    shadow_config: DeferredRetryShadowConfig,
    primary_commit_result: CommitResult,
    commit_order: Sequence[str],
    candidates_by_id: dict[str, BundleCandidate],
    inp: OptimizationInput,
) -> None:
    """Record primary-pass deferred retry shadow (observe-only; before LNS)."""

    summary = build_deferred_retry_shadow_summary(
        primary_commit_result=primary_commit_result,
        commit_order=commit_order,
        candidates_by_id=candidates_by_id,
        inp=inp,
        config=shadow_config,
    )
    metrics = deferred_retry_shadow_metrics(summary)
    steps.append(
        algorithm_step_summary_to_json(
            {
                "step_id": RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_SHADOW.value,
                "phase": "incremental_commit",
                "event_type": "rttp.deferred_commit_retry_shadow",
                "title": "Deferred commit retry shadow (observe-only)",
                "summary": ("Primary-pass deferred retry queue shadow; no retry executed."),
                "metrics": metrics,
                "passed": True,
            }
        )
    )


def _append_deferred_retry_execute_step(
    steps: list[dict[str, Any]],
    *,
    execute_out: DeferredRetryExecuteResult,
) -> None:
    """Record bounded deferred retry execution metrics (PR-3)."""

    metrics = deferred_retry_execute_metrics(execute_out)
    steps.append(
        algorithm_step_summary_to_json(
            {
                "step_id": RttpAlgorithmStepId.RTTP_DEFERRED_COMMIT_RETRY_EXECUTE.value,
                "phase": "incremental_commit",
                "event_type": et.EVENT_TYPE_RTTP_DEFERRED_COMMIT_RETRY_EXECUTE,
                "title": "Deferred commit retry execute",
                "summary": "Bounded deferred retry round after primary commit.",
                "metrics": metrics,
                "passed": True,
            }
        )
    )


def _append_catalog_placement_audit_step(
    inp: OptimizationInput,
    committed_ids: tuple[str, ...],
    candidates_by_id: dict[str, BundleCandidate],
    steps: list[dict[str, Any]],
    *,
    catalog_result: CatalogValidationResult | None,
    mode: CatalogValidationMode,
) -> None:
    """Record catalog placement audit/validation in algorithm_steps (output-only)."""

    from django_apps.asteroid_lab.catalog.projection_compat_metrics import (
        committed_projection_audit_metrics,
    )

    catalog_slice = inp.catalog_slice
    slice_hash = catalog_slice_hash(catalog_slice) if catalog_slice is not None else None
    slice_version = catalog_slice.slice_version if catalog_slice is not None else None
    audit = audit_catalog_placements(
        committed_ids,
        candidates_by_id,
        catalog_slice,
        catalog_slice_hash=slice_hash,
        catalog_slice_version=slice_version,
        mode=mode,
    )
    metrics = catalog_placement_audit_metrics(
        audit,
        catalog_slice_hash=slice_hash,
        catalog_slice_version=slice_version,
    )
    metrics.update(
        committed_projection_audit_metrics(
            catalog_slice,
            transport_kind=inp.transport_kind,
            committed_ids=committed_ids,
            candidates_by_id=candidates_by_id,
            include_route_instrumentation=True,
        )
    )
    metrics["catalog_validation_mode"] = mode
    if catalog_result is not None:
        metrics["catalog_issue_codes"] = [issue.issue_code.value for issue in catalog_result.issues]
        metrics["catalog_warning_codes"] = [
            issue.issue_code.value
            for issue in catalog_result.issues
            if issue.severity.value in ("warning", "info")
        ]
        metrics["catalog_slice_missing"] = any(
            issue.issue_code is CatalogPlacementIssueCode.CATALOG_SLICE_MISSING
            for issue in catalog_result.issues
        )
        metrics["catalog_error_issue_codes"] = [
            issue.issue_code.value
            for issue in catalog_result.issues
            if issue.severity.value == "error"
        ]
    step_passed = catalog_result.passed if catalog_result is not None else True
    title = (
        "Catalog placement validation (observe-only)"
        if mode == "observe_only"
        else "Catalog placement validation (mapped fail-closed)"
    )
    steps.append(
        algorithm_step_summary_to_json(
            {
                "step_id": RttpAlgorithmStepId.RTTP_CATALOG_PLACEMENT_VALIDATION.value,
                "phase": "catalog",
                "event_type": "rttp.catalog_placement_validation",
                "title": title,
                "summary": "Committed layout vs catalog footprint audit (output-only).",
                "metrics": metrics,
                "passed": step_passed,
            }
        )
    )


def _transport_mismatch_metrics(inp: OptimizationInput) -> dict[str, int | dict[str, int]]:
    _trunk, _blocked, by_kind = partition_existing_transport(
        inp.existing_transport_cells, inp.transport_kind
    )
    return mismatched_existing_transport_metrics(
        inp.blocked_incompatible_transport_cells, by_kind=by_kind
    )


def _pipeline_field_kind_by_coord(config: RttpPipelineConfig) -> dict[Coord, str] | None:
    if not config.mineable_field_kind_by_coord:
        return None
    return field_kind_map_from_entries(config.mineable_field_kind_by_coord)


def _macro_commit_as_bundle_result(macro_commit: MacroCommitResult) -> CommitResult:
    return CommitResult(
        committed_ids=macro_commit.committed_child_ids,
        reserved_route_cells=macro_commit.reserved_route_cells,
        domain_version=macro_commit.domain_version,
        conflicts=macro_commit.conflicts,
    )


def _run_v01_rttp_pipeline(
    inp: OptimizationInput,
    *,
    policy: ExtractorPlacementPolicy,
    sink: RttpReplaySink,
    config: RttpPipelineConfig,
) -> PipelineResult:
    steps: list[dict[str, Any]] = []
    field_kind_by_coord = _pipeline_field_kind_by_coord(config)
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    transport_mismatch_metrics = _transport_mismatch_metrics(inp)
    start_payload = build_pipeline_start_replay_payload(skeleton)
    _record_pipeline_step(
        sink,
        steps,
        step_id=RttpAlgorithmStepId.RTTP_ROUTE_DOMAIN,
        event_key="rttp-pipeline-start",
        event_type=et.EVENT_TYPE_RTTP_ROUTE_DOMAIN_SNAPSHOT,
        phase="rttp_pipeline",
        title="RTTP pipeline started",
        description=start_payload.description,
        metrics_json={
            "skeleton_id": skeleton.skeleton_id,
            **transport_mismatch_metrics,
        },
        cell_overlay_json=start_payload.cell_overlay_json,
        passed=True,
    )

    generation = generate_candidates(inp, skeleton, policy=policy)
    candidates_payload = build_candidates_replay_payload(
        generation,
        field_kind_by_coord=field_kind_by_coord,
    )
    normal_count = len(generation.normal_candidates)
    _record_pipeline_step(
        sink,
        steps,
        step_id=RttpAlgorithmStepId.RTTP_CANDIDATE_POOL,
        event_key="rttp-candidates",
        event_type=et.EVENT_TYPE_RTTP_CANDIDATE_POOL_SNAPSHOT,
        phase="candidate_generation",
        title="RTTP candidates generated",
        description=candidates_payload.description,
        metrics_json={
            "normal_count": normal_count,
            "rejected_count": len(generation.rejected_candidates),
        },
        cell_overlay_json=candidates_payload.cell_overlay_json,
        passed=normal_count > 0,
    )

    selection_goal, placement_plan = _selection_goal_for_pipeline(
        config=config,
        skeleton_capacity_goals=skeleton.capacity_goals,
        normal_candidates=generation.normal_candidates,
        transport_kind=inp.transport_kind,
    )
    genome = select_genome(
        generation.normal_candidates,
        skeleton,
        inp,
        goal_count=selection_goal,
    )
    selection_payload = build_selection_replay_payload(
        genome,
        generation.normal_candidates,
        field_kind_by_coord=field_kind_by_coord,
    )
    selection_metrics: dict[str, Any] = {
        "commit_order": list(genome.commit_order),
        "selected_count": len(genome.commit_order),
        "placement_goal_count": selection_goal,
    }
    if placement_plan is not None:
        selection_metrics.update(placement_plan.to_summary_dict())
    _record_pipeline_step(
        sink,
        steps,
        step_id=RttpAlgorithmStepId.RTTP_GENOME_SELECTION,
        event_key="rttp-selection",
        event_type=et.EVENT_TYPE_RTTP_GENOME_SELECTION_SNAPSHOT,
        phase="genome_fitness",
        title="RTTP selection complete",
        description=selection_payload.description,
        metrics_json=selection_metrics,
        cell_overlay_json=selection_payload.cell_overlay_json,
        passed=len(genome.commit_order) > 0,
    )

    candidates_by_id = {
        candidate.candidate_id: candidate for candidate in generation.normal_candidates
    }
    domain = initial_commit_domain(skeleton, inp)
    primary_commit_result = incremental_commit(
        genome,
        candidates_by_id,
        inp,
        skeleton,
        domain=domain,
    )
    _append_deferred_retry_shadow_step(
        steps,
        shadow_config=config.deferred_retry_shadow,
        primary_commit_result=primary_commit_result,
        commit_order=genome.commit_order,
        candidates_by_id=candidates_by_id,
        inp=inp,
    )
    shadow_cfg = config.deferred_retry_shadow
    should_execute_deferred_retry = shadow_cfg.enabled and not shadow_cfg.observe_only
    commit_result = primary_commit_result
    if should_execute_deferred_retry:
        execute_out = run_bounded_deferred_retry(
            primary_commit_result=primary_commit_result,
            commit_order=genome.commit_order,
            candidates_by_id=candidates_by_id,
            inp=inp,
            skeleton=skeleton,
            config=shadow_cfg,
        )
        commit_result = execute_out.merged_commit_result
        _append_deferred_retry_execute_step(steps, execute_out=execute_out)
    if commit_result.conflicts:
        genome, commit_result = run_local_lns(
            inp,
            skeleton,
            genome,
            candidates_by_id,
            commit_result,
            policy=policy,
        )

    catalog_mode = config.catalog_placement_validation_mode
    validation_passed, catalog_result = validate_pipeline_layout(
        committed_ids=commit_result.committed_ids,
        reserved_route_cells=commit_result.reserved_route_cells,
        candidates_by_id=candidates_by_id,
        inp=inp,
        catalog_mode=catalog_mode,
    )

    commit_payload, placement_diag = build_commit_replay_payload(
        commit_result,
        validation_passed=validation_passed,
        normal_count=len(generation.normal_candidates),
        commit_order=tuple(genome.commit_order),
        candidates_by_id=candidates_by_id,
        field_kind_by_coord=field_kind_by_coord,
    )
    _record_pipeline_step(
        sink,
        steps,
        step_id=RttpAlgorithmStepId.RTTP_COMMIT,
        event_key="rttp-commit-final",
        event_type=et.EVENT_TYPE_RTTP_COMMIT_DOMAIN_SNAPSHOT,
        phase="incremental_commit",
        title="RTTP commit complete",
        description=commit_payload.description,
        metrics_json={
            "committed_ids": list(commit_result.committed_ids),
            "commit_order": list(genome.commit_order),
            "validation_passed": validation_passed,
            "conflict_count": len(commit_result.conflicts),
            "normal_count": len(generation.normal_candidates),
            "visible_miner_cell_count": placement_diag.visible_miner_cell_count,
            "visible_extension_cell_count": placement_diag.visible_extension_cell_count,
            "placement_route_overlap_warning_count": (
                placement_diag.placement_route_overlap_warning_count
            ),
            "placement_route_overlap_warning_coords": [
                [int(x), int(y)] for x, y in placement_diag.placement_route_overlap_warning_coords
            ],
        },
        cell_overlay_json=commit_payload.cell_overlay_json,
        passed=validation_passed,
    )
    _append_catalog_placement_audit_step(
        inp,
        commit_result.committed_ids,
        candidates_by_id,
        steps,
        catalog_result=catalog_result,
        mode=catalog_mode,
    )

    throughput_factors = collect_committed_throughput_factors(
        committed_ids=commit_result.committed_ids,
        candidates_by_id=candidates_by_id,
    )
    return PipelineResult(
        genome=genome,
        commit_result=commit_result,
        normal_count=len(generation.normal_candidates),
        validation_passed=validation_passed,
        algorithm_steps=tuple(steps),
        committed_throughput_factors=throughput_factors,
        placement_goal_plan=placement_plan,
    )


def _run_macro_rttp_pipeline(
    inp: OptimizationInput,
    *,
    policy: ExtractorPlacementPolicy,
    sink: RttpReplaySink,
    config: RttpPipelineConfig,
) -> PipelineResult:
    steps: list[dict[str, Any]] = []
    field_kind_by_coord = _pipeline_field_kind_by_coord(config)
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    transport_mismatch_metrics = _transport_mismatch_metrics(inp)
    start_payload = build_pipeline_start_replay_payload(skeleton)
    _record_pipeline_step(
        sink,
        steps,
        step_id=RttpAlgorithmStepId.RTTP_ROUTE_DOMAIN,
        event_key="rttp-pipeline-start",
        event_type=et.EVENT_TYPE_RTTP_ROUTE_DOMAIN_SNAPSHOT,
        phase="rttp_pipeline",
        title="RTTP macro pipeline started",
        description=start_payload.description,
        metrics_json={
            "skeleton_id": skeleton.skeleton_id,
            "macro_only_mode": True,
            **transport_mismatch_metrics,
        },
        cell_overlay_json=start_payload.cell_overlay_json,
        passed=True,
    )

    generation = generate_candidates(inp, skeleton, policy=policy)
    macro_generation = compile_macros(
        generation.normal_candidates,
        skeleton,
        inp,
        config=MacroCompileConfig(max_macro_candidates=config.max_macro_candidates),
    )
    macro_normal = dedupe_macros(macro_generation.macro_normal)
    candidates_payload = build_candidates_replay_payload(
        generation,
        macro_generation=macro_generation,
        macro_normal=macro_normal,
        skeleton=skeleton,
        field_kind_by_coord=field_kind_by_coord,
    )
    macro_normal_count = len(macro_normal)
    _record_pipeline_step(
        sink,
        steps,
        step_id=RttpAlgorithmStepId.RTTP_CANDIDATE_POOL,
        event_key="rttp-candidates",
        event_type=et.EVENT_TYPE_RTTP_CANDIDATE_POOL_SNAPSHOT,
        phase="candidate_generation",
        title="RTTP macro candidates generated",
        description=candidates_payload.description,
        metrics_json={
            "normal_count": len(generation.normal_candidates),
            "rejected_count": len(generation.rejected_candidates),
            "macro_normal_count": macro_normal_count,
            "macro_rejected_count": len(macro_generation.macro_rejected),
            "child_normal_count": len(generation.normal_candidates),
        },
        cell_overlay_json=candidates_payload.cell_overlay_json,
        passed=macro_normal_count > 0,
    )

    selection_goal, placement_plan = _selection_goal_for_pipeline(
        config=config,
        skeleton_capacity_goals=skeleton.capacity_goals,
        normal_candidates=generation.normal_candidates,
        transport_kind=inp.transport_kind,
    )
    genome = select_macro_genome(
        macro_normal,
        skeleton,
        inp,
        pipeline_config=config,
        goal_count=selection_goal,
    )
    selection_payload = build_macro_selection_replay_payload(genome, macro_normal)
    macro_selection_metrics: dict[str, Any] = {
        "commit_order": list(genome.commit_order),
        "macro_count_selected": len(genome.commit_order),
        "selected_count": len(genome.commit_order),
        "placement_goal_count": selection_goal,
    }
    if placement_plan is not None:
        macro_selection_metrics.update(placement_plan.to_summary_dict())
    _record_pipeline_step(
        sink,
        steps,
        step_id=RttpAlgorithmStepId.RTTP_GENOME_SELECTION,
        event_key="rttp-selection",
        event_type=et.EVENT_TYPE_RTTP_GENOME_SELECTION_SNAPSHOT,
        phase="genome_fitness",
        title="RTTP macro selection complete",
        description=selection_payload.description,
        metrics_json=macro_selection_metrics,
        cell_overlay_json=selection_payload.cell_overlay_json,
        passed=len(genome.commit_order) > 0,
    )

    candidates_by_id = {
        candidate.candidate_id: candidate for candidate in generation.normal_candidates
    }
    macros_by_id = {row.macro_id: row for row in macro_normal}
    domain = initial_commit_domain(skeleton, inp)
    macro_commit = incremental_commit_macro(
        genome,
        macros_by_id,
        candidates_by_id,
        inp,
        skeleton,
        domain=domain,
    )
    commit_result = _macro_commit_as_bundle_result(macro_commit)

    catalog_mode = config.catalog_placement_validation_mode
    macro_ok = validate_macro_layout(
        macro_commit.committed_macro_ids,
        macro_commit.committed_child_ids,
        macro_commit.reserved_route_cells,
        macros_by_id,
        candidates_by_id,
        inp,
    )
    catalog_result: CatalogValidationResult | None
    if catalog_mode == "observe_only":
        validation_passed = macro_ok
        catalog_result = None
    else:
        catalog_result = validate_catalog_placements(
            macro_commit.committed_child_ids,
            candidates_by_id,
            inp.catalog_slice,
        )
        validation_passed = macro_ok and catalog_result.passed

    commit_payload = build_macro_commit_replay_payload(
        macro_commit,
        validation_passed=validation_passed,
        normal_count=len(generation.normal_candidates),
        commit_order=tuple(genome.commit_order),
        macro_normal=macro_normal,
    )
    _record_pipeline_step(
        sink,
        steps,
        step_id=RttpAlgorithmStepId.RTTP_COMMIT,
        event_key="rttp-commit-final",
        event_type=et.EVENT_TYPE_RTTP_COMMIT_DOMAIN_SNAPSHOT,
        phase="incremental_commit",
        title="RTTP macro commit complete",
        description=commit_payload.description,
        metrics_json={
            "committed_ids": list(commit_result.committed_ids),
            "committed_child_ids": list(macro_commit.committed_child_ids),
            "committed_macro_ids": list(macro_commit.committed_macro_ids),
            "commit_order": list(genome.commit_order),
            "validation_passed": validation_passed,
            "conflict_count": len(commit_result.conflicts),
            "domain_version": macro_commit.domain_version,
            "normal_count": len(generation.normal_candidates),
            "macro_normal_count": len(macro_normal),
        },
        cell_overlay_json=commit_payload.cell_overlay_json,
        passed=validation_passed,
    )
    _append_catalog_placement_audit_step(
        inp,
        macro_commit.committed_child_ids,
        candidates_by_id,
        steps,
        catalog_result=catalog_result,
        mode=catalog_mode,
    )

    throughput_factors = collect_committed_throughput_factors(
        committed_ids=commit_result.committed_ids,
        candidates_by_id=candidates_by_id,
    )
    return PipelineResult(
        genome=genome,
        commit_result=commit_result,
        normal_count=len(generation.normal_candidates),
        validation_passed=validation_passed,
        algorithm_steps=tuple(steps),
        committed_throughput_factors=throughput_factors,
        placement_goal_plan=placement_plan,
    )


def run_rttp_pipeline(
    inp: OptimizationInput,
    *,
    policy: ExtractorPlacementPolicy = ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    replay_sink: RttpReplaySink | None = None,
    pipeline_config: RttpPipelineConfig | None = None,
) -> PipelineResult:
    """Wire skeleton → candidates → select → commit → (LNS if needed) → validate."""

    from django_apps.asteroid_lab.catalog.projection_compat_metrics import (
        reset_projection_compat_instrumentation,
    )

    reset_projection_compat_instrumentation()
    resolved_config = pipeline_config or RttpPipelineConfig()
    sink = resolve_replay_sink(replay_sink)
    if resolved_config.macro_only_mode:
        return _run_macro_rttp_pipeline(
            inp,
            policy=policy,
            sink=sink,
            config=resolved_config,
        )
    return _run_v01_rttp_pipeline(inp, policy=policy, sink=sink, config=resolved_config)


__all__ = ["PipelineResult", "run_rttp_pipeline"]
