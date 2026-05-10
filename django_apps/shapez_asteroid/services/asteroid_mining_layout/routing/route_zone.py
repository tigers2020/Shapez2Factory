"""Route zones and transport kind multipliers for Pass3 lexicographic routing (P3-E1)."""

from __future__ import annotations

from collections.abc import Mapping
from enum import Enum

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
    ASTEROID_INTERIOR = "asteroid_interior"


ROUTE_ZONE_COST: dict[RouteZone, int] = {
    # Aligned with mining_solver_cursor_sessions DTO: outside cheap, interior expensive
    # so lex route_cost (3rd axis) pushes paths toward exterior/boundary after internal_min.
    RouteZone.EXTERIOR_VOID: 1,
    RouteZone.ASTEROID_PERIMETER: 5,
    RouteZone.ASTEROID_INTERIOR: 50,
}


def build_route_zone_map(
    *, asteroid_cells: frozenset[Coord] | set[Coord]
) -> dict[Coord, RouteZone]:
    """Assign ``RouteZone`` to each asteroid cell.

    Any coordinate not in the map is treated as ``EXTERIOR_VOID``.
    Interior = all four neighbors inside the asteroid; otherwise perimeter.
    """

    ac = frozenset(asteroid_cells)
    perimeter = cells_touching_void(set(ac))
    out: dict[Coord, RouteZone] = {}
    for c in ac:
        x, y = c
        if c in perimeter:
            out[c] = RouteZone.ASTEROID_PERIMETER
            continue
        nbs = ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1))
        if all(n in ac for n in nbs):
            out[c] = RouteZone.ASTEROID_INTERIOR
        else:
            out[c] = RouteZone.ASTEROID_PERIMETER
    return out


def route_zone_for_cell(cell: Coord, route_zone_map: Mapping[Coord, RouteZone]) -> RouteZone:
    """Resolve zone for ``cell`` using a partial map (missing key ⇒ exterior)."""

    z = route_zone_map.get(cell)
    if z is None:
        return RouteZone.EXTERIOR_VOID
    return z
