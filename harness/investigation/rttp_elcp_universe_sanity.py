"""Attempt-universe sanity metrics for P1-ELCP-RF (Task 9; not solver input)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import ExteriorLaneCapacityPlan
from django_apps.asteroid_lab.optimization.commit.incremental_commit import CommitResult
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RttpPipelineConfig,
)
from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId
from django_apps.asteroid_lab.services.placement_goal import compute_placement_goal_count


def _step_metrics(
    algorithm_steps: Sequence[Mapping[str, object]],
    step_id: str,
) -> Mapping[str, object]:
    for step in algorithm_steps:
        if str(step.get("step_id")) == step_id:
            metrics = step.get("metrics")
            if isinstance(metrics, Mapping):
                return metrics
    return {}


def extract_elcp_attempt_universe_sanity(
    *,
    algorithm_steps: Sequence[Mapping[str, object]],
    inp: OptimizationInput,
    pipeline_config: RttpPipelineConfig,
    primary_commit_result: CommitResult | None = None,
    exterior_lane_plan: ExteriorLaneCapacityPlan | None = None,
) -> dict[str, Any]:
    """Explain why primary forensics universe size == len(commit_order), not full candidate pool."""
    pool_metrics = _step_metrics(algorithm_steps, RttpAlgorithmStepId.RTTP_CANDIDATE_POOL.value)
    selection_metrics = _step_metrics(
        algorithm_steps, RttpAlgorithmStepId.RTTP_GENOME_SELECTION.value
    )
    commit_metrics = _step_metrics(algorithm_steps, RttpAlgorithmStepId.RTTP_COMMIT.value)

    normal_candidate_count = int(pool_metrics.get("normal_count", 0))
    rejected_candidate_count = int(pool_metrics.get("rejected_count", 0))
    candidate_pool_total = normal_candidate_count + rejected_candidate_count

    commit_order = selection_metrics.get("commit_order")
    if isinstance(commit_order, Sequence) and not isinstance(commit_order, str):
        commit_order_len = len(commit_order)
    else:
        commit_order_len = int(selection_metrics.get("selected_count", 0))

    selected_gene_count = commit_order_len
    placement_goal_count = int(selection_metrics.get("placement_goal_count", 0))
    asteroid_field_cell_count = int(
        selection_metrics.get("asteroid_field_cell_count", 0)
        or selection_metrics.get("mineable_platform_cell_count", 0)
        or pipeline_config.placement_platform_cell_count
    )
    if asteroid_field_cell_count <= 0 and pipeline_config.placement_platform_cell_count > 0:
        asteroid_field_cell_count = pipeline_config.placement_platform_cell_count

    expected_goal_from_platform = compute_placement_goal_count(
        asteroid_field_cell_count=asteroid_field_cell_count,
        placement_target_percent=pipeline_config.placement_target_percent,
    )
    expected_attempt_floor = min(
        normal_candidate_count,
        placement_goal_count if placement_goal_count > 0 else expected_goal_from_platform,
    )

    primary_committed_count: int | None = None
    primary_conflict_count: int | None = None
    primary_reprobe_failed_count: int | None = None
    if primary_commit_result is not None:
        primary_committed_count = len(primary_commit_result.committed_ids)
        primary_conflict_count = len(primary_commit_result.conflicts)
        primary_reprobe_failed_count = sum(
            1
            for conflict in primary_commit_result.conflicts
            if conflict.reason.value == "reprobe_failed"
        )

    lane_count = len(exterior_lane_plan.lanes) if exterior_lane_plan is not None else None
    required_external_connectors = inp.required_external_connector_count

    forensics_scope = (
        "selected_genome_commit_order_only" if commit_order_len > 0 else "empty_commit_order"
    )

    return {
        "forensics_scope": forensics_scope,
        "candidate_pool_total": candidate_pool_total,
        "normal_candidate_count": normal_candidate_count,
        "rejected_candidate_count": rejected_candidate_count,
        "selected_genome_size": selected_gene_count,
        "commit_order_len": commit_order_len,
        "primary_commit_attempt_count": commit_order_len,
        "primary_committed_count": primary_committed_count,
        "primary_conflict_count": primary_conflict_count,
        "primary_reprobe_failed_count": primary_reprobe_failed_count,
        "placement_goal_count": placement_goal_count,
        "asteroid_field_cell_count": asteroid_field_cell_count,
        "expected_goal_from_platform": expected_goal_from_platform,
        "expected_attempt_floor": expected_attempt_floor,
        "selection_mode": selection_metrics.get("selection_mode"),
        "max_placement_goal_count_config": pipeline_config.max_placement_goal_count,
        "placement_target_percent": pipeline_config.placement_target_percent,
        "required_external_connectors": required_external_connectors,
        "lane_count": lane_count,
        "exterior_lane_required_lane_count": (
            exterior_lane_plan.required_lane_count if exterior_lane_plan else None
        ),
        "final_commit_metrics_normal_count": commit_metrics.get("normal_count"),
        "universe_reconciliation_note": (
            "M1 ledger walks genome.commit_order only; it does not enumerate "
            "normal_candidates outside selection. primary_commit_attempt_count "
            "equals commit_order_len by construction."
        ),
        "b_spec_nomination_blocked": True,
    }


__all__ = ["extract_elcp_attempt_universe_sanity"]
