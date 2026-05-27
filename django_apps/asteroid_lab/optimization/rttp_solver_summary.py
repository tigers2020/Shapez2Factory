"""Build persisted ``solver_summary`` payloads (output-only; never solver input)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum
from typing import Any

from django_apps.asteroid_lab.adapters.catalog_footprint_policy import (
    summarize_footprint_catalog,
)
from django_apps.asteroid_lab.catalog.projection_compat_metrics import (
    equipment_projection_metrics,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import BuildingCatalogSlice
from django_apps.asteroid_lab.contracts.rttp_ops_policy import classify_t2_policy
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.reconstruction.confidence import QUALITY_TIER_CONFIDENT
from django_apps.asteroid_lab.reconstruction.result import ReconstructionResult
from django_apps.asteroid_lab.replay import event_types as et

RTTP_ALGORITHM_LABEL = "rttp_v0.1"
# Must match services.throughput_target.THROUGHPUT_TARGET_SHORTFALL_ISSUE_CODE
THROUGHPUT_TARGET_SHORTFALL_ISSUE_CODE = "throughput_target_shortfall"


class RttpAlgorithmStepId(StrEnum):
    """Stable step ids inside ``solver_summary["algorithm_steps"]``."""

    RECONSTRUCTION = "reconstruction"
    RTTP_ROUTE_DOMAIN = "rttp.route_domain"
    RTTP_CANDIDATE_POOL = "rttp.candidate_pool"
    RTTP_GENOME_SELECTION = "rttp.genome_selection"
    RTTP_COMMIT = "rttp.commit"
    RTTP_CATALOG_SLICE = "rttp.catalog_slice"
    RTTP_CATALOG_PLACEMENT_VALIDATION = "rttp.catalog_placement_validation"
    RTTP_GA_EVOLUTION_SHADOW = "rttp.ga_evolution_shadow"
    RTTP_DEFERRED_COMMIT_RETRY_SHADOW = "rttp.deferred_commit_retry_shadow"
    RTTP_DEFERRED_COMMIT_RETRY_EXECUTE = "rttp.deferred_commit_retry_execute"


def algorithm_step_summary_to_json(step: Mapping[str, Any]) -> dict[str, Any]:
    """Normalize one step row for JSON persistence."""

    row: dict[str, Any] = {
        "step_id": str(step["step_id"]),
        "phase": str(step["phase"]),
        "event_type": str(step["event_type"]),
        "title": str(step["title"]),
        "summary": str(step.get("summary") or ""),
        "metrics": dict(step.get("metrics") or {}),
    }
    passed = step.get("passed")
    if passed is not None:
        row["passed"] = bool(passed)
    return row


def reconstruction_step_from_result(recon: ReconstructionResult) -> dict[str, Any]:
    """Summarize reconstruction for ``solver_summary`` (read-only observability)."""

    summary_json = dict(recon.summary_json or {})
    metrics: dict[str, Any] = {
        "cell_count": len(recon.cells),
        "confidence_score": float(recon.confidence_score),
        "quality_tier": str(recon.quality_tier),
        "confirmed_cell_count": len(recon.confirmed_cells),
        "ambiguous_cell_count": len(recon.ambiguous_cells),
        "external_void_cell_count": len(recon.external_void_cells),
    }
    metrics.update(summary_json)
    tier = str(recon.quality_tier)
    lines = [
        "Map reconstruction complete.",
        f"quality_tier: {tier}",
        f"cell_count: {len(recon.cells)}",
        f"confidence_score: {recon.confidence_score:.3f}",
    ]
    return algorithm_step_summary_to_json(
        {
            "step_id": RttpAlgorithmStepId.RECONSTRUCTION.value,
            "phase": "reconstruction",
            "event_type": et.EVENT_TYPE_RECONSTRUCTION_MAP_COMPLETE,
            "title": "Map reconstruction",
            "summary": "\n".join(lines),
            "metrics": metrics,
            "passed": tier == QUALITY_TIER_CONFIDENT,
        }
    )


def catalog_slice_step_from_slice(
    catalog_slice: BuildingCatalogSlice,
    *,
    transport_kind: TransportKind = TransportKind.SHAPE_BELT,
) -> dict[str, Any]:
    """Output-only catalog geometry metrics (Track D)."""

    metrics = summarize_footprint_catalog(catalog_slice)
    metrics.update(equipment_projection_metrics(catalog_slice, transport_kind=transport_kind))
    return algorithm_step_summary_to_json(
        {
            "step_id": RttpAlgorithmStepId.RTTP_CATALOG_SLICE.value,
            "phase": "catalog",
            "event_type": "rttp.catalog_slice",
            "title": "Catalog slice",
            "summary": "Building catalog slice geometry summary (output-only).",
            "metrics": metrics,
            "passed": True,
        }
    )


def _placement_capacity_dev_metric(
    *,
    committed_count: int,
    throughput_goal: Mapping[str, Any] | None,
) -> bool:
    if throughput_goal is None:
        return False
    goal = int(throughput_goal.get("placement_goal_count") or 0)
    needed = int(throughput_goal.get("bundles_needed_for_target") or 0)
    if goal <= 0:
        return False
    return committed_count >= min(goal, needed)


def _issue_codes_for_solver_summary(
    *,
    pipeline_ok: bool,
    catalog_error_issue_codes: tuple[str, ...],
    optimization_goal: Mapping[str, Any] | None,
) -> list[str]:
    if pipeline_ok:
        return []
    if catalog_error_issue_codes:
        return list(catalog_error_issue_codes)
    issue_code = optimization_goal.get("issue_code") if optimization_goal is not None else None
    if isinstance(issue_code, str) and issue_code:
        return [issue_code]
    return ["rttp_validation_failed"]


def extract_macro_commit_summary(
    algorithm_steps: Sequence[Mapping[str, Any]],
    *,
    macro_only_mode: bool,
    validation_passed: bool,
) -> dict[str, Any] | None:
    """Output-only macro commit HUD payload (never solver input)."""

    if not macro_only_mode:
        return None
    commit_metrics: dict[str, Any] = {}
    for step in algorithm_steps:
        if str(step.get("step_id")) == RttpAlgorithmStepId.RTTP_COMMIT.value:
            commit_metrics = dict(step.get("metrics") or {})
    return {
        "macro_only_mode": True,
        "committed_macro_ids": list(commit_metrics.get("committed_macro_ids") or []),
        "committed_child_ids": list(commit_metrics.get("committed_child_ids") or []),
        "domain_version": commit_metrics.get("domain_version"),
        "validation_passed": bool(validation_passed),
        "conflict_count": int(commit_metrics.get("conflict_count") or 0),
    }


def build_rttp_solver_summary(
    *,
    pipeline_ok: bool,
    committed_count: int,
    normal_count: int,
    commit_order: tuple[str, ...],
    algorithm_steps: tuple[Mapping[str, Any], ...] | list[Mapping[str, Any]],
    macro_only_mode: bool = False,
    reconstruction_step: Mapping[str, Any] | None = None,
    catalog_slice_step: Mapping[str, Any] | None = None,
    catalog_error_issue_codes: tuple[str, ...] = (),
    reconstruction_capacity: Mapping[str, Any] | None = None,
    reconstruction_observability: Mapping[str, Any] | None = None,
    actual_committed_output_per_min: str | None = None,
    throughput_budget_fields: Mapping[str, Any] | None = None,
    throughput_goal: Mapping[str, Any] | None = None,
    throughput_shortfall_reason: str | None = None,
    project_slug: str | None = None,
    optimization_goal: Mapping[str, Any] | None = None,
    run_status: str | None = None,
    structural_validation_passed: bool | None = None,
) -> dict[str, Any]:
    """Aggregate RTTP scalars and per-step summaries for ``SolverRun.config_json``."""

    steps_json: list[dict[str, Any]] = []
    if reconstruction_step is not None:
        steps_json.append(algorithm_step_summary_to_json(reconstruction_step))
    if catalog_slice_step is not None:
        steps_json.append(algorithm_step_summary_to_json(catalog_slice_step))
    steps_json.extend(algorithm_step_summary_to_json(step) for step in algorithm_steps)
    budget_ok = pipeline_ok
    if throughput_budget_fields is not None:
        budget_ok = bool(throughput_budget_fields.get("throughput_budget_satisfied"))
    deprecated_capacity_ok = budget_ok if throughput_budget_fields is not None else pipeline_ok
    goal_block = dict(optimization_goal) if optimization_goal is not None else None
    issue_codes = _issue_codes_for_solver_summary(
        pipeline_ok=pipeline_ok,
        catalog_error_issue_codes=catalog_error_issue_codes,
        optimization_goal=goal_block,
    )
    summary: dict[str, Any] = {
        "algorithm": RTTP_ALGORITHM_LABEL,
        "macro_only_mode": bool(macro_only_mode),
        "validation_passed": pipeline_ok,
        "run_success": pipeline_ok,
        "capacity_satisfied": deprecated_capacity_ok,
        "placement_capacity_satisfied": _placement_capacity_dev_metric(
            committed_count=committed_count,
            throughput_goal=throughput_goal,
        ),
        "throughput_budget_satisfied": budget_ok,
        "confirmed_count": committed_count,
        "target_miner_bundle_count": len(commit_order),
        "target_placement_count": len(commit_order),
        "normal_candidate_count": normal_count,
        "commit_order": list(commit_order),
        "issue_codes": issue_codes,
        "issue_details": [] if pipeline_ok else [],
        "algorithm_steps": steps_json,
    }
    if run_status is not None:
        summary["run_status"] = str(run_status)
    if structural_validation_passed is not None:
        summary["structural_validation_passed"] = bool(structural_validation_passed)
    if goal_block is not None:
        summary["optimization_goal"] = goal_block
        target_cells = goal_block.get("target_mining_equipment_cells")
        if target_cells is not None:
            summary["target_mining_equipment_cells"] = target_cells
    macro_hud = extract_macro_commit_summary(
        algorithm_steps,
        macro_only_mode=macro_only_mode,
        validation_passed=pipeline_ok,
    )
    if macro_hud is not None:
        summary["macro_commit_summary"] = macro_hud
    if reconstruction_capacity is not None:
        summary["reconstruction_capacity"] = dict(reconstruction_capacity)
    if reconstruction_observability is not None:
        summary["reconstruction_observability"] = dict(reconstruction_observability)
    if actual_committed_output_per_min is not None:
        summary["actual_committed_output_per_min"] = actual_committed_output_per_min
    if throughput_budget_fields is not None:
        fields = dict(throughput_budget_fields)
        summary.update(fields)
        summary["throughput_budget_satisfied"] = bool(fields["throughput_budget_satisfied"])
        if not fields["throughput_budget_satisfied"]:
            codes = list(summary["issue_codes"])
            if THROUGHPUT_TARGET_SHORTFALL_ISSUE_CODE not in codes:
                codes.append(THROUGHPUT_TARGET_SHORTFALL_ISSUE_CODE)
            summary["issue_codes"] = codes
    if throughput_goal is not None:
        summary["throughput_goal"] = dict(throughput_goal)
    if throughput_shortfall_reason and throughput_budget_fields is not None:
        if not throughput_budget_fields.get("throughput_budget_satisfied"):
            details = list(summary.get("issue_details") or [])
            details.append(
                {
                    "code": THROUGHPUT_TARGET_SHORTFALL_ISSUE_CODE,
                    "throughput_shortfall_reason": throughput_shortfall_reason,
                }
            )
            summary["issue_details"] = details
    if throughput_budget_fields is not None:
        policy = classify_t2_policy(
            project_slug=project_slug,
            throughput_budget_satisfied=summary.get("throughput_budget_satisfied"),
        )
        summary.update(policy.as_summary_fields())
    return summary


__all__ = [
    "RTTP_ALGORITHM_LABEL",
    "RttpAlgorithmStepId",
    "algorithm_step_summary_to_json",
    "build_rttp_solver_summary",
    "catalog_slice_step_from_slice",
    "extract_macro_commit_summary",
    "reconstruction_step_from_result",
]
