"""Mapped-only fail-closed catalog placement validation (Track D+ PR-2)."""

from __future__ import annotations

from django_apps.asteroid_lab.adapters.catalog_placement_audit import (
    classify_committed_catalog_placements,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import BuildingCatalogSlice
from django_apps.asteroid_lab.contracts.catalog_placement import (
    CatalogPlacementIssueCode,
    CatalogPlacementIssueRow,
)
from django_apps.asteroid_lab.contracts.catalog_validation import (
    CatalogValidationIssue,
    CatalogValidationResult,
    ValidationSeverity,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate

_ERROR_CODES = frozenset(
    {
        CatalogPlacementIssueCode.CATALOG_FOOTPRINT_MISMATCH,
        CatalogPlacementIssueCode.CATALOG_VARIANT_NOT_IN_SLICE,
        CatalogPlacementIssueCode.CATALOG_ANCHOR_TRANSFORM_ERROR,
        CatalogPlacementIssueCode.CATALOG_ROTATION_UNSUPPORTED,
        CatalogPlacementIssueCode.CATALOG_CONNECTOR_MISMATCH,
    }
)


def _severity_for_row(row: CatalogPlacementIssueRow) -> ValidationSeverity:
    if row.issue_code is CatalogPlacementIssueCode.CATALOG_VARIANT_MAPPING_MISSING:
        return ValidationSeverity.WARNING
    if row.issue_code is CatalogPlacementIssueCode.CATALOG_SLICE_MISSING:
        return ValidationSeverity.WARNING
    if not row.had_ref:
        return ValidationSeverity.WARNING
    if row.issue_code in _ERROR_CODES:
        return ValidationSeverity.ERROR
    return ValidationSeverity.WARNING


def _row_to_issue(row: CatalogPlacementIssueRow) -> CatalogValidationIssue:
    return CatalogValidationIssue(
        issue_code=row.issue_code,
        severity=_severity_for_row(row),
        candidate_id=row.candidate_id or None,
        message=row.message,
    )


def validate_catalog_placements(
    committed_ids: tuple[str, ...],
    candidates_by_id: dict[str, BundleCandidate],
    catalog_slice: BuildingCatalogSlice | None,
) -> CatalogValidationResult:
    rows = classify_committed_catalog_placements(
        committed_ids, candidates_by_id, catalog_slice
    )
    issues = tuple(_row_to_issue(row) for row in rows)
    passed = not any(issue.severity is ValidationSeverity.ERROR for issue in issues)
    return CatalogValidationResult(passed=passed, issues=issues)


__all__ = ["validate_catalog_placements"]
