"""Lab UI run summary DTOs (read-only; never solver input)."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY,
)

_PLACEHOLDER = "—"


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
    return {
        "id": str(run_id),
        "status": status,
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
    }


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
