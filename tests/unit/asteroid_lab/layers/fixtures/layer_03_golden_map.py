"""Golden 5×5 field map + minimal L2 plan for replay / assembler tests."""

from __future__ import annotations

from decimal import Decimal

from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.reconstruction.rim_topology import field_rim_cells
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import Coord
from shapez2_factory.application.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connection import (
    ExteriorConnectionPlan,
    ExteriorConnector,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)

_FIELD_ORIGIN = 2
_FIELD_SIZE = 5


def _field_cells() -> frozenset[Coord]:
    cells: set[Coord] = set()
    for x in range(_FIELD_ORIGIN, _FIELD_ORIGIN + _FIELD_SIZE):
        for y in range(_FIELD_ORIGIN, _FIELD_ORIGIN + _FIELD_SIZE):
            cells.add((x, y))
    return frozenset(cells)


def _external_void_cells(field: frozenset[Coord]) -> frozenset[Coord]:
    void: set[Coord] = set()
    for x, y in field:
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (nx, ny) not in field:
                void.add((nx, ny))
    void.add((8, 4))
    return frozenset(void)


def golden_5x5_complete_map() -> ReconstructionCompleteMap:
    field = _field_cells()
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field,
        shape_field_cell_count=len(field),
        fluid_field_cell_count=0,
        external_void_cells=_external_void_cells(field),
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def minimal_l2_plan_for_golden(*, goal_coord: Coord = (8, 4)) -> ExteriorConnectionPlan:
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
                connector_id="ext_conn_golden",
                void_coord=goal_coord,
                edge=CardinalEdge.EAST,
                layout_t="SpaceBelt_Forward",
                rotation=0,
                capacity_per_min=Decimal("1000"),
                coords=(goal_coord,),
                role=ExteriorConnectorRole.REQUIRED,
            ),
        ),
        unmet_reason=None,
    )


def expected_golden_rim_anchor_count() -> int:
    return len(field_rim_cells(_field_cells()))


__all__ = [
    "expected_golden_rim_anchor_count",
    "golden_5x5_complete_map",
    "minimal_l2_plan_for_golden",
]
