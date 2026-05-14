"""
Lattice / bbox / neighbor-set helpers on top of ``domain.coord``.

**Layering:** ``coord`` defines one cell and atomic ``neighbor`` / ``step_x`` only.
This module performs tuple adapters, bbox iteration, Chebyshev balls, and any
multi-cell read helpers. **Do not** use raw ``x + dx`` for east/west here — call
``neighbor`` / ``step_blueprint_cell`` only.

Pass3 / reclaim **RouteZone** costs live in ``domain.enums.ROUTE_ZONE_PASS3_BASE_COST``
(``03_data_schema_dto`` §11.1). **Do not** mix those numbers with STEP 4 grid
Dijkstra / merge-aware cell weights (``01_project_overview`` §3.5).
"""

from __future__ import annotations

from collections.abc import Iterator

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BBox,
    BlueprintCell,
    Coord,
    Direction,
    is_physical_coord,
    is_physical_x,
    neighbor,
    step_x,
)

_CARDINAL_DIRS: tuple[Direction, ...] = ((0, -1), (1, 0), (0, 1), (-1, 0))


def assert_nonzero_x(x: int) -> None:
    """Blueprint invariant: column x==0 does not exist."""

    if x == 0:
        msg = "illegal blueprint x==0"
        raise ValueError(msg)


def manhattan(a: Coord | tuple[int, int], b: Coord | tuple[int, int]) -> int:
    """|ax-bx|+|ay-by| (raw axis delta; not shapez layout-column distance)."""

    ax, ay = _as_xy(a)
    bx, by = _as_xy(b)
    return abs(ax - bx) + abs(ay - by)


def _as_xy(value: Coord | tuple[int, int]) -> tuple[int, int]:
    if isinstance(value, Coord):
        return (value.x, value.y)
    return (value[0], value[1])


def step_blueprint_cell(cell: BlueprintCell, d: Direction) -> BlueprintCell:
    """One cardinal step on tuples; implemented only via ``coord.neighbor``."""

    return neighbor(Coord(cell[0], cell[1]), d).as_tuple()


def physical_cardinal_neighbors(coord: Coord) -> tuple[Coord, ...]:
    """The four cardinal ``neighbor`` results (drops any non-physical landing)."""

    out: list[Coord] = []
    for d in _CARDINAL_DIRS:
        n = neighbor(coord, d)
        if is_physical_coord(n):
            out.append(n)
    return tuple(out)


def cardinal_neighbors4(cell: BlueprintCell) -> tuple[BlueprintCell, ...]:
    """Four shapez-adjacent tuple neighbors; order N → E → S → W."""

    return tuple(step_blueprint_cell(cell, d) for d in _CARDINAL_DIRS)


def chebyshev_neighbors8(cell: BlueprintCell) -> frozenset[BlueprintCell]:
    """8-neighborhood: horizontal offset uses ``coord.step_x`` only (no ``x + dx``)."""

    x, y = cell
    out: set[BlueprintCell] = set()
    for hdx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            if hdx == 0 and dy == 0:
                continue
            if hdx == 0:
                out.add((x, y + dy))
            else:
                out.add((step_x(x, hdx), y + dy))
    return frozenset(out)


def iter_physical_x_in_range(min_x: int, max_x: int) -> Iterator[int]:
    for x in range(min_x, max_x + 1):
        if is_physical_x(x):
            yield x


def iter_physical_bbox_coords(bbox: BBox) -> Iterator[Coord]:
    """Every lattice cell inside ``bbox`` skipping ``x == 0``."""

    for y in range(bbox.min_y, bbox.max_y + 1):
        for x in iter_physical_x_in_range(bbox.min_x, bbox.max_x):
            yield Coord(x, y)


def iter_physical_bbox_cells(bbox: BBox) -> Iterator[BlueprintCell]:
    """Same as ``iter_physical_bbox_coords`` but yields ``(x, y)`` tuples."""

    for c in iter_physical_bbox_coords(bbox):
        yield c.as_tuple()


def physical_column_count_inclusive(min_x: int, max_x: int) -> int:
    """Count of integer columns in ``[min_x, max_x]`` excluding ``x == 0``."""

    return sum(1 for _ in iter_physical_x_in_range(min_x, max_x))


__all__ = [
    "assert_nonzero_x",
    "cardinal_neighbors4",
    "chebyshev_neighbors8",
    "iter_physical_bbox_cells",
    "iter_physical_bbox_coords",
    "iter_physical_x_in_range",
    "manhattan",
    "physical_cardinal_neighbors",
    "physical_column_count_inclusive",
    "step_blueprint_cell",
]
