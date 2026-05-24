"""Task 3.5 — runtime solver_summary issue_codes wiring for catalog placement validation."""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.catalog_placement import CatalogPlacementIssueCode
from django_apps.asteroid_lab.optimization.rttp_solver_summary import (
    RttpAlgorithmStepId,
    build_rttp_solver_summary,
)
from django_apps.asteroid_lab.optimization.validation.catalog_layout_validation import (
    catalog_error_issue_codes_from_algorithm_steps,
)


def _catalog_validation_step(
    *,
    catalog_error_issue_codes: list[str] | None = None,
    catalog_warning_codes: list[str] | None = None,
    catalog_validation_mode: str = "mapped_fail_closed",
    passed: bool = False,
) -> dict[str, object]:
    metrics: dict[str, object] = {
        "catalog_validation_mode": catalog_validation_mode,
    }
    if catalog_error_issue_codes is not None:
        metrics["catalog_error_issue_codes"] = catalog_error_issue_codes
    if catalog_warning_codes is not None:
        metrics["catalog_warning_codes"] = catalog_warning_codes
    return {
        "step_id": RttpAlgorithmStepId.RTTP_CATALOG_PLACEMENT_VALIDATION.value,
        "phase": "catalog",
        "event_type": "rttp.catalog_placement_validation",
        "title": "Catalog placement validation",
        "summary": "",
        "metrics": metrics,
        "passed": passed,
    }


def test_runtime_extracts_catalog_error_issue_codes_from_algorithm_steps() -> None:
    steps = (
        _catalog_validation_step(
            catalog_error_issue_codes=[CatalogPlacementIssueCode.CATALOG_FOOTPRINT_MISMATCH.value],
        ),
    )
    assert catalog_error_issue_codes_from_algorithm_steps(steps) == (
        CatalogPlacementIssueCode.CATALOG_FOOTPRINT_MISMATCH.value,
    )


def test_runtime_summary_exposes_catalog_error_codes_when_pipeline_fails() -> None:
    steps = (
        _catalog_validation_step(
            catalog_error_issue_codes=[CatalogPlacementIssueCode.CATALOG_FOOTPRINT_MISMATCH.value],
        ),
    )
    catalog_error_issue_codes = catalog_error_issue_codes_from_algorithm_steps(steps)
    summary = build_rttp_solver_summary(
        pipeline_ok=False,
        committed_count=1,
        normal_count=1,
        commit_order=("c1",),
        algorithm_steps=steps,
        catalog_error_issue_codes=catalog_error_issue_codes,
    )
    assert summary["issue_codes"] == [CatalogPlacementIssueCode.CATALOG_FOOTPRINT_MISMATCH.value]


def test_runtime_summary_warning_only_does_not_enter_top_level_issue_codes() -> None:
    steps = (
        _catalog_validation_step(
            catalog_error_issue_codes=[],
            catalog_warning_codes=[CatalogPlacementIssueCode.CATALOG_VARIANT_MAPPING_MISSING.value],
            passed=True,
        ),
    )
    catalog_error_issue_codes = catalog_error_issue_codes_from_algorithm_steps(steps)
    summary = build_rttp_solver_summary(
        pipeline_ok=True,
        committed_count=1,
        normal_count=1,
        commit_order=("c1",),
        algorithm_steps=steps,
        catalog_error_issue_codes=catalog_error_issue_codes,
    )
    assert summary["issue_codes"] == []


def test_runtime_summary_generic_fallback_when_no_catalog_error_codes() -> None:
    steps = (
        {
            "step_id": RttpAlgorithmStepId.RTTP_COMMIT.value,
            "phase": "incremental_commit",
            "event_type": "rttp.commit",
            "title": "commit",
            "summary": "",
            "metrics": {"validation_passed": False},
            "passed": False,
        },
    )
    catalog_error_issue_codes = catalog_error_issue_codes_from_algorithm_steps(steps)
    assert catalog_error_issue_codes == ()
    summary = build_rttp_solver_summary(
        pipeline_ok=False,
        committed_count=0,
        normal_count=1,
        commit_order=(),
        algorithm_steps=steps,
        catalog_error_issue_codes=catalog_error_issue_codes,
    )
    assert summary["issue_codes"] == ["rttp_validation_failed"]


def test_runtime_observe_only_step_has_no_catalog_error_codes_for_e3() -> None:
    steps = (
        _catalog_validation_step(
            catalog_validation_mode="observe_only",
            passed=True,
        ),
    )
    assert catalog_error_issue_codes_from_algorithm_steps(steps) == ()
    summary = build_rttp_solver_summary(
        pipeline_ok=True,
        committed_count=1,
        normal_count=1,
        commit_order=("c1",),
        algorithm_steps=steps,
        catalog_error_issue_codes=(),
    )
    assert summary["issue_codes"] == []
