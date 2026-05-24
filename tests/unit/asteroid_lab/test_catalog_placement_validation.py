"""Track D+ PR-2 — mapped-only fail-closed catalog placement validation."""

from __future__ import annotations

from django_apps.asteroid_lab.adapters.catalog_placement_validation import (
    validate_catalog_placements,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    SLICE_VERSION,
    BuildingCatalogSlice,
    VariantGeometryCatalog,
    VariantIdentity,
)
from django_apps.asteroid_lab.contracts.catalog_placement import (
    CardinalDirection,
    CatalogPlacementIssueCode,
    CatalogPlacementRef,
)
from django_apps.asteroid_lab.contracts.catalog_validation import ValidationSeverity
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    BuildingFootprintCell,
    TransportRegistryEntry,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.pattern_library import (
    build_pattern_library,
)
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind


def _catalog_slice(
    *,
    canonical_id: str = "bv:1",
    footprint: tuple[BuildingFootprintCell, ...] = (
        BuildingFootprintCell(0, 0, 0),
        BuildingFootprintCell(1, 0, 1),
    ),
) -> BuildingCatalogSlice:
    return BuildingCatalogSlice(
        slice_version=SLICE_VERSION,
        transport_registry=(TransportRegistryEntry("space_belt", "belt", canonical_id),),
        variants=(VariantIdentity(canonical_id, "miner_a"),),
        variant_geometries=(
            VariantGeometryCatalog(
                canonical_id=canonical_id,
                internal_name="miner_a",
                footprint_cells=footprint,
                connectors=(),
            ),
        ),
    )


def _candidate(
    *,
    candidate_id: str = "c1",
    occupied: frozenset[tuple[int, int]],
    ref: CatalogPlacementRef | None = None,
) -> BundleCandidate:
    pat = build_pattern_library()[0]
    return BundleCandidate(
        candidate_id=candidate_id,
        anchor_coord=(5, 7),
        pattern=pat,
        occupied_cells=occupied,
        output_stub=(9, 7),
        output_dir="E",
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=4,
        route_probe_cost=1,
        reachable=True,
        catalog_placement_ref=ref,
    )


def test_catalog_slice_missing_emits_warning_not_silent_pass() -> None:
    cand = _candidate(occupied=frozenset({(5, 7)}), ref=None)
    result = validate_catalog_placements(("c1",), {"c1": cand}, None)
    assert result.passed is True
    assert any(
        i.issue_code is CatalogPlacementIssueCode.CATALOG_SLICE_MISSING
        and i.severity is ValidationSeverity.WARNING
        for i in result.issues
    )


def test_mapped_mismatch_fails_validation() -> None:
    sl = _catalog_slice()
    ref = CatalogPlacementRef("bv:1", (5, 7), CardinalDirection.E)
    cand = _candidate(occupied=frozenset({(5, 7), (99, 99)}), ref=ref)
    result = validate_catalog_placements(("c1",), {"c1": cand}, sl)
    assert result.passed is False
    assert any(
        i.issue_code is CatalogPlacementIssueCode.CATALOG_FOOTPRINT_MISMATCH
        and i.severity is ValidationSeverity.ERROR
        for i in result.issues
    )


def test_mapped_match_passes_validation() -> None:
    sl = _catalog_slice()
    ref = CatalogPlacementRef("bv:1", (5, 7), CardinalDirection.E)
    occupied = frozenset({(5, 7), (6, 7)})
    cand = _candidate(occupied=occupied, ref=ref)
    result = validate_catalog_placements(("c1",), {"c1": cand}, sl)
    assert result.passed is True
    assert not any(i.severity is ValidationSeverity.ERROR for i in result.issues)


def test_unmapped_does_not_fail_validation() -> None:
    sl = _catalog_slice()
    cand = _candidate(occupied=frozenset({(99, 99)}), ref=None)
    result = validate_catalog_placements(("c1",), {"c1": cand}, sl)
    assert result.passed is True
    assert any(
        i.issue_code is CatalogPlacementIssueCode.CATALOG_VARIANT_MAPPING_MISSING
        and i.severity is ValidationSeverity.WARNING
        for i in result.issues
    )


def test_not_in_slice_with_ref_fails_validation() -> None:
    sl = _catalog_slice()
    ref = CatalogPlacementRef("bv:missing", (5, 7), CardinalDirection.E)
    cand = _candidate(occupied=frozenset({(5, 7)}), ref=ref)
    result = validate_catalog_placements(("c1",), {"c1": cand}, sl)
    assert result.passed is False


def test_no_free_string_issue_codes() -> None:
    sl = _catalog_slice()
    ref = CatalogPlacementRef("bv:1", (5, 7), CardinalDirection.E)
    cand = _candidate(occupied=frozenset({(5, 7), (99, 99)}), ref=ref)
    result = validate_catalog_placements(("c1",), {"c1": cand}, sl)
    for issue in result.issues:
        assert isinstance(issue.issue_code, CatalogPlacementIssueCode)
