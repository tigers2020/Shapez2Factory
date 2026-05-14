"""Route zones and transport kind multipliers for Pass3 lexicographic routing (P3-E1)."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from enum import Enum

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.boundary import (
    cells_touching_void,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord


class TransportKind(str, Enum):
    """Surface / fluid transport — values match solver map row strings (STEP4/Pass12)."""

    SHAPE_BELT = "shape_belt"
    FLUID_PIPE = "fluid_pipe"


KIND_COST_MULTIPLIER: dict[TransportKind, int] = {
    TransportKind.SHAPE_BELT: 1,
    TransportKind.FLUID_PIPE: 1,
}


def transport_kind_from_solver_value(value: str) -> TransportKind:
    """Map solver ``transport_kind`` strings to :class:`TransportKind`."""

    try:
        return TransportKind(value)
    except ValueError as exc:
        raise ValueError(f"unknown transport_kind for lex router: {value!r}") from exc


class RouteZone(Enum):
    """Per-cell coarse zone for route cost and internal-transport accounting."""

    EXTERIOR_VOID = "exterior_void"
    ASTEROID_PERIMETER = "asteroid_perimeter"
    ASTEROID_INTERIOR_VOID = "asteroid_interior_void"
    FILLABLE_INTERIOR = "fillable_interior"


ROUTE_ZONE_COST: dict[RouteZone, int] = {
    # Outside / boundary cheap; rock interior medium; mineable interior expensive
    # (push routes toward exterior / void trunk; preserve mining footprint).
    RouteZone.EXTERIOR_VOID: 1,
    RouteZone.ASTEROID_PERIMETER: 5,
    RouteZone.ASTEROID_INTERIOR_VOID: 50,
    RouteZone.FILLABLE_INTERIOR: 150,
}

# Lex axis ``internal``: new transport on these zones (not on existing transport).
ROUTE_ZONES_LEX_COUNT_AS_INTERNAL: frozenset[RouteZone] = frozenset(
    {RouteZone.ASTEROID_INTERIOR_VOID, RouteZone.FILLABLE_INTERIOR}
)


def build_asteroid_boundary_depth_by_cell(
    *, asteroid_cells: frozenset[Coord] | set[Coord]
) -> dict[Coord, int]:
    """Shortest graph distance from void-touching boundary cells within ``asteroid_cells``.

    Depth ``0`` on :func:`cells_touching_void` members; increases for cardinal steps inward.
    Unreachable cells (isolated cavities) are omitted from the map; callers should treat
    missing keys as depth ``0`` for penalties.
    """

    ac = frozenset(asteroid_cells)
    if not ac:
        return {}
    boundary = cells_touching_void(set(ac))
    depth: dict[Coord, int] = {}
    q: deque[Coord] = deque()
    for c in boundary:
        depth[c] = 0
        q.append(c)
    while q:
        cur = q.popleft()
        d0 = depth[cur]
        x, y = cur
        for nxt in neighbors4(x, y):
            if nxt not in ac or nxt in depth:
                continue
            depth[nxt] = d0 + 1
            q.append(nxt)
    return depth


def build_route_zone_map(
    *,
    asteroid_cells: frozenset[Coord] | set[Coord],
    mineable_cells: frozenset[Coord] | set[Coord] | None = None,
) -> dict[Coord, RouteZone]:
    """Assign :class:`RouteZone` to each asteroid cell.

    Any coordinate not in the returned map is treated as ``EXTERIOR_VOID`` by
    :func:`route_zone_for_cell`.

    ``mineable_cells``: cells that are both mineable and in ``asteroid_cells`` become
    ``FILLABLE_INTERIOR`` (including perimeter-adjacent mineable). Other asteroid cells
    use void-touching perimeter vs four-neighbor interior void classification.
    """

    ac = frozenset(asteroid_cells)
    mine = frozenset(mineable_cells) if mineable_cells is not None else frozenset()
    perimeter = cells_touching_void(set(ac))
    out: dict[Coord, RouteZone] = {}
    for c in ac:
        if c in mine:
            out[c] = RouteZone.FILLABLE_INTERIOR
            continue
        if c in perimeter:
            out[c] = RouteZone.ASTEROID_PERIMETER
            continue
        x, y = c
        nbs = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
        if all(n in ac for n in nbs):
            out[c] = RouteZone.ASTEROID_INTERIOR_VOID
        else:
            out[c] = RouteZone.ASTEROID_PERIMETER
    return out


def route_zone_for_cell(cell: Coord, route_zone_map: Mapping[Coord, RouteZone]) -> RouteZone:
    """Resolve zone for ``cell`` using a partial map (missing key ⇒ exterior)."""

    z = route_zone_map.get(cell)
    if z is None:
        return RouteZone.EXTERIOR_VOID
    return z
