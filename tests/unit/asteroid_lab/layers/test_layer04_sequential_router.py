"""Sequential merge-aware Layer 04 router (PR-L4-3)."""

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
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    Layer04FailureReason,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    CommittedRimSeedPlacement,
    RimGreedyMetrics,
    build_empty_integrated_rim_greedy_result,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.sequential_router import (  # noqa: E501
    route_layer04_sequential,
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


def _placement(
    placement_id: str,
    stub: tuple[int, int],
    load_m: int,
) -> CommittedRimSeedPlacement:
    return CommittedRimSeedPlacement(
        placement_id=placement_id,
        variant_id="v1",
        anchor=(0, 0),
        output_dir="W",
        seed_id="gene_a",
        miner_cells=frozenset({(0, 0)}),
        extension_cells=frozenset(),
        m_output_stub=stub,
        throughput_factor=load_m,
        route_probe_path=(),
    )


def test_second_source_overflows_single_connector_capacity() -> None:
    cm = build_rect_field_with_void_shell(width=4, height=4, void_pad=2)
    connector_void = (-1, 0)
    exterior = _exterior_plan(connector_void)
    rim = replace(
        build_empty_integrated_rim_greedy_result(),
        committed_placements=(
            _placement("p1", (-1, 1), 8),
            _placement("p2", (-1, 2), 8),
        ),
        metrics=RimGreedyMetrics(committed_placement_count=2),
    )
    plan = route_layer04_sequential(
        complete_map=cm,
        exterior_plan=exterior,
        rim_result=rim,
        resource_kind="shape",
    )
    assert len(plan.routes) == 1
    assert any(f.reason is Layer04FailureReason.CAPACITY_OVERFLOW for f in plan.failures)


def test_routes_populate_group_summaries() -> None:
    cm = build_rect_field_with_void_shell(width=4, height=4, void_pad=2)
    connector_void = (-1, 0)
    exterior = _exterior_plan(connector_void)
    rim = replace(
        build_empty_integrated_rim_greedy_result(),
        committed_placements=(_placement("p1", (-1, 1), 4),),
        metrics=RimGreedyMetrics(committed_placement_count=1),
    )
    plan = route_layer04_sequential(
        complete_map=cm,
        exterior_plan=exterior,
        rim_result=rim,
        resource_kind="shape",
    )
    assert len(plan.routes) == 1
    assert len(plan.groups) == 1
    assert plan.groups[0].used_m == 4
    assert plan.groups[0].capacity_m == 12
