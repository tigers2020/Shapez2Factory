"""Layer 03 weighted transport routing — contract and projection tests."""

from __future__ import annotations

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.candidates import (
    CandidateRejectReason,
    make_bundle_candidate_for_test,
)
from django_apps.asteroid_lab.layers.contracts.transport_kind import (
    ResourceKind,
    TransportKind,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.project import (
    project_miner_seed_at_anchor,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from tests.unit.asteroid_lab.layers.fixtures.layer_03_virtual_exterior_map import (
    virtual_exterior_m0e_seed,
)


def test_candidate_reject_reason_includes_transport_collides_with_mining_equipment() -> None:
    assert hasattr(CandidateRejectReason, "TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT")
    assert (
        CandidateRejectReason.TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT.value
        == "transport_collides_with_mining_equipment"
    )


def test_bundle_candidate_allows_route_probe_start_not_in_transport_stubs() -> None:
    candidate = make_bundle_candidate_for_test(
        anchor_coord=(7, 3),
        mining_occupied_cells=frozenset({(7, 3)}),
        transport_stub_cells=frozenset(),
        route_probe_start_coord=(8, 3),
    )
    assert candidate.route_probe_start_coord == (8, 3)
    assert candidate.route_probe_start_coord not in candidate.transport_stub_cells


def test_bundle_candidate_rejects_route_probe_start_on_mining_cell() -> None:
    import pytest

    with pytest.raises(
        ValueError,
        match="route_probe_start_coord must not be in mining_occupied_cells",
    ):
        make_bundle_candidate_for_test(
            anchor_coord=(7, 3),
            mining_occupied_cells=frozenset({(7, 3)}),
            transport_stub_cells=frozenset(),
            route_probe_start_coord=(7, 3),
        )


def test_projection_allows_transport_stub_on_field() -> None:
    complete_map = ReconstructionCompleteMap(
        cells=(),
        field_cells=frozenset({(5, 5), (6, 5)}),
        shape_field_cell_count=2,
        fluid_field_cell_count=0,
        external_void_cells=frozenset({(4, 5)}),
        coord_frame=CoordFrame.ISLAND_RAW,
    )
    result = project_miner_seed_at_anchor(
        seed=virtual_exterior_m0e_seed(),
        anchor_coord=(5, 5),
        output_dir=Direction.E,
        resource_kind=ResourceKind.SHAPE,
        transport_kind=TransportKind.SHAPE_BELT,
        complete_map=complete_map,
    )
    assert result.candidate is not None
    assert result.reject_reason is None
    assert result.candidate.transport_stub_cells & complete_map.field_cells


def test_projection_does_not_emit_transport_collides_with_field() -> None:
    complete_map = ReconstructionCompleteMap(
        cells=(),
        field_cells=frozenset({(5, 5), (6, 5)}),
        shape_field_cell_count=2,
        fluid_field_cell_count=0,
        external_void_cells=frozenset({(4, 5)}),
        coord_frame=CoordFrame.ISLAND_RAW,
    )
    result = project_miner_seed_at_anchor(
        seed=virtual_exterior_m0e_seed(),
        anchor_coord=(5, 5),
        output_dir=Direction.E,
        resource_kind=ResourceKind.SHAPE,
        transport_kind=TransportKind.SHAPE_BELT,
        complete_map=complete_map,
    )
    assert result.reject_reason != CandidateRejectReason.TRANSPORT_COLLIDES_WITH_FIELD


def test_projection_rejects_transport_overlapping_mining() -> None:
    decoded_json = {
        "BP": {
            "Entries": [
                {"T": "Layout_ShapeMiner", "X": 0, "Y": 0, "R": 0},
                {"T": "SpaceBelt_Forward", "X": 0, "Y": 0, "R": 0},
            ],
        },
    }
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.seed_catalog import (
        MinerSeedEntry,
    )

    seed = MinerSeedEntry(
        gene_key="belt_on_miner",
        pattern_id="overlap",
        intrinsic_priority_rank=1,
        throughput_factor=16,
        topology_signature="topo_overlap",
        decoded_json=decoded_json,
    )
    complete_map = ReconstructionCompleteMap(
        cells=(),
        field_cells=frozenset({(5, 5)}),
        shape_field_cell_count=1,
        fluid_field_cell_count=0,
        external_void_cells=frozenset(),
        coord_frame=CoordFrame.ISLAND_RAW,
    )
    result = project_miner_seed_at_anchor(
        seed=seed,
        anchor_coord=(5, 5),
        output_dir=Direction.E,
        resource_kind=ResourceKind.SHAPE,
        transport_kind=TransportKind.SHAPE_BELT,
        complete_map=complete_map,
    )
    assert result.candidate is None
    assert result.reject_reason == CandidateRejectReason.TRANSPORT_COLLIDES_WITH_MINING_EQUIPMENT


def test_weighted_domain_field_cost_exceeds_exterior() -> None:
    from django_apps.asteroid_lab.layers.contracts.weighted_transport_route_domain import (
        EXTERIOR_ROUTE_COST,
        FIELD_ROUTE_COST,
        WeightedTransportRouteDomain,
    )
    from django_apps.asteroid_lab.snapshots.grid_contract import BBox

    domain = WeightedTransportRouteDomain(
        search_bbox=BBox(0, 5, 0, 5),
        blocked_cells=frozenset(),
        walkable_cells=frozenset({(1, 1), (2, 1)}),
        field_cost_cells=frozenset({(2, 1)}),
    )
    assert domain.step_cost((1, 1)) == EXTERIOR_ROUTE_COST
    assert domain.step_cost((2, 1)) == FIELD_ROUTE_COST
    assert domain.step_cost((9, 9)) is None


def test_weighted_route_probe_prefers_exterior_over_field() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import RouteProbeStatus
    from django_apps.asteroid_lab.layers.shared.route_probe import weighted_route_probe
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_weighted_route_maps import (
        exterior_preferred_probe_setup,
    )

    complete_map, goals, candidate, domain = exterior_preferred_probe_setup()
    probed = weighted_route_probe(
        candidate=candidate,
        route_goals=goals,
        domain=domain,
        field_cells=complete_map.field_cells,
    )
    assert probed.route_probe_status == RouteProbeStatus.SUCCEEDED
    assert probed.route_probe_result is not None
    assert probed.route_probe_result.field_route_cell_count == 0


def test_weighted_route_probe_uses_field_when_only_field_route_exists() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import RouteProbeStatus
    from django_apps.asteroid_lab.layers.shared.route_probe import weighted_route_probe
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_weighted_route_maps import (
        field_only_probe_setup,
    )

    complete_map, goals, candidate, domain = field_only_probe_setup()
    probed = weighted_route_probe(
        candidate=candidate,
        route_goals=goals,
        domain=domain,
        field_cells=complete_map.field_cells,
    )
    assert probed.route_probe_status == RouteProbeStatus.SUCCEEDED
    assert probed.route_probe_result is not None
    assert probed.route_probe_result.field_route_cell_count > 0


def test_route_probe_without_preinstalled_belt_at_entry() -> None:
    from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
    from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.expand import (
        expand_rim_bundle_candidates,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_weighted_route_maps import (
        no_stub_entry_complete_map,
        no_stub_entry_l2_plan,
        no_stub_miner_only_catalog,
    )

    result = expand_rim_bundle_candidates(
        complete_map=no_stub_entry_complete_map(),
        exterior_plan=no_stub_entry_l2_plan(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        seed_catalog=no_stub_miner_only_catalog(),
    )
    assert result.metrics.route_probe_attempt_count > 0
    counts = dict(result.metrics.reject_reason_counts)
    assert counts.get("local_geometry_invalid.probe_start_not_transport", 0) == 0
    assert counts.get("transport_collides_with_field", 0) == 0
