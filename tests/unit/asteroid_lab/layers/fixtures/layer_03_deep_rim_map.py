"""Deep / shallow rim field maps for m3e_01 (miner + up to 3 extensions) tests.

Lab raw grid convention (``cardinal_map``): north decreases ``y``. A north-rim
miner anchor at ``(x, y0)`` has its output stub in void at ``(x, y0 - 1)`` and
its extensions extend inward (south, increasing ``y``) at ``(x, y0 + 1..3)``.
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
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.snapshots.coord_frames import CoordFrame
from django_apps.asteroid_lab.snapshots.grid_contract import Coord


def _box_field(x0: int, x1: int, y0: int, y1: int) -> frozenset[Coord]:
    """Inclusive rectangular field block."""
    return frozenset((x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1))


def _void_ring(field: frozenset[Coord], *, pad: int = 2) -> frozenset[Coord]:
    """Connected void box around the field bbox (expanded by ``pad``), minus field."""
    xs = [x for x, _ in field]
    ys = [y for _, y in field]
    x0, x1 = min(xs) - pad, max(xs) + pad
    y0, y1 = min(ys) - pad, max(ys) + pad
    box = {(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}
    return frozenset(box - field)


def _complete_map(field: frozenset[Coord]) -> ReconstructionCompleteMap:
    return ReconstructionCompleteMap(
        cells=(),
        field_cells=field,
        shape_field_cell_count=len(field),
        fluid_field_cell_count=0,
        external_void_cells=_void_ring(field),
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def _plan(*, goal_coord: Coord) -> ExteriorConnectionPlan:
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
                connector_id="ext_conn_deep_rim",
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


# Deep field: 5 wide x 6 tall (x 0..4, y 0..5). A north-rim anchor at y=0 has
# 3+ inward field cells (y 1..3), so a full m3e_01 (3 extensions) fits.
_DEEP_FIELD = _box_field(0, 4, 0, 5)

# Shallow-2 field: 3 tall (y 0..2). North-rim anchor at y=0 has only 2 inward
# field cells (y 1, 2) -> m3e_01 degrades from 3 to 2 extensions.
_SHALLOW2_FIELD = _box_field(0, 4, 0, 2)

# Shallow-1 field: 2 tall (y 0..1). North-rim anchor at y=0 has only 1 inward
# field cell (y 1) -> m3e_01 degrades from 3 to 1 extension.
_SHALLOW1_FIELD = _box_field(0, 4, 0, 1)


def deep_rim_complete_map() -> ReconstructionCompleteMap:
    return _complete_map(_DEEP_FIELD)


def deep_rim_exterior_plan() -> ExteriorConnectionPlan:
    return _plan(goal_coord=(6, 2))


def shallow2_rim_complete_map() -> ReconstructionCompleteMap:
    return _complete_map(_SHALLOW2_FIELD)


def shallow2_rim_exterior_plan() -> ExteriorConnectionPlan:
    return _plan(goal_coord=(6, 1))


def shallow1_rim_complete_map() -> ReconstructionCompleteMap:
    return _complete_map(_SHALLOW1_FIELD)


def shallow1_rim_exterior_plan() -> ExteriorConnectionPlan:
    return _plan(goal_coord=(6, 0))


def single_column_field(*, top: Coord, depth: int) -> frozenset[Coord]:
    """Field = a single inward column of ``depth`` cells starting at ``top`` (north rim)."""
    x, y0 = top
    return frozenset((x, y0 + d) for d in range(depth))


__all__ = [
    "deep_rim_complete_map",
    "deep_rim_exterior_plan",
    "shallow1_rim_complete_map",
    "shallow1_rim_exterior_plan",
    "shallow2_rim_complete_map",
    "shallow2_rim_exterior_plan",
    "single_column_field",
]
