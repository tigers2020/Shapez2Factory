"""Synthetic map: belt stubs outside finite external_void_cells but not on field.

Single field cell at (5, 5); external_void_cells is minimal (only (4, 5)).
L2 connector goal at (2, 12) — outside pre-existing void corridor.
m0e belt west: stubs (4,5), (3,5), (2,5); (2,5) is virtual exterior.
"""

from __future__ import annotations

from decimal import Decimal

from django_apps.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from django_apps.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
    ExteriorConnector,
)
from django_apps.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from django_apps.asteroid_lab.layers.contracts.route_goal import build_layer03_route_goals
from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.seed_catalog import (
    MinerSeedEntry,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

_ANCHOR: Coord = (5, 5)
_VOID_WEST: Coord = (4, 5)


def _field_cells() -> frozenset[Coord]:
    return frozenset({_ANCHOR})


def virtual_exterior_complete_map() -> ReconstructionCompleteMap:
    field = _field_cells()
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field,
        shape_field_cell_count=len(field),
        fluid_field_cell_count=0,
        external_void_cells=frozenset({_VOID_WEST}),
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def virtual_exterior_l2_plan() -> ExteriorConnectionPlan:
    goal_coord: Coord = (2, 12)
    return ExteriorConnectionPlan(
        transport_kind="shape",
        terrain_upper_bound_per_min=Decimal("10000"),
        planning_target_per_min=Decimal("5000"),
        per_connector_capacity_per_min=Decimal("1000"),
        required_connector_count=1,
        reference_connector_count=1,
        spare_connector_count=0,
        planned_connectors=(
            ExteriorConnector(
                connector_id="ext_conn_virtual",
                void_coord=goal_coord,
                edge=CardinalEdge.NORTH,
                layout_t="SpaceBelt_Forward",
                rotation=0,
                capacity_per_min=Decimal("1000"),
                coords=(goal_coord,),
                role=ExteriorConnectorRole.REQUIRED,
            ),
        ),
        unmet_reason=None,
    )


def virtual_exterior_route_goals():
    return build_layer03_route_goals(
        virtual_exterior_l2_plan(),
        transport_kind=TransportKind.SHAPE_BELT,
    )


def _m0e_decoded_json() -> dict[str, object]:
    return {
        "BP": {
            "Entries": [
                {"T": "Layout_ShapeMiner", "X": 0, "Y": 0, "R": 0},
                {"T": "SpaceBelt_Forward", "X": 1, "Y": 0, "R": 0},
                {"T": "SpaceBelt_Forward", "X": 2, "Y": 0, "R": 0},
                {"T": "SpaceBelt_Forward", "X": 3, "Y": 0, "R": 0},
            ],
        },
    }


def virtual_exterior_m0e_seed() -> MinerSeedEntry:
    return MinerSeedEntry(
        gene_key="miner_seed_m0e_virtual",
        pattern_id="m0e_01",
        intrinsic_priority_rank=17,
        throughput_factor=16,
        topology_signature="topo_virtual_exterior",
        decoded_json=_m0e_decoded_json(),
    )


__all__ = [
    "virtual_exterior_complete_map",
    "virtual_exterior_l2_plan",
    "virtual_exterior_m0e_seed",
    "virtual_exterior_route_goals",
]
