"""Track B — RTTP slug certification scan (read-only ops; not solver algorithm input)."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from decimal import Decimal, InvalidOperation
from typing import Any

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.contracts.rttp_ops_policy import (
    CERT_STATUS_CERTIFIED_PASS,
    CERT_STATUS_FAIL_RUNTIME,
    CERT_STATUS_SKIPPED_DIAGNOSTIC,
    CERT_STATUS_SKIPPED_NO_MAP,
    RTTP_DIAGNOSTIC_CANON_SLUGS,
    T3CertificationResult,
    classify_rttp_ops_slug,
    evaluate_t3_certification,
    is_diagnostic_canon_slug,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_RTTP_RECORD_REPLAY_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import (
    SolverRuntimeEntryErrorCode,
    SolverRuntimeEntryResult,
    entry_result_to_json_dict,
    run_solver_runtime_for_project,
)

SCAN_SCHEMA_VERSION = "rttp.slug_certification_scan.v1"

_RUNTIME_ERROR_CODES = frozenset(
    {
        SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE,
        SolverRuntimeEntryErrorCode.PROJECT_NOT_FOUND,
        SolverRuntimeEntryErrorCode.DECODE_FAILED,
    }
)


def resolve_scan_projects(
    *,
    project_id: int | None = None,
    slug: str | None = None,
    limit: int | None = None,
    include_diagnostic: bool = False,
) -> list[m.AsteroidProject]:
    if slug is not None and str(slug).strip():
        normalized = str(slug).strip()
        project = m.AsteroidProject.objects.filter(slug=normalized).first()
        return [project] if project is not None else []

    if project_id is not None:
        project = m.AsteroidProject.objects.filter(pk=int(project_id)).first()
        return [project] if project is not None else []

    qs = m.AsteroidProject.objects.filter(map_inputs__isnull=False).distinct().order_by("slug")
    if not include_diagnostic:
        qs = qs.exclude(slug__in=RTTP_DIAGNOSTIC_CANON_SLUGS)
    if limit is not None and limit > 0:
        qs = qs[: int(limit)]
    return list(qs)


def _parse_metric_number(raw: Any) -> int | float | None:
    if raw is None:
        return None
    try:
        dec = Decimal(str(raw))
    except (InvalidOperation, ValueError):
        return None
    if dec == dec.to_integral_value():
        return int(dec)
    return float(dec)


def _row_from_certification(
    *,
    slug: str,
    project_id: int,
    cert: T3CertificationResult,
    solver_run_id: int | None,
    summary: Mapping[str, Any],
    runtime_error_code: str | None = None,
    runtime_message: str | None = None,
) -> dict[str, Any]:
    issue_codes = list(summary.get("issue_codes") or [])
    row: dict[str, Any] = {
        "slug": slug,
        "project_id": project_id,
        "slug_class": cert.slug_class,
        "solver_run_id": solver_run_id,
        "cert_status": cert.cert_status,
        "t0_passed": cert.t0_pass,
        "t1a_passed": cert.t1a_pass,
        "t1b_passed": cert.t1b_pass,
        "t2_passed": cert.t2_pass,
        "t3_shell_passed": cert.t3_shell_pass,
        "validation_passed": summary.get("validation_passed"),
        "issue_codes": issue_codes,
        "actual_committed": _parse_metric_number(summary.get("actual_committed_output_per_min")),
        "throughput_target_min": _parse_metric_number(summary.get("target_throughput_per_min")),
        "throughput_budget_satisfied": summary.get("throughput_budget_satisfied"),
        "t2_policy_status": summary.get("t2_policy_status"),
        "rttp_ops_slug_class": summary.get("rttp_ops_slug_class") or cert.slug_class,
    }
    if runtime_error_code is not None:
        row["runtime_error_code"] = runtime_error_code
    if runtime_message is not None:
        row["runtime_message"] = runtime_message
    return row


def scan_project_certification(
    project: m.AsteroidProject,
    *,
    game_data_snapshot: Any,
    game_data_provenance: Any,
    catalog_slice: Any,
    run_solver: Callable[..., SolverRuntimeEntryResult] | None = None,
) -> dict[str, Any]:
    """Run one slug through the same runtime entry as ``run_solver`` and evaluate T3 tiers."""
    solver_runner = run_solver if run_solver is not None else run_solver_runtime_for_project
    slug = str(project.slug)
    project_id = int(project.pk)
    slug_class = classify_rttp_ops_slug(slug)

    if not m.AsteroidMapInput.objects.filter(project_id=project_id).exists():
        cert = T3CertificationResult(
            cert_status=CERT_STATUS_SKIPPED_NO_MAP,
            slug_class=slug_class,
            t0_pass=False,
            t1a_pass=False,
            t1b_pass=False,
            t2_pass=False,
            t3_shell_pass=False,
        )
        return _row_from_certification(
            slug=slug,
            project_id=project_id,
            cert=cert,
            solver_run_id=None,
            summary={},
        )

    if is_diagnostic_canon_slug(slug):
        cert = evaluate_t3_certification(
            slug=slug,
            solver_summary={},
            pipeline_steps=(),
        )
        return _row_from_certification(
            slug=slug,
            project_id=project_id,
            cert=cert,
            solver_run_id=None,
            summary={},
        )

    config = {SOLVER_RUN_CONFIG_RTTP_RECORD_REPLAY_KEY: False}
    result = solver_runner(
        project_id,
        config=config,
        game_data_snapshot=game_data_snapshot,
        game_data_provenance=game_data_provenance,
        catalog_slice=catalog_slice,
    )
    body = entry_result_to_json_dict(result)
    summary: dict[str, Any] = dict(body.get("solver_summary") or {})
    if summary.get("validation_passed") is None:
        summary["validation_passed"] = result.validation_passed
    steps = summary.get("algorithm_steps") or []

    if result.error_code in _RUNTIME_ERROR_CODES or (
        not result.ok and not summary and result.solver_run_id is None
    ):
        cert = T3CertificationResult(
            cert_status=CERT_STATUS_FAIL_RUNTIME,
            slug_class=slug_class,
            t0_pass=False,
            t1a_pass=False,
            t1b_pass=False,
            t2_pass=False,
            t3_shell_pass=False,
        )
        error_value = result.error_code.value if result.error_code is not None else None
        return _row_from_certification(
            slug=slug,
            project_id=project_id,
            cert=cert,
            solver_run_id=result.solver_run_id,
            summary=summary,
            runtime_error_code=error_value,
            runtime_message=result.message,
        )

    cert = evaluate_t3_certification(
        slug=slug,
        solver_summary=summary,
        pipeline_steps=steps,
    )
    return _row_from_certification(
        slug=slug,
        project_id=project_id,
        cert=cert,
        solver_run_id=result.solver_run_id,
        summary=summary,
    )


def build_scan_report(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    rows = [dict(row) for row in results]
    certified_pass_count = sum(
        1 for row in rows if row.get("cert_status") == CERT_STATUS_CERTIFIED_PASS
    )
    non_blocked = frozenset(
        {
            CERT_STATUS_CERTIFIED_PASS,
            CERT_STATUS_SKIPPED_DIAGNOSTIC,
            CERT_STATUS_SKIPPED_NO_MAP,
        }
    )
    blocked_count = sum(1 for row in rows if row.get("cert_status") not in non_blocked)
    return {
        "schema_version": SCAN_SCHEMA_VERSION,
        "candidate_count": len(rows),
        "certified_pass_count": certified_pass_count,
        "blocked_count": blocked_count,
        "results": rows,
    }


def run_slug_certification_scan(
    *,
    projects: Sequence[m.AsteroidProject],
    game_data_snapshot: Any,
    game_data_provenance: Any,
    catalog_slice: Any,
    run_solver: Callable[..., SolverRuntimeEntryResult] | None = None,
) -> dict[str, Any]:
    solver_runner = run_solver if run_solver is not None else run_solver_runtime_for_project
    results = [
        scan_project_certification(
            project,
            game_data_snapshot=game_data_snapshot,
            game_data_provenance=game_data_provenance,
            catalog_slice=catalog_slice,
            run_solver=solver_runner,
        )
        for project in projects
    ]
    return build_scan_report(results)


__all__ = [
    "SCAN_SCHEMA_VERSION",
    "build_scan_report",
    "resolve_scan_projects",
    "run_slug_certification_scan",
    "scan_project_certification",
]
