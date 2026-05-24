"""RTTP end-to-end pipeline wiring skeleton through validation (PR-5 + v1 macro)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    ExtractorPlacementPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
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
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpPipelineConfig,
    RttpSkeletonConfig,
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
from django_apps.asteroid_lab.optimization.validation.final_validation import (
    validate_final_layout,
    validate_macro_layout,
)
from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.dto import SnapshotEventDTO


@dataclass(frozen=True, slots=True)
class PipelineResult:
    genome: PlacementGenome
    commit_result: CommitResult
    normal_count: int
    validation_passed: bool
    algorithm_steps: tuple[dict[str, Any], ...] = ()


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


def _transport_mismatch_metrics(inp: OptimizationInput) -> dict[str, int | dict[str, int]]:
    _trunk, _blocked, by_kind = partition_existing_transport(
        inp.existing_transport_cells, inp.transport_kind
    )
    return mismatched_existing_transport_metrics(
        inp.blocked_incompatible_transport_cells, by_kind=by_kind
    )


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
) -> PipelineResult:
    steps: list[dict[str, Any]] = []
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
    candidates_payload = build_candidates_replay_payload(generation)
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

    genome = select_genome(generation.normal_candidates, skeleton, inp)
    selection_payload = build_selection_replay_payload(genome, generation.normal_candidates)
    _record_pipeline_step(
        sink,
        steps,
        step_id=RttpAlgorithmStepId.RTTP_GENOME_SELECTION,
        event_key="rttp-selection",
        event_type=et.EVENT_TYPE_RTTP_GENOME_SELECTION_SNAPSHOT,
        phase="genome_fitness",
        title="RTTP selection complete",
        description=selection_payload.description,
        metrics_json={"commit_order": list(genome.commit_order)},
        cell_overlay_json=selection_payload.cell_overlay_json,
        passed=len(genome.commit_order) > 0,
    )

    candidates_by_id = {
        candidate.candidate_id: candidate for candidate in generation.normal_candidates
    }
    domain = initial_commit_domain(skeleton, inp)
    commit_result = incremental_commit(
        genome,
        candidates_by_id,
        inp,
        skeleton,
        domain=domain,
    )

    if commit_result.conflicts:
        genome, commit_result = run_local_lns(
            inp,
            skeleton,
            genome,
            candidates_by_id,
            commit_result,
            policy=policy,
        )

    validation_passed = validate_final_layout(
        commit_result.committed_ids,
        commit_result.reserved_route_cells,
        candidates_by_id,
        inp,
    )

    commit_payload = build_commit_replay_payload(
        commit_result,
        validation_passed=validation_passed,
        normal_count=len(generation.normal_candidates),
        commit_order=tuple(genome.commit_order),
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
        },
        cell_overlay_json=commit_payload.cell_overlay_json,
        passed=validation_passed,
    )

    return PipelineResult(
        genome=genome,
        commit_result=commit_result,
        normal_count=len(generation.normal_candidates),
        validation_passed=validation_passed,
        algorithm_steps=tuple(steps),
    )


def _run_macro_rttp_pipeline(
    inp: OptimizationInput,
    *,
    policy: ExtractorPlacementPolicy,
    sink: RttpReplaySink,
    config: RttpPipelineConfig,
) -> PipelineResult:
    steps: list[dict[str, Any]] = []
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

    genome = select_macro_genome(
        macro_normal,
        skeleton,
        inp,
        pipeline_config=config,
    )
    selection_payload = build_macro_selection_replay_payload(genome, macro_normal)
    _record_pipeline_step(
        sink,
        steps,
        step_id=RttpAlgorithmStepId.RTTP_GENOME_SELECTION,
        event_key="rttp-selection",
        event_type=et.EVENT_TYPE_RTTP_GENOME_SELECTION_SNAPSHOT,
        phase="genome_fitness",
        title="RTTP macro selection complete",
        description=selection_payload.description,
        metrics_json={
            "commit_order": list(genome.commit_order),
            "macro_count_selected": len(genome.commit_order),
        },
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

    validation_passed = validate_macro_layout(
        macro_commit.committed_macro_ids,
        macro_commit.committed_child_ids,
        macro_commit.reserved_route_cells,
        macros_by_id,
        candidates_by_id,
        inp,
    )

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

    return PipelineResult(
        genome=genome,
        commit_result=commit_result,
        normal_count=len(generation.normal_candidates),
        validation_passed=validation_passed,
        algorithm_steps=tuple(steps),
    )


def run_rttp_pipeline(
    inp: OptimizationInput,
    *,
    policy: ExtractorPlacementPolicy = ExtractorPlacementPolicy.INTERIOR_AND_RIM,
    replay_sink: RttpReplaySink | None = None,
    pipeline_config: RttpPipelineConfig | None = None,
) -> PipelineResult:
    """Wire skeleton → candidates → select → commit → (LNS if needed) → validate."""

    resolved_config = pipeline_config or RttpPipelineConfig()
    sink = resolve_replay_sink(replay_sink)
    if resolved_config.macro_only_mode:
        return _run_macro_rttp_pipeline(
            inp,
            policy=policy,
            sink=sink,
            config=resolved_config,
        )
    return _run_v01_rttp_pipeline(inp, policy=policy, sink=sink)


__all__ = ["PipelineResult", "run_rttp_pipeline"]
