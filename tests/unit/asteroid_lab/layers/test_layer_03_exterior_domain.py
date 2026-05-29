"""Layer 03 virtual exterior transport domain (contract + expansion P0 gate)."""

from __future__ import annotations

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.candidates import (
    RouteProbeStatus,
)
from django_apps.asteroid_lab.layers.contracts.exterior_transport_domain import (
    ExteriorTransportDomain,
)
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.transport_kind import (
    ResourceKind,
    TransportKind,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.expand import (
    expand_rim_bundle_candidates,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.exterior_domain import (
    build_exterior_transport_domain,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.project import (
    project_miner_seed_at_anchor,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.seed_catalog import (
    MinerSeedCatalog,
)
from django_apps.asteroid_lab.layers.shared.route_probe import immediate_route_probe
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.grid_contract import BBox
from tests.unit.asteroid_lab.layers.fixtures.layer_03_virtual_exterior_map import (
    virtual_exterior_complete_map,
    virtual_exterior_l2_plan,
    virtual_exterior_m0e_seed,
    virtual_exterior_route_goals,
)


def test_projection_does_not_emit_transport_stub_not_in_void() -> None:
    complete_map = virtual_exterior_complete_map()
    result = project_miner_seed_at_anchor(
        seed=virtual_exterior_m0e_seed(),
        anchor_coord=(5, 5),
        output_dir=Direction.W,
        resource_kind=ResourceKind.SHAPE,
        transport_kind=TransportKind.SHAPE_BELT,
        complete_map=complete_map,
    )
    assert result.candidate is not None
    assert result.reject_reason is None
    assert (3, 5) in result.candidate.transport_stub_cells
    assert (3, 5) not in complete_map.external_void_cells


def test_build_exterior_transport_domain_includes_virtual_stub_cells() -> None:
    complete_map = virtual_exterior_complete_map()
    seed = virtual_exterior_m0e_seed()
    projection = project_miner_seed_at_anchor(
        seed=seed,
        anchor_coord=(5, 5),
        output_dir=Direction.W,
        resource_kind=ResourceKind.SHAPE,
        transport_kind=TransportKind.SHAPE_BELT,
        complete_map=complete_map,
    )
    assert projection.candidate is not None
    candidate = projection.candidate
    route_goals = virtual_exterior_route_goals()
    domain = build_exterior_transport_domain(
        complete_map=complete_map,
        anchor_abs=(5, 5),
        transport_stub_cells=candidate.transport_stub_cells,
        route_goals=route_goals,
        route_probe_start=candidate.route_probe_start_coord,
    )
    assert candidate.transport_stub_cells <= domain.placeable_cells
    assert (2, 12) in domain.placeable_cells


def test_virtual_exterior_expansion_route_probe_succeeds() -> None:
    result = expand_rim_bundle_candidates(
        complete_map=virtual_exterior_complete_map(),
        exterior_plan=virtual_exterior_l2_plan(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        seed_catalog=MinerSeedCatalog.from_entries(virtual_exterior_m0e_seed()),
    )
    assert result.metrics.route_probe_attempt_count > 0
    assert result.metrics.normal_candidate_count > 0


def test_projection_allows_transport_stub_on_field() -> None:
    base = virtual_exterior_complete_map()
    complete_map = ReconstructionCompleteMap(
        cells=base.cells,
        field_cells=frozenset({(5, 5), (6, 5)}),
        shape_field_cell_count=2,
        fluid_field_cell_count=0,
        external_void_cells=base.external_void_cells,
        coord_frame=base.coord_frame,
    )
    seed = virtual_exterior_m0e_seed()
    result = project_miner_seed_at_anchor(
        seed=seed,
        anchor_coord=(5, 5),
        output_dir=Direction.E,
        resource_kind=ResourceKind.SHAPE,
        transport_kind=TransportKind.SHAPE_BELT,
        complete_map=complete_map,
    )
    assert result.candidate is not None
    assert result.reject_reason is None
    assert result.candidate.transport_stub_cells & complete_map.field_cells


def test_exterior_transport_domain_exposes_placeable_cells() -> None:
    domain = ExteriorTransportDomain(
        search_bbox=BBox(0, 10, 0, 10),
        blocked_field_cells=frozenset({(5, 5)}),
        placeable_cells=frozenset({(4, 5), (3, 5)}),
    )
    assert (4, 5) in domain.placeable_cells
    assert not hasattr(domain, "traversable_cells")


def test_probe_path_is_not_full_placeable_component() -> None:
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_placeable_flood_trap import (
        flood_trap_candidate,
        flood_trap_complete_map,
        flood_trap_goals,
    )

    candidate = flood_trap_candidate()
    complete_map = flood_trap_complete_map()
    domain = build_exterior_transport_domain(
        complete_map=complete_map,
        anchor_abs=candidate.anchor_coord,
        transport_stub_cells=candidate.transport_stub_cells,
        route_goals=flood_trap_goals(),
        route_probe_start=candidate.route_probe_start_coord,
    )
    probed = immediate_route_probe(
        candidate=candidate,
        route_goals=flood_trap_goals(),
        placeable_cells=domain.placeable_cells,
    )
    assert probed.route_probe_status == RouteProbeStatus.SUCCEEDED
    assert probed.route_probe_result is not None
    path_set = frozenset(probed.route_probe_result.path_coords)
    assert len(domain.placeable_cells) >= len(path_set) + 3
    assert path_set < domain.placeable_cells
    proposed = probed.route_probe_result.proposed_transport_cells(
        stub_cells=candidate.transport_stub_cells,
    )
    assert proposed == candidate.transport_stub_cells | path_set
    assert proposed != domain.placeable_cells
    assert probed.route_probe_result.path_coords[0] == candidate.route_probe_start_coord
    assert probed.route_probe_result.goal_coord == probed.route_probe_result.path_coords[-1]


def test_successful_candidate_keeps_seed_stub_count_after_probe() -> None:
    result = expand_rim_bundle_candidates(
        complete_map=virtual_exterior_complete_map(),
        exterior_plan=virtual_exterior_l2_plan(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        seed_catalog=MinerSeedCatalog.from_entries(virtual_exterior_m0e_seed()),
    )
    assert result.metrics.normal_candidate_count >= 1
    probed = result.normal_candidates[0]
    assert probed.route_probe_result is not None
    assert len(probed.candidate.transport_stub_cells) < 10
