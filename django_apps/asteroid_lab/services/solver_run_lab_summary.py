"""Lab UI run summary DTOs (read-only; never solver input)."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)

_PLACEHOLDER = "—"

_QUALITY_TIER_SHORT: dict[str, str] = {
    "CONFIDENT_RECONSTRUCTION": "HIGH",
    "PARTIAL_RECONSTRUCTION": "MED",
    "PROVISIONAL_RECONSTRUCTION": "LOW",
    "FAILED_RECONSTRUCTION": "FAIL",
}


def _quality_tier_short(tier: str) -> str:
    if tier == _PLACEHOLDER or not tier:
        return _PLACEHOLDER
    return _QUALITY_TIER_SHORT.get(tier, tier)


def _section_reconstruction(obs: dict[str, Any] | None) -> dict[str, Any]:
    keys = (
        "cell_count",
        "display_cell_count",
        "mineable_cell_count",
        "confirmed_cell_count",
        "shape_confirmed_cell_count",
        "fluid_confirmed_cell_count",
        "primary_resource_kind",
        "ambiguous_cell_count",
        "external_void_cell_count",
        "quality_tier",
        "confidence_score",
        "quality_tier_short",
    )
    if not obs:
        return dict.fromkeys(keys, _PLACEHOLDER)
    tier = str(obs.get("quality_tier", _PLACEHOLDER))
    return {
        "cell_count": obs.get("cell_count", _PLACEHOLDER),
        "display_cell_count": obs.get("display_cell_count", _PLACEHOLDER),
        "mineable_cell_count": obs.get("mineable_cell_count", _PLACEHOLDER),
        "confirmed_cell_count": obs.get("confirmed_cell_count", _PLACEHOLDER),
        "shape_confirmed_cell_count": obs.get("shape_confirmed_cell_count", _PLACEHOLDER),
        "fluid_confirmed_cell_count": obs.get("fluid_confirmed_cell_count", _PLACEHOLDER),
        "primary_resource_kind": obs.get("primary_resource_kind", _PLACEHOLDER),
        "ambiguous_cell_count": obs.get("ambiguous_cell_count", _PLACEHOLDER),
        "external_void_cell_count": obs.get("external_void_cell_count", _PLACEHOLDER),
        "quality_tier": tier,
        "confidence_score": obs.get("confidence_score", _PLACEHOLDER),
        "quality_tier_short": _quality_tier_short(tier),
    }


def _section_capacity(cap: dict[str, Any] | None) -> dict[str, Any]:
    empty: dict[str, Any] = {
        "shape_max_throughput_per_min": _PLACEHOLDER,
        "fluid_max_throughput_per_min": _PLACEHOLDER,
        "shape_output_unit": _PLACEHOLDER,
        "fluid_output_unit": _PLACEHOLDER,
        "shape_platform_count": _PLACEHOLDER,
        "fluid_platform_count": _PLACEHOLDER,
        "reconstruction_max_throughput_per_min": _PLACEHOLDER,
        "primary_resource_kind": _PLACEHOLDER,
        "platform_upper_bound": _PLACEHOLDER,
        "capacity_basis": _PLACEHOLDER,
        "extraction_rule_source": _PLACEHOLDER,
    }
    if not cap:
        return empty
    by = dict(cap.get("by_resource") or {})
    shape = dict(by.get("shape") or {})
    fluid = dict(by.get("fluid") or {})
    primary = str(cap.get("primary_resource_kind", "shape"))
    shape_max = shape.get("max_throughput_per_min", _PLACEHOLDER)
    primary_row = shape if primary == "shape" else fluid
    headline_max = primary_row.get("max_throughput_per_min", _PLACEHOLDER)
    return {
        "shape_max_throughput_per_min": shape_max,
        "fluid_max_throughput_per_min": fluid.get("max_throughput_per_min", _PLACEHOLDER),
        "shape_output_unit": shape.get("output_unit", _PLACEHOLDER),
        "fluid_output_unit": fluid.get("output_unit", _PLACEHOLDER),
        "shape_platform_count": shape.get("capacity_upper_bound_platform_count", _PLACEHOLDER),
        "fluid_platform_count": fluid.get("capacity_upper_bound_platform_count", _PLACEHOLDER),
        "reconstruction_max_throughput_per_min": headline_max,
        "primary_resource_kind": primary,
        "platform_upper_bound": primary_row.get(
            "capacity_upper_bound_platform_count",
            _PLACEHOLDER,
        ),
        "capacity_basis": cap.get("capacity_basis", _PLACEHOLDER),
        "extraction_rule_source": shape.get("source_kind", _PLACEHOLDER),
    }


def _section_rttp(solver_summary: dict[str, Any]) -> dict[str, Any]:
    order = list(solver_summary.get("commit_order") or [])
    if not order:
        preview: str | int = _PLACEHOLDER
    elif len(order) == 1:
        preview = str(order[0])
    else:
        preview = f"{order[0]} (+{len(order) - 1})"
    actual = solver_summary.get("actual_committed_output_per_min")
    return {
        "confirmed_count": solver_summary.get("confirmed_count", _PLACEHOLDER),
        "validation_passed": bool(solver_summary.get("validation_passed")),
        "actual_committed_output_per_min": actual,
        "actual_output_status": "available" if actual is not None else "pending_pr_2b",
        "candidate_count": solver_summary.get("normal_candidate_count", _PLACEHOLDER),
        "commit_order_preview": preview,
    }


def lab_run_summary_from_solver_summary(
    *,
    run_id: int,
    status: str,
    solver_summary: dict[str, Any],
) -> dict[str, Any]:
    """Build Evolution Runs / Selected Run Detail payload from persisted summary."""

    issue_codes = list(solver_summary.get("issue_codes") or [])
    issue_details = list(solver_summary.get("issue_details") or [])
    validation_passed = bool(solver_summary.get("validation_passed"))
    capacity_satisfied = bool(solver_summary.get("capacity_satisfied"))
    run_success = bool(solver_summary.get("run_success"))
    placement_capacity_satisfied = bool(solver_summary.get("placement_capacity_satisfied"))
    throughput_budget_satisfied = bool(solver_summary.get("throughput_budget_satisfied"))
    confirmed = solver_summary.get("confirmed_count", _PLACEHOLDER)
    target = solver_summary.get("target_miner_bundle_count", _PLACEHOLDER)
    target_placement = solver_summary.get("target_placement_count", target)
    target_throughput = solver_summary.get("target_throughput", target)
    confirmed_throughput = solver_summary.get("confirmed_throughput", _PLACEHOLDER)
    capacity_deficit_count = solver_summary.get("capacity_deficit_count", _PLACEHOLDER)
    throughput_deficit_count = solver_summary.get("throughput_deficit_count", _PLACEHOLDER)
    algorithm_steps = list(solver_summary.get("algorithm_steps") or [])
    macro_only_mode = solver_summary.get("macro_only_mode")
    macro_commit_summary = solver_summary.get("macro_commit_summary")
    row: dict[str, Any] = {
        "id": str(run_id),
        "status": status,
        "algorithm_steps": algorithm_steps,
        "macro_only_mode": macro_only_mode,
        "validation_passed": validation_passed,
        "capacity_satisfied": capacity_satisfied,
        "run_success": run_success,
        "placement_capacity_satisfied": placement_capacity_satisfied,
        "throughput_budget_satisfied": throughput_budget_satisfied,
        "target_miner_bundle_count": target,
        "target_placement_count": target_placement,
        "target_throughput": target_throughput,
        "confirmed_throughput": confirmed_throughput,
        "capacity_deficit_count": capacity_deficit_count,
        "throughput_deficit_count": throughput_deficit_count,
        "issue_codes": issue_codes,
        "first_issue_code": issue_codes[0] if issue_codes else None,
        "first_issue_detail": issue_details[0] if issue_details else None,
        "score": confirmed,
        "miners": confirmed,
        "placed": confirmed,
        "saturation": _PLACEHOLDER,
        "cost": _PLACEHOLDER,
        "belts": _PLACEHOLDER,
        "pipes": _PLACEHOLDER,
        "extension_cap": _PLACEHOLDER,
        "reconstruction": _section_reconstruction(
            solver_summary.get("reconstruction_observability")
        ),
        "capacity": _section_capacity(solver_summary.get("reconstruction_capacity")),
        "rttp": _section_rttp(solver_summary),
    }
    if isinstance(macro_commit_summary, dict) and macro_commit_summary:
        row["macro_commit_summary"] = dict(macro_commit_summary)
    return row


def lab_run_summary_from_orm(run: m.SolverRun) -> dict[str, Any]:
    """Serialize one :class:`SolverRun` for Lab template/JSON."""

    config = dict(run.config_json or {})
    summary = dict(config.get(SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY) or {})
    status = run.status
    if status == m.SolverRun.RunStatus.COMPLETED:
        ui_status = "completed"
    elif status == m.SolverRun.RunStatus.PARTIAL:
        ui_status = "partial"
    elif status == m.SolverRun.RunStatus.FAILED:
        ui_status = "failed"
    else:
        ui_status = str(status)
    return lab_run_summary_from_solver_summary(
        run_id=int(run.pk),
        status=ui_status,
        solver_summary=summary,
    )


def solver_runs_for_lab_project(project_id: int, *, limit: int = 10) -> list[dict[str, Any]]:
    """Latest solver runs for one project (newest first)."""

    qs = m.SolverRun.objects.filter(project_id=int(project_id)).order_by("-created_at", "-id")[
        :limit
    ]
    return [lab_run_summary_from_orm(run) for run in qs]


__all__ = [
    "lab_run_summary_from_orm",
    "lab_run_summary_from_solver_summary",
    "solver_runs_for_lab_project",
]
