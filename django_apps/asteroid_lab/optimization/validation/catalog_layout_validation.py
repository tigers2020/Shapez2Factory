"""Layout validation AND mapped-only catalog placement validation (Track D+ PR-2)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from django_apps.asteroid_lab.adapters.catalog_placement_validation import (
    validate_catalog_placements,
)
from django_apps.asteroid_lab.contracts.catalog_placement import CatalogValidationMode
from django_apps.asteroid_lab.contracts.catalog_validation import (
    CatalogValidationResult,
    ValidationSeverity,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId
from django_apps.asteroid_lab.optimization.validation.final_validation import (
    validate_final_layout,
)


def validate_pipeline_layout(
    *,
    committed_ids: tuple[str, ...],
    reserved_route_cells: frozenset[Coord],
    candidates_by_id: dict[str, BundleCandidate],
    inp: OptimizationInput,
    catalog_mode: CatalogValidationMode,
) -> tuple[bool, CatalogValidationResult | None]:
    layout_ok = validate_final_layout(
        committed_ids,
        reserved_route_cells,
        candidates_by_id,
        inp,
    )
    if catalog_mode == "observe_only":
        return layout_ok, None
    catalog_result = validate_catalog_placements(
        committed_ids,
        candidates_by_id,
        inp.catalog_slice,
    )
    return layout_ok and catalog_result.passed, catalog_result


def catalog_error_issue_codes_for_summary(
    catalog_result: CatalogValidationResult | None,
) -> tuple[str, ...]:
    if catalog_result is None:
        return ()
    return tuple(
        issue.issue_code.value
        for issue in catalog_result.issues
        if issue.severity is ValidationSeverity.ERROR
    )


def catalog_error_issue_codes_from_algorithm_steps(
    algorithm_steps: Sequence[Mapping[str, object]],
) -> tuple[str, ...]:
    for step in algorithm_steps:
        if str(step.get("step_id")) != RttpAlgorithmStepId.RTTP_CATALOG_PLACEMENT_VALIDATION.value:
            continue
        metrics = step.get("metrics")
        if not isinstance(metrics, Mapping):
            return ()
        raw = metrics.get("catalog_error_issue_codes")
        if not isinstance(raw, Sequence) or isinstance(raw, str):
            return ()
        return tuple(str(code) for code in raw)
    return ()


__all__ = [
    "catalog_error_issue_codes_for_summary",
    "catalog_error_issue_codes_from_algorithm_steps",
    "validate_pipeline_layout",
]
