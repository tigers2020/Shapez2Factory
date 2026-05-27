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
from django_apps.asteroid_lab.contracts.exterior_lane_capacity import (
    ExteriorLaneCapacityPlan,
    ExteriorLaneCommitValidationSnapshot,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.optimization.rttp_solver_summary import RttpAlgorithmStepId
from django_apps.asteroid_lab.optimization.validation.final_validation import (
    validate_final_layout,
)
from django_apps.asteroid_lab.optimization.validation.layout_connectivity_validation import (
    validate_layout_connectivity_issues,
)
from django_apps.asteroid_lab.optimization.validation.validate_exterior_lane_contract import (
    validate_exterior_lane_contract_issues,
)


def validate_pipeline_layout(
    *,
    committed_ids: tuple[str, ...],
    reserved_route_cells: frozenset[Coord],
    candidates_by_id: dict[str, BundleCandidate],
    inp: OptimizationInput,
    catalog_mode: CatalogValidationMode,
    trunk_mask_cells: frozenset[Coord] | None = None,
    lane_commit_snapshot: ExteriorLaneCommitValidationSnapshot | None = None,
    exterior_lane_plan: ExteriorLaneCapacityPlan | None = None,
) -> tuple[bool, CatalogValidationResult | None, tuple[str, ...]]:
    connectivity_issues = validate_layout_connectivity_issues(
        committed_ids=committed_ids,
        reserved_route_cells=reserved_route_cells,
        candidates_by_id=candidates_by_id,
        trunk_mask_cells=trunk_mask_cells or frozenset(),
        inp=inp,
    )
    lane_issues: tuple[str, ...] = ()
    if lane_commit_snapshot is not None and exterior_lane_plan is not None:
        lane_issues = validate_exterior_lane_contract_issues(
            committed_ids=committed_ids,
            lane_commit_snapshot=lane_commit_snapshot,
            candidates_by_id=candidates_by_id,
            exterior_lane_plan=exterior_lane_plan,
        )
    connectivity_issues = connectivity_issues + lane_issues
    layout_ok = validate_final_layout(
        committed_ids,
        reserved_route_cells,
        candidates_by_id,
        inp,
    )
    structural_ok = layout_ok and not connectivity_issues
    if catalog_mode == "observe_only":
        return structural_ok, None, connectivity_issues
    catalog_result = validate_catalog_placements(
        committed_ids,
        candidates_by_id,
        inp.catalog_slice,
    )
    passed = structural_ok and catalog_result.passed
    return passed, catalog_result, connectivity_issues


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


def layout_connectivity_issue_codes_from_algorithm_steps(
    algorithm_steps: Sequence[Mapping[str, object]],
) -> tuple[str, ...]:
    for step in algorithm_steps:
        if str(step.get("step_id")) != RttpAlgorithmStepId.RTTP_COMMIT.value:
            continue
        metrics = step.get("metrics")
        if not isinstance(metrics, Mapping):
            return ()
        raw = metrics.get("layout_connectivity_issue_codes")
        if not isinstance(raw, Sequence) or isinstance(raw, str):
            return ()
        return tuple(str(code) for code in raw)
    return ()


def pipeline_layout_issue_codes_from_algorithm_steps(
    algorithm_steps: Sequence[Mapping[str, object]],
) -> tuple[str, ...]:
    """Catalog + layout connectivity error codes from persisted algorithm steps."""

    catalog = catalog_error_issue_codes_from_algorithm_steps(algorithm_steps)
    layout = layout_connectivity_issue_codes_from_algorithm_steps(algorithm_steps)
    if not catalog and not layout:
        return ()
    merged: list[str] = []
    for code in (*layout, *catalog):
        if code not in merged:
            merged.append(code)
    return tuple(merged)


__all__ = [
    "catalog_error_issue_codes_for_summary",
    "catalog_error_issue_codes_from_algorithm_steps",
    "layout_connectivity_issue_codes_from_algorithm_steps",
    "pipeline_layout_issue_codes_from_algorithm_steps",
    "validate_pipeline_layout",
]
