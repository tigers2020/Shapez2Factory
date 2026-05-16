"""Interior component detection, enclosure guards, and deterministic fill kind."""

from __future__ import annotations

from collections import Counter, deque

from django_apps.asteroid_lab.reconstruction.evidence import ASTEROID_FIELD_KINDS
from django_apps.asteroid_lab.reconstruction.grid import Coord
from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.transport_components import iter_four_neighbors

ASTEROID_SHAPE_FIELD = "asteroid_shape_field"


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


def _neighbor_pool(comp: set[Coord], *, chebyshev: bool) -> set[Coord]:
    pool: set[Coord] = set()
    for x, y in comp:
        if chebyshev:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    if dx == 0 and dy == 0:
                        continue
                    pool.add((x + dx, y + dy))
        else:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                pool.add((x + dx, y + dy))
    return pool


def _tally_field_kinds(pool: set[Coord], field_by_xy: dict[Coord, str]) -> Counter[str]:
    ctr: Counter[str] = Counter()
    for xy in pool:
        k = field_by_xy.get(xy)
        if k in ASTEROID_FIELD_KINDS:
            ctr[k] += 1
    return ctr


def _strict_winner(ctr: Counter[str]) -> str | None:
    """Return kind if it has strictly higher count than any other; ties return None."""

    if not ctr:
        return None
    items = sorted(ctr.items(), key=lambda kv: (-kv[1], kv[0]))
    top_k, top_v = items[0]
    if len(items) == 1:
        return top_k
    second_v = items[1][1]
    if top_v > second_v:
        return top_k
    return None


def infer_fill_field_kind(
    comp: set[Coord],
    field_by_xy: dict[Coord, str],
    global_field_counter: Counter[str],
) -> str:
    """Deterministic fluid/shape choice (building types must not influence this)."""

    for cheb in (False, True):
        ctr = _tally_field_kinds(_neighbor_pool(comp, chebyshev=cheb), field_by_xy)
        winner = _strict_winner(ctr)
        if winner is not None:
            return winner
    gwin = _strict_winner(global_field_counter)
    if gwin is not None:
        return gwin
    return ASTEROID_SHAPE_FIELD


def synthetic_field_cell(
    x: int,
    y: int,
    layer: int | None,
    field_kind: str,
    *,
    server_x: int | None = None,
    server_y: int | None = None,
) -> DecodedCellDTO:
    """Replay-only filled hole cell."""

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
