"""Track D+ — catalog placement audit taxonomy tests."""

from __future__ import annotations

from django_apps.asteroid_lab.adapters.catalog_placement_audit import (
    audit_catalog_placements,
    catalog_placement_audit_metrics,
)
from django_apps.asteroid_lab.catalog.projection_compat_metrics import (
    committed_projection_audit_metrics,
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


def test_audit_skips_when_catalog_slice_none() -> None:
    audit = audit_catalog_placements(("c1",), {"c1": _candidate(occupied=frozenset())}, None)
    assert audit.checked_candidate_count == 0
    assert audit.catalog_validation_mode == "observe_only"


def test_audit_unmapped_when_ref_missing() -> None:
    sl = _catalog_slice()
    cand = _candidate(occupied=frozenset({(5, 7), (6, 7)}), ref=None)
    audit = audit_catalog_placements(("c1",), {"c1": cand}, sl)
    assert audit.unmapped_candidate_count == 1
    assert CatalogPlacementIssueCode.CATALOG_VARIANT_MAPPING_MISSING.value in audit.issue_codes


def test_audit_matched_when_footprint_aligns() -> None:
    sl = _catalog_slice()
    ref = CatalogPlacementRef("bv:1", (5, 7), CardinalDirection.E)
    occupied = frozenset({(5, 7), (6, 7)})
    cand = _candidate(occupied=occupied, ref=ref)
    audit = audit_catalog_placements(("c1",), {"c1": cand}, sl)
    assert audit.matched_candidate_count == 1
    assert audit.mismatch_candidate_count == 0


def test_audit_mismatch_when_footprint_differs() -> None:
    sl = _catalog_slice()
    ref = CatalogPlacementRef("bv:1", (5, 7), CardinalDirection.E)
    cand = _candidate(occupied=frozenset({(5, 7), (99, 99)}), ref=ref)
    audit = audit_catalog_placements(("c1",), {"c1": cand}, sl)
    assert audit.mismatch_candidate_count == 1
    assert CatalogPlacementIssueCode.CATALOG_FOOTPRINT_MISMATCH.value in audit.issue_codes


def test_audit_not_in_slice_when_canonical_id_unknown() -> None:
    sl = _catalog_slice()
    ref = CatalogPlacementRef("bv:missing", (5, 7), CardinalDirection.E)
    cand = _candidate(occupied=frozenset({(5, 7)}), ref=ref)
    audit = audit_catalog_placements(("c1",), {"c1": cand}, sl)
    assert audit.not_in_slice_count == 1
    assert CatalogPlacementIssueCode.CATALOG_VARIANT_NOT_IN_SLICE.value in audit.issue_codes


def test_audit_metrics_include_temporary_compat_count() -> None:
    from tests.support.catalog_test_fixtures import build_minimal_test_catalog_slice

    sl = build_minimal_test_catalog_slice()
    audit = audit_catalog_placements((), {}, sl)
    metrics = catalog_placement_audit_metrics(audit, catalog_slice_hash="h1", catalog_slice_version="v1")
    metrics.update(
        committed_projection_audit_metrics(
            sl,
            transport_kind=TransportKind.SHAPE_BELT,
            committed_ids=(),
            candidates_by_id={},
            include_route_instrumentation=False,
        )
    )
    assert "temporary_compat_count" in metrics
    assert "projection_source_kind_counts" in metrics
    assert "committed_projection_audit" in metrics


def test_audit_transform_error_on_empty_footprint_in_slice() -> None:
    sl = _catalog_slice(footprint=())
    ref = CatalogPlacementRef("bv:1", (5, 7), CardinalDirection.E)
    cand = _candidate(occupied=frozenset({(5, 7)}), ref=ref)
    audit = audit_catalog_placements(("c1",), {"c1": cand}, sl)
    assert audit.transform_error_count == 1
    assert CatalogPlacementIssueCode.CATALOG_ANCHOR_TRANSFORM_ERROR.value in audit.issue_codes
