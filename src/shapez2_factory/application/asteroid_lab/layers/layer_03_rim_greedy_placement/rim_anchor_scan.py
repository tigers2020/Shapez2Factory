"""Layer 03 rim anchor scan ??deterministic outer-rim enumeration (spec R1 / D1).

Enumerates field cells adjacent to external void in the canonical solver coordinate
frame of ``ReconstructionCompleteMap``. No ORM, no Lab-render/dense coordinates: all
coordinate and neighbor math uses ``complete_map`` solver-frame cells only.

Direction convention is reused from ``layer_02_exterior_transport/slots.py``:
``CardinalEdge`` (north/east/south/west) with the NESW rank order and deltas
N=(0,-1) E=(1,0) S=(0,1) W=(-1,0) (south is +y).
"""

from __future__ import annotations

from dataclasses import dataclass

from shapez2_factory.application.asteroid_lab.layers.contracts.cardinal_edge import CardinalEdge
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
    mineable_field_kind_by_coord,
)

# Fixed cardinal rank (NESW) shared with the L2 exterior slot catalog.
_NESW_DELTAS: tuple[tuple[CardinalEdge, Coord], ...] = (
    (CardinalEdge.NORTH, (0, -1)),
    (CardinalEdge.EAST, (1, 0)),
    (CardinalEdge.SOUTH, (0, 1)),
    (CardinalEdge.WEST, (-1, 0)),
)

_FIELD_KIND_BY_CELL_KIND: dict[str, str] = {
    "asteroid_shape_field": "shape",
    "asteroid_fluid_field": "fluid",
}


@dataclass(frozen=True, slots=True)
class RimAnchor:
    """A field cell adjacent to external void, with the void-facing directions.

    ``coord`` is in the canonical solver frame of ``ReconstructionCompleteMap``.
    ``void_dirs`` holds ``CardinalEdge`` values in fixed NESW rank order.
    """

    coord: Coord
    field_kind: str
    void_dirs: tuple[str, ...]


def _resolve_field_kind(
    coord: Coord,
    kind_by_coord: dict[Coord, str],
    *,
    shape_count: int,
    fluid_count: int,
) -> str:
    """Map a field cell to ``"shape"`` / ``"fluid"``.

    Prefers per-cell evidence (``cells[].cell_kind``). When the map carries no decoded
    cells (e.g. synthetic fixtures with ``cells=()``) it falls back to the field counts:
    a single-resource field resolves unambiguously, otherwise defaults to ``"shape"``.
    """

    cell_kind = kind_by_coord.get(coord)
    if cell_kind is not None:
        mapped = _FIELD_KIND_BY_CELL_KIND.get(cell_kind)
        if mapped is not None:
            return mapped
    if fluid_count == 0:
        return "shape"
    if shape_count == 0:
        return "fluid"
    return "shape"


def scan_rim_anchors(complete_map: ReconstructionCompleteMap) -> tuple[RimAnchor, ...]:
    """Enumerate rim anchors: field cells with at least one external-void neighbor.

    Returns anchors sorted by ``(coord[0], coord[1])``; each anchor's ``void_dirs`` is in
    fixed NESW rank order. Field cells with no void neighbor (interior) are skipped.
    """

    field_cells = complete_map.field_cells
    external_void = complete_map.external_void_cells
    kind_by_coord = mineable_field_kind_by_coord(complete_map)

    anchors: list[RimAnchor] = []
    for coord in field_cells:
        x, y = coord
        void_dirs: list[str] = []
        for edge, (dx, dy) in _NESW_DELTAS:
            neighbor = (x + dx, y + dy)
            if neighbor in external_void:
                void_dirs.append(edge.value)
        if not void_dirs:
            continue
        anchors.append(
            RimAnchor(
                coord=coord,
                field_kind=_resolve_field_kind(
                    coord,
                    kind_by_coord,
                    shape_count=complete_map.shape_field_cell_count,
                    fluid_count=complete_map.fluid_field_cell_count,
                ),
                void_dirs=tuple(void_dirs),
            )
        )

    anchors.sort(key=lambda anchor: (anchor.coord[0], anchor.coord[1]))
    return tuple(anchors)


__all__ = ["RimAnchor", "scan_rim_anchors"]
