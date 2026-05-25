"""Observe-only catalog placement audit (Track D+ PR-1) + shared classification (PR-2)."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import (
    CatalogTransformError,
    expected_footprint_coords,
)
from django_apps.asteroid_lab.catalog.asteroid_equipment_projection import (
    CANON_MANUAL_CANONICAL_ID_PREFIX,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    BuildingCatalogSlice,
    VariantGeometryCatalog,
)
from django_apps.asteroid_lab.contracts.catalog_placement import (
    CatalogPlacementAudit,
    CatalogPlacementIssueCode,
    CatalogPlacementIssueRow,
    CatalogValidationMode,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate


def _variant_geometry(
    canonical_id: str,
    catalog_slice: BuildingCatalogSlice,
) -> VariantGeometryCatalog | None:
    for geometry in catalog_slice.variant_geometries:
        if geometry.canonical_id == canonical_id:
            return geometry
    return None


def classify_committed_catalog_placements(
    committed_ids: tuple[str, ...],
    candidates_by_id: dict[str, BundleCandidate],
    catalog_slice: BuildingCatalogSlice | None,
) -> tuple[CatalogPlacementIssueRow, ...]:
    if catalog_slice is None:
        if not committed_ids:
            return ()
        return (
            CatalogPlacementIssueRow(
                candidate_id="",
                issue_code=CatalogPlacementIssueCode.CATALOG_SLICE_MISSING,
                had_ref=False,
                message="catalog slice missing; classification skipped",
            ),
        )

    rows: list[CatalogPlacementIssueRow] = []
    for candidate_id in committed_ids:
        candidate = candidates_by_id.get(candidate_id)
        if candidate is None:
            continue
        ref = candidate.catalog_placement_ref
        if ref is None:
            rows.append(
                CatalogPlacementIssueRow(
                    candidate_id=candidate_id,
                    issue_code=CatalogPlacementIssueCode.CATALOG_VARIANT_MAPPING_MISSING,
                    had_ref=False,
                    message="no catalog_placement_ref",
                )
            )
            continue
        geometry = _variant_geometry(ref.canonical_id, catalog_slice)
        if geometry is None:
            if ref.canonical_id.startswith(CANON_MANUAL_CANONICAL_ID_PREFIX):
                # Phase A: equipment projection manual provenance until DB Layout_* parity.
                continue
            rows.append(
                CatalogPlacementIssueRow(
                    candidate_id=candidate_id,
                    issue_code=CatalogPlacementIssueCode.CATALOG_VARIANT_NOT_IN_SLICE,
                    had_ref=True,
                    message="variant not in slice",
                )
            )
            continue
        try:
            expected = expected_footprint_coords(
                geometry.footprint_cells,
                anchor_coord=ref.anchor_coord,
                rotation=ref.rotation,
            )
        except CatalogTransformError:
            rows.append(
                CatalogPlacementIssueRow(
                    candidate_id=candidate_id,
                    issue_code=CatalogPlacementIssueCode.CATALOG_ANCHOR_TRANSFORM_ERROR,
                    had_ref=True,
                    message="transform error",
                )
            )
            continue
        if expected == candidate.occupied_cells:
            continue
        rows.append(
            CatalogPlacementIssueRow(
                candidate_id=candidate_id,
                issue_code=CatalogPlacementIssueCode.CATALOG_FOOTPRINT_MISMATCH,
                had_ref=True,
                message="footprint mismatch",
            )
        )
    return tuple(rows)


def _audit_counts_from_rows(
    rows: tuple[CatalogPlacementIssueRow, ...],
    committed_ids: tuple[str, ...],
    candidates_by_id: dict[str, BundleCandidate],
    *,
    mode: CatalogValidationMode,
) -> CatalogPlacementAudit:
    issue_code_set = {row.issue_code.value for row in rows}
    mismatch = sum(
        1 for row in rows if row.issue_code is CatalogPlacementIssueCode.CATALOG_FOOTPRINT_MISMATCH
    )
    unmapped = sum(
        1
        for row in rows
        if row.issue_code is CatalogPlacementIssueCode.CATALOG_VARIANT_MAPPING_MISSING
    )
    not_in_slice = sum(
        1
        for row in rows
        if row.issue_code is CatalogPlacementIssueCode.CATALOG_VARIANT_NOT_IN_SLICE
    )
    transform_error = sum(
        1
        for row in rows
        if row.issue_code is CatalogPlacementIssueCode.CATALOG_ANCHOR_TRANSFORM_ERROR
    )
    if any(row.issue_code is CatalogPlacementIssueCode.CATALOG_SLICE_MISSING for row in rows):
        return CatalogPlacementAudit(
            catalog_validation_mode=mode,
            checked_candidate_count=0,
            matched_candidate_count=0,
            mismatch_candidate_count=0,
            unmapped_candidate_count=0,
            not_in_slice_count=0,
            transform_error_count=0,
            issue_codes=tuple(sorted(issue_code_set)),
        )

    present_ids = [
        candidate_id
        for candidate_id in committed_ids
        if candidates_by_id.get(candidate_id) is not None
    ]
    classified_ids = {row.candidate_id for row in rows if row.candidate_id}
    matched = len(present_ids) - len(classified_ids)
    checked = len(present_ids)
    return CatalogPlacementAudit(
        catalog_validation_mode=mode,
        checked_candidate_count=checked,
        matched_candidate_count=matched,
        mismatch_candidate_count=mismatch,
        unmapped_candidate_count=unmapped,
        not_in_slice_count=not_in_slice,
        transform_error_count=transform_error,
        issue_codes=tuple(sorted(issue_code_set)),
    )


def audit_catalog_placements(
    committed_ids: tuple[str, ...],
    candidates_by_id: dict[str, BundleCandidate],
    catalog_slice: BuildingCatalogSlice | None,
    *,
    catalog_slice_hash: str | None = None,
    catalog_slice_version: str | None = None,
    mode: CatalogValidationMode = "observe_only",
) -> CatalogPlacementAudit:
    """Classify committed candidates against catalog geometry (observe-only by default)."""

    del catalog_slice_hash, catalog_slice_version  # reserved for step metrics wiring

    rows = classify_committed_catalog_placements(committed_ids, candidates_by_id, catalog_slice)
    return _audit_counts_from_rows(rows, committed_ids, candidates_by_id, mode=mode)


def catalog_placement_audit_metrics(
    audit: CatalogPlacementAudit,
    *,
    catalog_slice_hash: str | None,
    catalog_slice_version: str | None,
) -> dict[str, Any]:
    metrics: dict[str, Any] = {
        "catalog_validation_mode": audit.catalog_validation_mode,
        "checked_candidate_count": audit.checked_candidate_count,
        "matched_candidate_count": audit.matched_candidate_count,
        "mismatch_candidate_count": audit.mismatch_candidate_count,
        "unmapped_candidate_count": audit.unmapped_candidate_count,
        "not_in_slice_count": audit.not_in_slice_count,
        "transform_error_count": audit.transform_error_count,
        "issue_codes": list(audit.issue_codes),
    }
    if catalog_slice_hash is not None:
        metrics["catalog_slice_hash"] = catalog_slice_hash
    if catalog_slice_version is not None:
        metrics["catalog_slice_version"] = catalog_slice_version
    return metrics


__all__ = [
    "audit_catalog_placements",
    "catalog_placement_audit_metrics",
    "classify_committed_catalog_placements",
]
