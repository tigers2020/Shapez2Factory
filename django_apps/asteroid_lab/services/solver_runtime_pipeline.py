"""Solver Runtime A→M orchestration (PR7). No ORM; receives gene_templates as input."""

from __future__ import annotations

import time
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from django_apps.asteroid_lab.optimization.candidate_dtos import CandidateGenerationConfig
from django_apps.asteroid_lab.optimization.candidate_generator import (
    default_generation_config,
    generate_gene_candidates,
)
from django_apps.asteroid_lab.optimization.candidate_selector import select_gene_candidates_greedy
from django_apps.asteroid_lab.optimization.capacity_planner import plan_capacity
from django_apps.asteroid_lab.optimization.commit_best_candidates import commit_selected_candidates
from django_apps.asteroid_lab.optimization.enums import ValidationSeverity
from django_apps.asteroid_lab.optimization.final_validation import validate_final_layout
from django_apps.asteroid_lab.optimization.gene_template import GeneTemplate
from django_apps.asteroid_lab.optimization.input_contracts import ValidationIssue
from django_apps.asteroid_lab.optimization.loaded_snapshot import LoadedReconstructionSnapshot
from django_apps.asteroid_lab.optimization.materialization_dtos import RouteMaterializationResult
from django_apps.asteroid_lab.optimization.pipeline_result import SolverRuntimeResult
from django_apps.asteroid_lab.optimization.placement_network_materializer import (
    materialize_confirmed_placements,
    merge_materialized_layout,
)
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_loaded_snapshot,
)
from django_apps.asteroid_lab.optimization.route_domain import clear_seed_domain_cache
from django_apps.asteroid_lab.optimization.route_goal_planner import plan_route_goals
from django_apps.asteroid_lab.optimization.route_network_materializer import (
    materialize_route_network,
)
from django_apps.asteroid_lab.optimization.timing_metrics import (
    CandidateGenerationTiming,
    SolverRuntimeTimingMetrics,
)

if TYPE_CHECKING:
    from django_apps.asteroid_lab.replay.solver_runtime_replay_recorder import (
        SolverRuntimeReplayRecorder,
    )


def _issue_detail(issue: ValidationIssue) -> dict[str, Any]:
    detail: dict[str, Any] = {
        "issue_code": issue.issue_code.value,
        "coord": list(issue.coord) if issue.coord is not None else None,
        "candidate_id": issue.candidate_id,
        "route_reservation_id": issue.route_reservation_id,
        "transport_kind": issue.transport_kind.value if issue.transport_kind else None,
        "message": issue.message,
    }
    if issue.issue_extra:
        for key, value in issue.issue_extra.items():
            if key == "transport_kind" and hasattr(value, "value"):
                detail[key] = value.value
            elif isinstance(value, tuple) and len(value) == 2:
                detail[key] = list(value)
            else:
                detail[key] = value
    return detail


def _error_issues(issues: tuple[ValidationIssue, ...]) -> tuple[ValidationIssue, ...]:
    return tuple(i for i in issues if i.severity is ValidationSeverity.ERROR)


def _build_solver_summary(
    *,
    validation_passed: bool,
    commit_count: int,
    skipped: tuple[str, ...],
    materialization: RouteMaterializationResult,
    issues: tuple[ValidationIssue, ...],
    timing: SolverRuntimeTimingMetrics,
) -> dict[str, Any]:
    error_issues = _error_issues(issues)
    return {
        "validation_passed": validation_passed,
        "confirmed_count": commit_count,
        "skipped_candidate_ids": list(skipped),
        "materialization_failure_reason": (
            materialization.failure_reason.value if materialization.failure_reason else None
        ),
        "issue_codes": [i.issue_code.value for i in error_issues],
        "issue_details": [_issue_detail(i) for i in error_issues],
        "timing": timing.to_dict(),
    }


def run_solver_runtime_pipeline(
    *,
    loaded: LoadedReconstructionSnapshot,
    gene_templates: tuple[GeneTemplate, ...],
    run_key: str = "runtime",
    generation_config: CandidateGenerationConfig | None = None,
    recorder: SolverRuntimeReplayRecorder | None = None,
) -> SolverRuntimeResult:
    """Execute Phase A→M in documented order (no ORM; receives gene_templates as input)."""

    pipeline_start = time.perf_counter()
    timing = SolverRuntimeTimingMetrics()
    clear_seed_domain_cache()

    config = generation_config or default_generation_config()

    inp = optimization_input_from_loaded_snapshot(loaded)
    if recorder is not None:
        recorder.record_optimization_input_loaded(inp)

    shape_platforms = max(12, len(inp.mineable_cells) * 8)
    capacity = plan_capacity(
        mineable_cell_count=len(inp.mineable_cells),
        shape_platform_count=shape_platforms,
        fluid_platform_count=0,
    )
    if recorder is not None:
        recorder.record_capacity_plan_created(capacity)

    planned = plan_route_goals(inp, capacity)
    inp = replace(inp, route_goals=planned.goals)
    if recorder is not None:
        recorder.record_route_goals_generated(planned)

    templates = gene_templates
    pool = generate_gene_candidates(inp, templates, config)
    if isinstance(pool.timing, CandidateGenerationTiming):
        timing.absorb_candidate_generation(pool.timing)
    if recorder is not None:
        recorder.record_candidate_pool_completed(pool)
        recorder.record_candidate_pool_details(pool)

    select_start = time.perf_counter()
    plan = select_gene_candidates_greedy(pool.normal_candidates, inp=inp)
    timing.evolution_ms = (time.perf_counter() - select_start) * 1000.0
    if recorder is not None:
        recorder.record_candidate_selection_completed(plan)
        recorder.record_genome_scaffold(plan, pool=pool)

    candidates_by_id = {c.candidate_id: c for c in pool.normal_candidates}
    commit, commit_timing = commit_selected_candidates(plan, candidates_by_id, inp=inp)
    timing.absorb_commit(commit_timing)
    if recorder is not None:
        recorder.record_route_committed(commit)
        recorder.record_commit_details(plan, candidates_by_id, commit)

    gene_templates_by_id = {g.gene_id: g for g in gene_templates}
    route_materialization = materialize_route_network(commit, candidates_by_id)
    equipment = materialize_confirmed_placements(
        commit,
        candidates_by_id,
        gene_templates_by_id=gene_templates_by_id,
    )
    materialization = merge_materialized_layout(route_materialization, equipment)
    if recorder is not None:
        recorder.record_route_materialized(materialization)

    validation_start = time.perf_counter()
    validation = validate_final_layout(
        commit,
        materialization.layout,
        inp=inp,
        candidates_by_id=candidates_by_id,
    )
    timing.validation_ms = (time.perf_counter() - validation_start) * 1000.0
    if recorder is not None:
        recorder.record_validation_completed(validation)

    timing.total_ms = (time.perf_counter() - pipeline_start) * 1000.0

    summary = _build_solver_summary(
        validation_passed=validation.passed,
        commit_count=len(commit.confirmed),
        skipped=commit.skipped_candidate_ids,
        materialization=materialization,
        issues=validation.issues,
        timing=timing,
    )

    if recorder is not None:
        recorder.record_result_layout(
            commit=commit,
            materialization=materialization,
            validation=validation,
            solver_summary=summary,
        )

    return SolverRuntimeResult(
        run_key=run_key,
        commit=commit,
        materialization=materialization,
        validation=validation,
        solver_summary=summary,
    )
