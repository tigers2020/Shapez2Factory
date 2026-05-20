"""Solver Runtime A→M orchestration (PR7). No ORM; receives gene_templates as input."""

from __future__ import annotations

import time
from dataclasses import replace
from typing import TYPE_CHECKING, Any

from django_apps.asteroid_lab.optimization.bundle_selection_targets import (
    BundleSelectionTargets,
    bundle_selection_targets_from_run_config,
)
from django_apps.asteroid_lab.optimization.candidate_dtos import (
    CandidateGenerationConfig,
    CandidateGenerationResult,
)
from django_apps.asteroid_lab.optimization.candidate_generator import (
    default_generation_config,
    generate_gene_candidates,
)
from django_apps.asteroid_lab.optimization.candidate_selector import (
    SelectedCandidatePlan,
    SelectionDiagnostics,
    select_gene_candidates_greedy,
)
from django_apps.asteroid_lab.optimization.capacity_planner import plan_capacity
from django_apps.asteroid_lab.optimization.commit_best_candidates import (
    SkippedCandidateRecord,
    commit_selected_candidates,
)
from django_apps.asteroid_lab.optimization.commit_order_diversity import diversify_commit_order
from django_apps.asteroid_lab.optimization.enums import CommitConflictReason, ValidationSeverity
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


def _unique_gene_ids_used_count(pool_normal_candidates: tuple) -> int:
    return len({getattr(c, "gene_id", None) for c in pool_normal_candidates} - {None})


def _pool_throughput(pool_normal_candidates: tuple) -> int:
    return sum(getattr(c, "base_throughput", 0) for c in pool_normal_candidates)


def _selected_throughput(
    plan: SelectedCandidatePlan,
    candidates_by_id: dict[str, Any],
) -> int:
    return sum(
        getattr(candidates_by_id[cid], "base_throughput", 0)
        for cid in plan.ordered_candidate_ids
        if cid in candidates_by_id
    )


def _commit_skip_summary(
    skipped_records: tuple[SkippedCandidateRecord, ...],
) -> dict[str, Any]:
    skipped_by_reason: dict[str, int] = {}
    for record in skipped_records:
        key = record.reason.value
        skipped_by_reason[key] = skipped_by_reason.get(key, 0) + 1

    def _count(reason: CommitConflictReason) -> int:
        return skipped_by_reason.get(reason.value, 0)

    return {
        "skipped_by_reason": skipped_by_reason,
        "commit_occupied_cell_conflict_count": _count(
            CommitConflictReason.OCCUPIED_CELL_CONFLICT
        ),
        "commit_route_cell_conflict_count": _count(CommitConflictReason.ROUTE_CELL_CONFLICT),
        "commit_route_probe_failed_count": _count(CommitConflictReason.ROUTE_PROBE_FAILED),
        "commit_transport_kind_conflict_count": _count(
            CommitConflictReason.TRANSPORT_KIND_CONFLICT
        ),
        "commit_hard_blocked_conflict_count": _count(
            CommitConflictReason.HARD_BLOCKED_CONFLICT
        ),
        "commit_hard_protected_conflict_count": _count(
            CommitConflictReason.HARD_PROTECTED_CONFLICT
        ),
        "commit_equipment_transport_overlap_count": _count(
            CommitConflictReason.EQUIPMENT_TRANSPORT_OVERLAP
        ),
    }


def _gate_c_branch_hint(
    *,
    rim_cell_count: int,
    reachable_anchors_after_prefilter_count: int,
    unique_anchors_in_normal_pool_count: int,
) -> str:
    """Gate C branch for PR-2 scope (read-only; no algorithm change in PR-1).

    Decision table (solver_summary ``gate_c_branch_hint``):
    | Branch | Condition | Bottleneck | PR-2 |
    | C1 | rim > reachable | probe/domain prefilter | reachable expansion |
    | C2 | rim == reachable | rim/topology supply | rim expansion |
    | C3 | reachable > pool anchors | dedupe/truncation | max_candidates policy |

    Production 7-route snapshot (rim=reachable=pool=7) → ``c2_rim_topology``.
    """

    if rim_cell_count > reachable_anchors_after_prefilter_count:
        return "c1_probe_domain"
    if reachable_anchors_after_prefilter_count > unique_anchors_in_normal_pool_count:
        return "c3_dedupe_truncation"
    if rim_cell_count == reachable_anchors_after_prefilter_count:
        return "c2_rim_topology"
    return "unknown"


def _generation_diagnostics_metrics(pool: CandidateGenerationResult) -> dict[str, int | str]:
    diag = pool.generation_diagnostics
    pool_anchor_count = len({c.extractor for c in pool.normal_candidates})
    return {
        "rim_cell_count": diag.rim_cell_count,
        "reachable_anchors_after_prefilter_count": diag.reachable_anchors_after_prefilter_count,
        "truncated_by_max_candidates_count": diag.truncated_by_max_candidates_count,
        "normal_pool_variants_per_anchor_max": diag.normal_pool_variants_per_anchor_max,
        "unique_anchors_after_probe_budget_count": diag.unique_anchors_after_probe_budget_count,
        "anchors_dropped_by_probe_budget_count": diag.anchors_dropped_by_probe_budget_count,
        "probe_budget_floor_reserved_count": diag.probe_budget_floor_reserved_count,
        "probe_budget_fill_count": diag.probe_budget_fill_count,
        "unique_anchors_after_dedupe_count": diag.unique_anchors_after_dedupe_count,
        "unique_anchors_after_truncate_count": pool_anchor_count,
        "anchor_preserved_by_truncation_count": diag.anchor_preserved_by_truncation_count,
        "anchor_dropped_by_truncation_count": diag.anchor_dropped_by_truncation_count,
        "gate_c_branch_hint": _gate_c_branch_hint(
            rim_cell_count=diag.rim_cell_count,
            reachable_anchors_after_prefilter_count=diag.reachable_anchors_after_prefilter_count,
            unique_anchors_in_normal_pool_count=pool_anchor_count,
        ),
    }


def _anchor_diversity_metrics(
    pool: CandidateGenerationResult,
    plan: SelectedCandidatePlan,
    candidates_by_id: dict[str, Any],
    selection_diag: SelectionDiagnostics,
) -> dict[str, int]:
    pool_anchors = {c.extractor for c in pool.normal_candidates}
    selected_extractors: list[tuple[int, int]] = []
    for cid in plan.ordered_candidate_ids:
        candidate = candidates_by_id.get(cid)
        if candidate is not None:
            selected_extractors.append(candidate.extractor)

    unique_selected = len(set(selected_extractors))
    per_anchor: dict[tuple[int, int], int] = {}
    for coord in selected_extractors:
        per_anchor[coord] = per_anchor.get(coord, 0) + 1
    variants_per_anchor_max = max(per_anchor.values(), default=0)

    return {
        "unique_anchors_in_normal_pool_count": len(pool_anchors),
        "unique_anchors_selected_count": unique_selected,
        "variants_per_anchor_max": variants_per_anchor_max,
        "selected_duplicate_anchor_count": len(selected_extractors) - unique_selected,
        "selection_skipped_duplicate_anchor_count": (
            selection_diag.selection_skipped_duplicate_anchor_count
        ),
        "max_selected_variants_per_extractor": (
            selection_diag.max_selected_variants_per_extractor
        ),
        "selection_stopped_by_throughput_budget": int(
            selection_diag.selection_stopped_by_throughput_budget
        ),
        "selected_throughput_at_stop": selection_diag.selected_throughput_at_stop,
    }


def _confirmed_throughput(commit: Any, candidates_by_id: dict[str, Any]) -> int:
    total = 0
    for placement in commit.confirmed:
        candidate = candidates_by_id.get(placement.candidate_id)
        if candidate is None:
            continue
        total += getattr(candidate, "base_throughput", 0)
    return total


def _build_solver_summary(
    *,
    validation_passed: bool,
    commit_count: int,
    skipped_records: tuple[SkippedCandidateRecord, ...],
    materialization: RouteMaterializationResult,
    issues: tuple[ValidationIssue, ...],
    timing: SolverRuntimeTimingMetrics,
    targets: BundleSelectionTargets,
    raw_pattern_count: int,
    pool_metrics: dict[str, int],
    plan: SelectedCandidatePlan,
    commit_attempt_count: int,
    throughput_metrics: dict[str, int],
    anchor_metrics: dict[str, int],
    generation_metrics: dict[str, int | str],
) -> dict[str, Any]:
    error_issues = _error_issues(issues)
    commit_rolled_back_count = len(skipped_records)
    skip_summary = _commit_skip_summary(skipped_records)
    confirmed_tp = throughput_metrics["confirmed_throughput"]
    target_placement_count = targets.target_miner_bundle_count
    # v0: same numeric budget for placement count and throughput units (greedy-v0).
    target_throughput = target_placement_count
    placement_capacity_satisfied = commit_count >= target_placement_count
    throughput_budget_satisfied = confirmed_tp >= target_throughput
    capacity_satisfied = placement_capacity_satisfied and throughput_budget_satisfied
    capacity_deficit_count = max(0, target_placement_count - commit_count)
    throughput_deficit_count = max(0, target_throughput - confirmed_tp)
    run_success = validation_passed and capacity_satisfied
    return {
        "validation_passed": validation_passed,
        "confirmed_count": commit_count,
        "confirmed_miner_count": commit_count,
        "skipped_candidate_ids": [r.candidate_id for r in skipped_records],
        **skip_summary,
        "materialization_failure_reason": (
            materialization.failure_reason.value if materialization.failure_reason else None
        ),
        "issue_codes": [i.issue_code.value for i in issues],
        "issue_details": [_issue_detail(i) for i in error_issues],
        "timing": timing.to_dict(),
        "route_out_count": targets.route_out_count,
        "miners_per_route": targets.miners_per_shape_route,
        "target_miner_bundle_count": targets.target_miner_bundle_count,
        "target_placement_count": target_placement_count,
        "raw_pattern_count": raw_pattern_count,
        "projected_candidate_count_before_probe": pool_metrics[
            "projected_candidate_count_before_probe"
        ],
        "normal_candidate_count_after_probe": pool_metrics["normal_candidate_count_after_probe"],
        "rejected_candidate_count": pool_metrics["rejected_candidate_count"],
        "deduped_candidate_count": pool_metrics["deduped_candidate_count"],
        "best_genome_enabled_gene_count": len(plan.ordered_candidate_ids),
        "commit_attempt_count": commit_attempt_count,
        "commit_confirmed_count": commit_count,
        "commit_rolled_back_count": commit_rolled_back_count,
        # NOTE: target_miner_bundle_count / target_placement_count / target_throughput
        # share the same v0 numeric budget (route slots × miners_per_route).
        "target_throughput": target_throughput,
        "normal_pool_throughput": throughput_metrics["normal_pool_throughput"],
        "selected_throughput": throughput_metrics["selected_throughput"],
        "confirmed_throughput": throughput_metrics["confirmed_throughput"],
        "unique_gene_ids_used_count": throughput_metrics["unique_gene_ids_used_count"],
        "placement_capacity_satisfied": placement_capacity_satisfied,
        "throughput_budget_satisfied": throughput_budget_satisfied,
        "capacity_satisfied": capacity_satisfied,
        "capacity_deficit_count": capacity_deficit_count,
        "throughput_deficit_count": throughput_deficit_count,
        "run_success": run_success,
        **anchor_metrics,
        **generation_metrics,
    }


def run_solver_runtime_pipeline(
    *,
    loaded: LoadedReconstructionSnapshot,
    gene_templates: tuple[GeneTemplate, ...],
    run_key: str = "runtime",
    generation_config: CandidateGenerationConfig | None = None,
    run_config: dict[str, Any] | None = None,
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

    capacity = plan_capacity(mineable_cell_count=len(inp.mineable_cells))
    if recorder is not None:
        recorder.record_capacity_plan_created(capacity)

    planned = plan_route_goals(inp, capacity)
    inp = replace(inp, route_goals=planned.goals)
    targets = bundle_selection_targets_from_run_config(inp.route_goals, run_config)
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
    plan, selection_diag = select_gene_candidates_greedy(
        pool.normal_candidates,
        inp=inp,
        targets=targets,
    )
    timing.evolution_ms = (time.perf_counter() - select_start) * 1000.0
    if recorder is not None:
        recorder.record_candidate_selection_completed(plan, targets=targets)
        recorder.record_genome_scaffold(plan, pool=pool, targets=targets)

    candidates_by_id = {c.candidate_id: c for c in pool.normal_candidates}
    commit_plan = diversify_commit_order(plan, candidates_by_id)
    commit, commit_timing = commit_selected_candidates(commit_plan, candidates_by_id, inp=inp)
    timing.absorb_commit(commit_timing)
    if recorder is not None:
        recorder.record_route_committed(commit)
        recorder.record_commit_details(commit_plan, candidates_by_id, commit)

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
        targets=targets,
    )
    timing.validation_ms = (time.perf_counter() - validation_start) * 1000.0
    if recorder is not None:
        recorder.record_validation_completed(validation)

    timing.total_ms = (time.perf_counter() - pipeline_start) * 1000.0

    pool_metrics = {
        "projected_candidate_count_before_probe": pool.projected_candidate_count_before_probe,
        "normal_candidate_count_after_probe": len(pool.normal_candidates),
        "rejected_candidate_count": len(pool.rejected_candidates),
        "deduped_candidate_count": pool.deduped_candidate_count,
    }
    throughput_metrics = {
        "target_throughput": targets.target_miner_bundle_count,
        "normal_pool_throughput": _pool_throughput(pool.normal_candidates),
        "selected_throughput": _selected_throughput(plan, candidates_by_id),
        "confirmed_throughput": _confirmed_throughput(commit, candidates_by_id),
        "unique_gene_ids_used_count": _unique_gene_ids_used_count(pool.normal_candidates),
    }
    commit_attempt_count = len(plan.ordered_candidate_ids)
    anchor_metrics = _anchor_diversity_metrics(
        pool, plan, candidates_by_id, selection_diag
    )
    generation_metrics = _generation_diagnostics_metrics(pool)
    summary = _build_solver_summary(
        validation_passed=validation.passed,
        commit_count=len(commit.confirmed),
        skipped_records=commit.skipped_candidates,
        materialization=materialization,
        issues=validation.issues,
        timing=timing,
        targets=targets,
        raw_pattern_count=len(gene_templates),
        pool_metrics=pool_metrics,
        plan=plan,
        commit_attempt_count=commit_attempt_count,
        throughput_metrics=throughput_metrics,
        anchor_metrics=anchor_metrics,
        generation_metrics=generation_metrics,
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
