"""Projection compat metrics — Task 7 audit instrumentation."""

from __future__ import annotations

from django_apps.asteroid_lab.catalog.asteroid_equipment_projection import (
    list_equipment_placement_specs,
)
from django_apps.asteroid_lab.catalog.projection_compat_metrics import (
    committed_projection_audit_metrics,
    equipment_projection_metrics,
    reset_projection_compat_instrumentation,
    route_compat_instrumentation_count,
)
from django_apps.asteroid_lab.catalog.projection_source import ProjectionSourceKind
from django_apps.asteroid_lab.contracts.catalog_placement import (
    CardinalDirection,
    CatalogPlacementRef,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
)
from django_apps.asteroid_lab.adapters.catalog_candidate_placements import (
    build_catalog_placement_specs,
)
from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from tests.support.catalog_test_fixtures import build_minimal_test_catalog_slice
from tests.unit.asteroid_lab.test_catalog_placement_validation import _slice_with_variant


def test_equipment_projection_metrics_includes_source_kind_counts() -> None:
    sl = build_minimal_test_catalog_slice()
    metrics = equipment_projection_metrics(sl, transport_kind=TransportKind.SHAPE_BELT)
    assert metrics["equipment_projection_spec_count"] == 16
    assert "projection_source_kind_counts" in metrics
    assert metrics["projection_source_kind_counts"]["game_data_canon"] == 16


def test_committed_projection_audit_reports_source_kind() -> None:
    footprint = (BuildingFootprintCell(0, 0, 0), BuildingFootprintCell(1, 0, 1))
    connectors = (BuildingConnectorSnapshot(0, "output", "East", "Regular", 1, 0, 0),)
    sl = _slice_with_variant(
        canonical_id="bv:shape_miner",
        internal_name="Layout_ShapeMiner",
        footprint=footprint,
        connectors=connectors,
    )
    spec = next(
        s
        for s in build_catalog_placement_specs(sl, transport_kind=TransportKind.SHAPE_BELT)
        if s.rotation is CardinalDirection.E and s.pattern_id.endswith("_ext0")
    )
    pat = BundlePattern(
        pattern_id=spec.pattern_id,
        extension_count=len(spec.extension_offsets),
        occupied_offsets=spec.occupied_offsets,
        extractor_offset=spec.extractor_offset,
        extension_offsets=spec.extension_offsets,
        output_dir=spec.output_dir,
        fixed_output_transport_offset=spec.fixed_output_transport_offset,
        output_stub_offset=spec.output_stub_offset,
        throughput_factor=spec.throughput_factor,
        topology_kind=spec.topology_kind,
    )
    ref = CatalogPlacementRef(spec.canonical_id, (5, 7), CardinalDirection.E)
    cand = BundleCandidate(
        candidate_id="c1",
        anchor_coord=(5, 7),
        pattern=pat,
        occupied_cells=frozenset({(5, 7)}),
        output_stub=(7, 7),
        output_dir="E",
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=4,
        route_probe_cost=1,
        reachable=True,
        catalog_placement_ref=ref,
    )
    reset_projection_compat_instrumentation()
    metrics = committed_projection_audit_metrics(
        sl,
        transport_kind=TransportKind.SHAPE_BELT,
        committed_ids=("c1",),
        candidates_by_id={"c1": cand},
        include_route_instrumentation=False,
    )
    assert metrics["temporary_compat_count"] == 0
    assert metrics["committed_projection_audit"][0]["projection_source_kind"] == (
        ProjectionSourceKind.GAME_DATA_CANON.value
    )


def test_route_instrumentation_resets_per_run() -> None:
    from django_apps.asteroid_lab.catalog.asteroid_transport_projection import (
        resolve_route_tile,
    )

    reset_projection_compat_instrumentation()
    assert route_compat_instrumentation_count() == 0
    resolve_route_tile(
        transport_kind=TransportKind.SHAPE_BELT,
        incoming_dir=0,
        outgoing_dir=3,
    )
    assert route_compat_instrumentation_count() == 1
    reset_projection_compat_instrumentation()
    assert route_compat_instrumentation_count() == 0


def test_canon_manual_equipment_counts_as_temporary_compat_for_slice_only() -> None:
    sl = _slice_with_variant(
        canonical_id="bv:internal",
        internal_name="BeltDefaultForwardInternalVariant",
    )
    specs = list_equipment_placement_specs(sl, transport_kind=TransportKind.SHAPE_BELT)
    assert any(s.source_kind is ProjectionSourceKind.CANON_MANUAL for s in specs)
    metrics = equipment_projection_metrics(sl, transport_kind=TransportKind.SHAPE_BELT)
    assert metrics["temporary_compat_count_equipment"] == 0
