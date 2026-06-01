"""W5: L4 routing ignores L3 route_probe_path (PR-L4-2)."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

from shapez2_factory.application.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
    ExteriorConnector,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    CommittedRimSeedPlacement,
    RimGreedyMetrics,
    build_empty_integrated_rim_greedy_result,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.run import (
    run_layer_04_transport_routing,
)
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import (
    build_rect_field_with_void_shell,
)


def _exterior_plan(connector_void: tuple[int, int]) -> ExteriorConnectionPlan:
    conn = ExteriorConnector(
        connector_id="ext_conn_00",
        void_coord=connector_void,
        edge=CardinalEdge.WEST,
        layout_t="SpaceBelt_Forward",
        rotation=0,
        capacity_per_min=Decimal("5760"),
        coords=(connector_void,),
        role=ExteriorConnectorRole.REQUIRED,
    )
    return ExteriorConnectionPlan(
        transport_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        planning_target_per_min=Decimal("5760"),
        per_connector_capacity_per_min=Decimal("5760"),
        required_connector_count=1,
        reference_connector_count=1,
        spare_connector_count=0,
        planned_connectors=(conn,),
        unmet_reason=None,
    )


def _rim_with_probe(stub: tuple[int, int], probe: tuple[tuple[int, int], ...]):
    placement = CommittedRimSeedPlacement(
        placement_id="p1",
        variant_id="v1",
        anchor=(0, 0),
        output_dir="W",
        seed_id="gene_a",
        miner_cells=frozenset({(0, 0)}),
        extension_cells=frozenset(),
        m_output_stub=stub,
        throughput_factor=4,
        route_probe_path=probe,
    )
    return replace(
        build_empty_integrated_rim_greedy_result(),
        committed_placements=(placement,),
        metrics=RimGreedyMetrics(committed_placement_count=1),
    )


def test_routing_unchanged_when_probe_paths_cleared() -> None:
    cm = build_rect_field_with_void_shell(width=4, height=4, void_pad=2)
    connector_void = (-1, 0)
    assert connector_void in cm.external_void_cells
    stub = (-1, 1)
    assert stub in cm.external_void_cells
    exterior = _exterior_plan(connector_void)

    rim_with_probe = _rim_with_probe(stub, ((-1, 1), (0, 1), (1, 1), connector_void))
    rim_cleared = _rim_with_probe(stub, ())

    plan_a = run_layer_04_transport_routing(
        complete_map=cm,
        exterior_plan=exterior,
        rim_result=rim_with_probe,
        resource_kind="shape",
    )
    plan_b = run_layer_04_transport_routing(
        complete_map=cm,
        exterior_plan=exterior,
        rim_result=rim_cleared,
        resource_kind="shape",
    )
    assert plan_a.routes == plan_b.routes
    assert plan_a.failures == plan_b.failures
    assert len(plan_a.routes) == 1
