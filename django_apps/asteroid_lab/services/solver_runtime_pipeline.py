"""Solver Runtime A→M orchestration (PR7)."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

from django_apps.asteroid_lab.optimization.candidate_dtos import (
    CandidateGenerationConfig,
    GeneCandidate,
)
from django_apps.asteroid_lab.optimization.candidate_generator import (
    default_generation_config,
    generate_gene_candidates,
)
from django_apps.asteroid_lab.optimization.candidate_selector import select_gene_candidates_greedy
from django_apps.asteroid_lab.optimization.capacity_planner import plan_capacity
from django_apps.asteroid_lab.optimization.commit_best_candidates import (
    ConfirmedGenePlacement,
    commit_selected_candidates,
)
from django_apps.asteroid_lab.optimization.enums import (
    OptimizationReplayEventType,
    ValidationSeverity,
)
from django_apps.asteroid_lab.optimization.final_validation import validate_final_layout
from django_apps.asteroid_lab.optimization.gene_template import GeneTemplate
from django_apps.asteroid_lab.optimization.gene_template_loader import load_gene_templates_from_json
from django_apps.asteroid_lab.optimization.input_contracts import ValidationIssue
from django_apps.asteroid_lab.optimization.loaded_snapshot import LoadedReconstructionSnapshot
from django_apps.asteroid_lab.optimization.materialization_dtos import RouteMaterializationResult
from django_apps.asteroid_lab.optimization.pipeline_result import SolverRuntimeResult
from django_apps.asteroid_lab.optimization.reconstruction_adapter import (
    optimization_input_from_loaded_snapshot,
)
from django_apps.asteroid_lab.optimization.route_goal_planner import plan_route_goals
from django_apps.asteroid_lab.optimization.route_network_materializer import (
    materialize_route_network,
)
from django_apps.asteroid_lab.replay.replay_recording_cells import (
    overlay_cell_dicts_from_materialization,
    visible_cell_dicts_from_loaded,
)
from django_apps.asteroid_lab.services.runtime_replay_recorder import RuntimeReplayRecorder


def _load_gene_templates(path: Path) -> tuple[GeneTemplate, ...]:
    if path.is_dir():
        templates: list[GeneTemplate] = []
        for json_path in sorted(path.glob("*.json")):
            templates.extend(load_gene_templates_from_json(json_path))
        return tuple(templates)
    return load_gene_templates_from_json(path)


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


def _route_committed_metrics(
    placement: ConfirmedGenePlacement,
    candidates_by_id: dict[str, GeneCandidate],
) -> dict[str, Any]:
    res = placement.reservation
    metrics: dict[str, Any] = {
        "candidate_id": placement.candidate_id,
        "route_reservation_id": res.reservation_id,
        "path_head": list(res.path[0]) if res.path else None,
        "path_tail": list(res.path[-1]) if res.path else None,
        "path_len": len(res.path),
        "reserved_cell_count": len(res.reserved_cells),
    }
    candidate = candidates_by_id.get(placement.candidate_id)
    if candidate is not None:
        metrics["output_stub"] = list(candidate.fixed_output_transport)
        metrics["path_contains_output_stub"] = (
            candidate.fixed_output_transport in res.reserved_cells
        )
    return metrics


def _error_issues(issues: tuple[ValidationIssue, ...]) -> tuple[ValidationIssue, ...]:
    return tuple(i for i in issues if i.severity is ValidationSeverity.ERROR)


def _build_solver_summary(
    *,
    validation_passed: bool,
    commit_count: int,
    skipped: tuple[str, ...],
    materialization: RouteMaterializationResult,
    issues: tuple[ValidationIssue, ...],
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
    }


def run_solver_runtime_pipeline(
    *,
    loaded: LoadedReconstructionSnapshot,
    gene_template_path: str | Path,
    run_key: str = "runtime",
    generation_config: CandidateGenerationConfig | None = None,
) -> SolverRuntimeResult:
    """Execute Phase A→M in documented order (no ORM; replay is output-only)."""

    recorder = RuntimeReplayRecorder()
    template_path = Path(gene_template_path)
    config = generation_config or default_generation_config(max_candidates=32)

    inp = optimization_input_from_loaded_snapshot(loaded)
    replay_base_cells = visible_cell_dicts_from_loaded(loaded)
    recorder.append(
        OptimizationReplayEventType.OPTIMIZATION_INPUT_LOADED,
        title="Optimization input loaded",
        metrics={"mineable_cell_count": len(inp.mineable_cells)},
        visible_cells=replay_base_cells,
    )

    shape_platforms = max(12, len(inp.mineable_cells) * 8)
    capacity = plan_capacity(
        mineable_cell_count=len(inp.mineable_cells),
        shape_platform_count=shape_platforms,
        fluid_platform_count=0,
    )
    recorder.append(
        OptimizationReplayEventType.CAPACITY_PLAN_CREATED,
        title="Capacity plan",
        metrics={
            "shape_goal_count": capacity.shape_goal_count,
            "fluid_goal_count": capacity.fluid_goal_count,
        },
        visible_cells=replay_base_cells,
    )

    planned = plan_route_goals(inp, capacity)
    inp = replace(inp, route_goals=planned.goals)
    recorder.append(
        OptimizationReplayEventType.ROUTE_GOAL_GENERATED,
        title="Route goals planned",
        metrics={"route_goal_count": len(planned.goals)},
        visible_cells=replay_base_cells,
    )

    templates = _load_gene_templates(template_path)
    for gene in templates:
        recorder.append(
            OptimizationReplayEventType.PATTERN_GENERATED,
            title=f"Pattern {gene.gene_id}",
            metrics={"gene_id": gene.gene_id},
            visible_cells=replay_base_cells,
        )

    pool = generate_gene_candidates(inp, templates, config)
    recorder.append(
        OptimizationReplayEventType.CANDIDATE_POOL_COMPLETED,
        title="Candidate pool",
        metrics={
            "normal_count": len(pool.normal_candidates),
            "rejected_count": len(pool.rejected_candidates),
        },
        visible_cells=replay_base_cells,
    )

    plan = select_gene_candidates_greedy(pool.normal_candidates, inp=inp)
    recorder.append(
        OptimizationReplayEventType.CANDIDATE_SELECTION_COMPLETED,
        title="Candidate selection",
        metrics={"selected_count": len(plan.ordered_candidate_ids)},
        visible_cells=replay_base_cells,
    )

    candidates_by_id = {c.candidate_id: c for c in pool.normal_candidates}
    for cid in plan.ordered_candidate_ids:
        recorder.append(
            OptimizationReplayEventType.ROUTE_COMMIT_ATTEMPTED,
            title=f"Commit attempt {cid}",
            metrics={"candidate_id": cid},
            visible_cells=replay_base_cells,
        )

    commit = commit_selected_candidates(plan, candidates_by_id, inp=inp)
    for placement in commit.confirmed:
        recorder.append(
            OptimizationReplayEventType.ROUTE_COMMITTED,
            title=f"Committed {placement.candidate_id}",
            metrics=_route_committed_metrics(placement, candidates_by_id),
            visible_cells=replay_base_cells,
        )
    for cid in commit.skipped_candidate_ids:
        recorder.append(
            OptimizationReplayEventType.ROUTE_ROLLED_BACK,
            title=f"Skipped {cid}",
            metrics={"candidate_id": cid},
            visible_cells=replay_base_cells,
        )

    materialization = materialize_route_network(commit, candidates_by_id)
    mat_metrics: dict[str, Any] = {
        "cell_count": len(materialization.layout.cells) if materialization.layout else 0,
    }
    if materialization.failure_reason is not None:
        mat_metrics["materialization_failure_reason"] = materialization.failure_reason.value
    mat_overlay = overlay_cell_dicts_from_materialization(materialization)
    recorder.append(
        OptimizationReplayEventType.ROUTE_MATERIALIZED,
        title="Route materialized",
        metrics=mat_metrics,
        visible_cells=replay_base_cells,
        overlay_cells=mat_overlay,
    )

    validation = validate_final_layout(
        commit,
        materialization.layout,
        inp=inp,
        candidates_by_id=candidates_by_id,
    )
    error_issues = _error_issues(validation.issues)
    error_issue_codes = [i.issue_code.value for i in error_issues]
    recorder.append(
        OptimizationReplayEventType.VALIDATION_COMPLETED,
        title="Validation completed",
        metrics={
            "passed": validation.passed,
            "issue_count": len(validation.issues),
            "first_issue_code": error_issue_codes[0] if error_issue_codes else None,
            "issue_codes": error_issue_codes,
            "first_issue_detail": _issue_detail(error_issues[0]) if error_issues else None,
        },
        visible_cells=replay_base_cells,
        overlay_cells=mat_overlay,
    )

    summary = _build_solver_summary(
        validation_passed=validation.passed,
        commit_count=len(commit.confirmed),
        skipped=commit.skipped_candidate_ids,
        materialization=materialization,
        issues=validation.issues,
    )

    return SolverRuntimeResult(
        run_key=run_key,
        commit=commit,
        materialization=materialization,
        validation=validation,
        solver_summary=summary,
        replay_frames=recorder.frames(),
    )
