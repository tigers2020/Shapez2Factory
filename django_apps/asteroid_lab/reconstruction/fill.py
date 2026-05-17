"""Interior component detection, enclosure guards, and topology placeholder fill."""

from __future__ import annotations

from collections import deque

from django_apps.asteroid_lab.reconstruction.grid import Coord
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.transport_components import iter_four_neighbors

ASTEROID_SHAPE_FIELD = "asteroid_shape_field"

# Island pass assigns final ``asteroid_*_field``; topology holes use this placeholder first.
TOPOLOGY_FILL_PLACEHOLDER_KIND = ASTEROID_SHAPE_FIELD


def passes_bbox_interior(comp: set[Coord], w0: int, w1: int, h0: int, h1: int) -> bool:
    """Drop components touching the working bbox border (open to exterior padding)."""

    for x, y in comp:
        if x <= w0 or x >= w1 or y <= h0 or y >= h1:
            return False
    return True


def passes_two_axis_evidence_guard(comp: set[Coord], walls: set[Coord]) -> bool:
    """Require evidence-wall touch on both x- and y-offset directions (4-neighbor).

    Pass ``cleanup.wall_coords`` only; do not pass inferred shell / flood ``barrier`` sets
    (would self-justify fills). Barriers for flood are handled in ``pipeline``.
    """

    has_x = False
    has_y = False
    for x, y in comp:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) in walls:
                if dx != 0:
                    has_x = True
                if dy != 0:
                    has_y = True
    return has_x and has_y


def connected_components(nodes: set[Coord]) -> list[set[Coord]]:
    """4-connected components."""

    remaining = set(nodes)
    comps: list[set[Coord]] = []
    while remaining:
        start = remaining.pop()
        comp: set[Coord] = {start}
        q: deque[Coord] = deque([start])
        while q:
            x, y = q.popleft()
            for nx, ny, _nl in iter_four_neighbors(x, y, None):
                n = (nx, ny)
                if n not in remaining or n in comp:
                    continue
                remaining.remove(n)
                comp.add(n)
                q.append(n)
        comps.append(comp)
    return comps


def synthetic_field_cell(
    x: int,
    y: int,
    layer: int | None,
    field_kind: str,
    *,
    server_x: int | None = None,
    server_y: int | None = None,
) -> DecodedCellDTO:
    """Replay-only filled hole cell (placeholder ``cell_kind`` until island stamp)."""

    return DecodedCellDTO(
        x=x,
        y=y,
        layer=layer,
        rotation=0,
        tile_type="",
        cell_kind=field_kind,
        transport_kind="none",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={"_replay_synthetic": True, "_reconstruction": "topology_fill"},
        server_x=server_x,
        server_y=server_y,
    )
