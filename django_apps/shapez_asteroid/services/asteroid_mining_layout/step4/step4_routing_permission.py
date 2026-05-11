"""STEP4 Dijkstra: cell occupation rules and goal predicate (§9.2, §9 STEP4 routing).

Spatial authority: legality and step costs for painting ``want_role`` transport onto the
working cell dict during merge-aware routing. Downstream stages must not re-derive these rules
independently — import from here or call ``dijkstra_route_step4`` in ``step4_dijkstra``.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    EXTENSIONS as _EXTENSIONS,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    EXTRACTORS_FLUID as _EXTRACTORS_FLUID,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    EXTRACTORS_SHAPE as _EXTRACTORS_SHAPE,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    layout_kind as _layout_kind,
)

# Positive costs for Dijkstra; ``None`` means the step is not permitted.
_COST_SAME_ROLE_TRANSPORT = 10.0
_COST_EXTERNAL_REACH = 15.0
_COST_MINEABLE = 100.0
_COST_ASTEROID_FIELD = 60.0
# Must not be cheaper than asteroid rock (``_COST_ASTEROID_FIELD``); otherwise Dijkstra
# prefers "open" coordinates over in-asteroid cells and cuts straight across interiors.
_COST_DEFAULT_OPEN = 60.0


def step4_step_cost(
    c: Coord,
    *,
    want_role: str,
    cells: dict[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    is_external: Callable[[Coord], bool],
) -> float | None:
    """Cost to occupy ``c`` with ``want_role`` transport; ``None`` if illegal."""

    x, _ = c
    if x == 0:
        return None
    row = cells.get(c)
    if row is not None:
        role = row.get("role")
        if role == want_role:
            return _COST_SAME_ROLE_TRANSPORT
        if role in ("belt", "pipe"):
            return None
        lk = _layout_kind(row)
        if lk in _EXTRACTORS_SHAPE | _EXTRACTORS_FLUID | _EXTENSIONS:
            return None
        if role == "occupied" and lk not in (None, "asteroid_field"):
            return None
    if is_external(c):
        return _COST_EXTERNAL_REACH
    if c in mineable:
        return _COST_MINEABLE
    if c in asteroid:
        return _COST_ASTEROID_FIELD
    return _COST_DEFAULT_OPEN


def step4_is_routing_goal(
    u: Coord,
    *,
    want_role: str,
    trunk: frozenset[Coord],
    is_external: Callable[[Coord], bool],
) -> bool:
    """True when search reached trunk or a cell adjacent to external (§9.2).

    상세: documents/Algorithm/mining_solver_cursor_sessions/08_step4_routing.md"""

    _ = want_role
    if u in trunk:
        return True
    x, y = u
    for nxt in neighbors4(x, y):
        if is_external(nxt):
            return True
    return False
