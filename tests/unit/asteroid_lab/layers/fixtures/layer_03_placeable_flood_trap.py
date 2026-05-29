"""4×4 field block + wide exterior placeable component (connectivity-split tests).

placeable component is much larger than the shortest BFS path from stub to goal.
"""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import make_bundle_candidate_for_test
from django_apps.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from django_apps.asteroid_lab.layers.contracts.route_goal import RouteGoal, RouteGoalKind
from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

_FIELD_X0 = 10
_FIELD_Y0 = 10
_FIELD_SIZE = 4
_PROBE_START: Coord = (8, 10)
_GOAL: Coord = (20, 10)


def _field_cells() -> frozenset[Coord]:
    cells: set[Coord] = set()
    for x in range(_FIELD_X0, _FIELD_X0 + _FIELD_SIZE):
        for y in range(_FIELD_Y0, _FIELD_Y0 + _FIELD_SIZE):
            cells.add((x, y))
    return frozenset(cells)


def flood_trap_complete_map() -> ReconstructionCompleteMap:
    field = _field_cells()
    west_corridor = frozenset((x, _PROBE_START[1]) for x in range(5, _FIELD_X0))
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field,
        shape_field_cell_count=len(field),
        fluid_field_cell_count=0,
        external_void_cells=west_corridor,
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def flood_trap_goals() -> tuple[RouteGoal, ...]:
    return (
        RouteGoal(
            goal_id="ext_conn_trap",
            kind=RouteGoalKind.EXTERIOR_CONNECTOR_VOID,
            coord=_GOAL,
            transport_kind=TransportKind.SHAPE_BELT,
            priority=0,
            connector_role=ExteriorConnectorRole.REQUIRED,
        ),
    )


def flood_trap_candidate():
    anchor: Coord = (_FIELD_X0, _FIELD_Y0)
    return make_bundle_candidate_for_test(
        gene_key="flood_trap_stub",
        anchor_coord=anchor,
        route_probe_start_coord=_PROBE_START,
        transport_stub_cells=frozenset({_PROBE_START}),
        mining_occupied_cells=frozenset({anchor}),
    )


__all__ = [
    "flood_trap_candidate",
    "flood_trap_complete_map",
    "flood_trap_goals",
]
