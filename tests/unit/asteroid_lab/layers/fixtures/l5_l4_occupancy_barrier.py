"""Named fixture: L4 interior fill blocks the shortest L5 void choke."""

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
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord
from tests.unit.asteroid_lab.layers.helpers.l02_complete_map_fixtures import make_complete_map

L5_L4_CONNECTOR: Coord = (-1, 0)
L5_L4_STUB: Coord = (2, 0)
L5_L4_MINER: Coord = (3, 0)
L5_L4_CHOKE_VOID: Coord = (1, 0)
L5_L4_WEST_VOID: Coord = (0, 0)
L5_L4_SOUTH_DETOUR: tuple[Coord, ...] = (
    (2, 1),
    (1, 1),
    (0, 1),
    (-1, 1),
)


def l5_l4_occupancy_barrier_basic_map():
    """West connector; east rim miner; y=0 void choke plus optional south detour."""

    field = frozenset({L5_L4_MINER})
    void = frozenset(
        {
            L5_L4_CONNECTOR,
            L5_L4_WEST_VOID,
            L5_L4_CHOKE_VOID,
            L5_L4_STUB,
            *L5_L4_SOUTH_DETOUR,
        }
    )
    return make_complete_map(field_cells=field, external_void_cells=void)


def l5_l4_occupancy_barrier_no_detour_map():
    """Choke-only west void corridor (no south detour row)."""

    field = frozenset({L5_L4_MINER})
    void = frozenset(
        {
            L5_L4_CONNECTOR,
            L5_L4_WEST_VOID,
            L5_L4_CHOKE_VOID,
            L5_L4_STUB,
        }
    )
    return make_complete_map(field_cells=field, external_void_cells=void)


def l5_l4_occupancy_barrier_exterior_plan() -> ExteriorConnectionPlan:
    connector = ExteriorConnector(
        connector_id="l5_l4_west",
        void_coord=L5_L4_CONNECTOR,
        edge=CardinalEdge.WEST,
        layout_t="SpaceBelt_Forward",
        rotation=0,
        capacity_per_min=Decimal("5760"),
        coords=(L5_L4_CONNECTOR,),
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
        planned_connectors=(connector,),
        unmet_reason=None,
    )


def l5_l4_occupancy_barrier_rim_result():
    placement = CommittedRimSeedPlacement(
        placement_id="l5_l4_p0",
        variant_id="v1",
        anchor=L5_L4_MINER,
        output_dir="W",
        seed_id="gene_a",
        miner_cells=frozenset({L5_L4_MINER}),
        extension_cells=frozenset(),
        m_output_stub=L5_L4_STUB,
        throughput_factor=4,
        route_probe_path=(),
    )
    return replace(
        build_empty_integrated_rim_greedy_result(),
        committed_placements=(placement,),
        metrics=RimGreedyMetrics(committed_placement_count=1),
    )


__all__ = [
    "L5_L4_CHOKE_VOID",
    "L5_L4_CONNECTOR",
    "L5_L4_MINER",
    "L5_L4_SOUTH_DETOUR",
    "L5_L4_STUB",
    "L5_L4_WEST_VOID",
    "l5_l4_occupancy_barrier_basic_map",
    "l5_l4_occupancy_barrier_exterior_plan",
    "l5_l4_occupancy_barrier_no_detour_map",
    "l5_l4_occupancy_barrier_rim_result",
]
