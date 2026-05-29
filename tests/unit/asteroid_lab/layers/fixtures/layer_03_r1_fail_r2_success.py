"""R1 picks N first; EEEMB seed needs output_dir=E at anchor (7,3)."""

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
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import Coord
from tests.unit.asteroid_lab.layers.fixtures.layer_03_eeemb_projection import (
    eeemb_seed_entry,
)

_ANCHOR: Coord = (7, 3)
_GOAL: Coord = (7, 2)


def r1_fail_r2_success_complete_map() -> ReconstructionCompleteMap:
    field = frozenset({(4, 3), (5, 3), (6, 3), (7, 3)})
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field,
        shape_field_cell_count=len(field),
        fluid_field_cell_count=0,
        external_void_cells=frozenset({_GOAL, (8, 3), (7, 4)}),
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def r1_fail_r2_success_l2_plan() -> ExteriorConnectionPlan:
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
                connector_id="ext_conn_r2_lite",
                void_coord=_GOAL,
                edge=CardinalEdge.NORTH,
                layout_t="SpaceBelt_Forward",
                rotation=0,
                capacity_per_min=Decimal("1000"),
                coords=(_GOAL,),
                role=ExteriorConnectorRole.REQUIRED,
            ),
        ),
        unmet_reason=None,
    )


def r1_fail_r2_success_route_goals():
    return build_layer03_route_goals(
        r1_fail_r2_success_l2_plan(),
        transport_kind=TransportKind.SHAPE_BELT,
    )


__all__ = [
    "eeemb_seed_entry",
    "r1_fail_r2_success_complete_map",
    "r1_fail_r2_success_l2_plan",
    "r1_fail_r2_success_route_goals",
]
