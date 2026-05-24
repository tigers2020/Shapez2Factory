"""Observe-only catalog placement audit (Track D+ PR-1)."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.adapters.catalog_geometry_transform import (
    CatalogTransformError,
    expected_footprint_coords,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    BuildingCatalogSlice,
    VariantGeometryCatalog,
)
from django_apps.asteroid_lab.contracts.catalog_placement import (
    CatalogPlacementAudit,
    CatalogPlacementIssueCode,
    CatalogPlacementRef,
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


def audit_catalog_placements(
    committed_ids: tuple[str, ...],
    candidates_by_id: dict[str, BundleCandidate],
    catalog_slice: BuildingCatalogSlice | None,
    *,
    catalog_slice_hash: str | None = None,
    catalog_slice_version: str | None = None,
) -> CatalogPlacementAudit:
    """Classify committed candidates against catalog geometry (observe-only)."""

    del catalog_slice_hash, catalog_slice_version  # reserved for step metrics wiring

    issue_code_set: set[str] = set()
    matched = 0
    mismatch = 0
    unmapped = 0
    not_in_slice = 0
    transform_error = 0

    if catalog_slice is None:
        return CatalogPlacementAudit(
            catalog_validation_mode="observe_only",
            checked_candidate_count=0,
            matched_candidate_count=0,
            mismatch_candidate_count=0,
            unmapped_candidate_count=0,
            not_in_slice_count=0,
            transform_error_count=0,
            issue_codes=(),
        )

    for candidate_id in committed_ids:
        candidate = candidates_by_id.get(candidate_id)
        if candidate is None:
            continue
        ref: CatalogPlacementRef | None = candidate.catalog_placement_ref
        if ref is None:
            unmapped += 1
            issue_code_set.add(
                CatalogPlacementIssueCode.CATALOG_VARIANT_MAPPING_MISSING.value
            )
            continue

        geometry = _variant_geometry(ref.canonical_id, catalog_slice)
        if geometry is None:
            not_in_slice += 1
            issue_code_set.add(
                CatalogPlacementIssueCode.CATALOG_VARIANT_NOT_IN_SLICE.value
            )
            continue

        try:
            expected = expected_footprint_coords(
                geometry.footprint_cells,
                anchor_coord=ref.anchor_coord,
                rotation=ref.rotation,
            )
        except CatalogTransformError:
            transform_error += 1
            issue_code_set.add(
                CatalogPlacementIssueCode.CATALOG_ANCHOR_TRANSFORM_ERROR.value
            )
            continue

        if expected == candidate.occupied_cells:
            matched += 1
        else:
            mismatch += 1
            issue_code_set.add(
                CatalogPlacementIssueCode.CATALOG_FOOTPRINT_MISMATCH.value
            )

    checked = matched + mismatch + unmapped + not_in_slice + transform_error
    return CatalogPlacementAudit(
        catalog_validation_mode="observe_only",
        checked_candidate_count=checked,
        matched_candidate_count=matched,
        mismatch_candidate_count=mismatch,
        unmapped_candidate_count=unmapped,
        not_in_slice_count=not_in_slice,
        transform_error_count=transform_error,
        issue_codes=tuple(sorted(issue_code_set)),
    )


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
]
