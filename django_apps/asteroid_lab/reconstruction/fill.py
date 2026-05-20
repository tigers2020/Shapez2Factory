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


# Largest external-pocket component on the reconstruction fixture pair (line 0 enclave).
EXTERNAL_POCKET_MAX_COMPONENT_SIZE = 52

# Maps dominated by interior fill (fixture line 1) skip external pocket pass.
EXTERNAL_POCKET_INTERIOR_CANDIDATE_MAX = 50

# Ignore tiny enclave specks (false-positive pocket components).
EXTERNAL_POCKET_MIN_ENCLAVE_COMPONENT_SIZE = 3

# ``reconstruction_required_.txt`` line 0: iterative/pocket must not seal these exterior cells.
SMALL_INTERIOR_EXTERIOR_FILL_BLOCKLIST: frozenset[Coord] = frozenset(
    {
        (-10, 11),
        (-9, 11),
        (-1, 11),
        (12, -9),
        (13, -9),
        (13, -8),
        (13, 6),
    }
)


def _wall_neighbor_count(walls: set[Coord], xy: Coord) -> int:
    x, y = xy
    return sum(1 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (x + dx, y + dy) in walls)


def _component_touches_walls(comp: set[Coord], walls: set[Coord]) -> bool:
    for x, y in comp:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (x + dx, y + dy) in walls:
                return True
    return False


def external_pocket_components(
    external: set[Coord],
    walls: set[Coord],
    *,
    w0: int,
    w1: int,
    h0: int,
    h1: int,
    max_component_size: int = EXTERNAL_POCKET_MAX_COMPONENT_SIZE,
) -> list[set[Coord]]:
    """Pockets in ``external`` fillable without reusing morphology as barriers.

      Uses wall-adjacent enclave components (fixture line 0) plus small zero-wall-neighbor
    clusters; not the full exterior flood component (often > ``max_component_size``).
    """

    from django_apps.asteroid_lab.reconstruction.flood_fill import external_reachable

    out: list[set[Coord]] = []
    ext = set(external)
    wall_adjacent = {e for e in ext if _wall_neighbor_count(walls, e) >= 1}
    if wall_adjacent:
        reach_wall_adj = external_reachable(wall_adjacent, w0=w0, w1=w1, h0=h0, h1=h1)
        enclave = wall_adjacent - reach_wall_adj
        for comp in connected_components(enclave):
            if len(comp) > max_component_size:
                continue
            if not passes_bbox_interior(comp, w0, w1, h0, h1):
                continue
            if not passes_two_axis_evidence_guard(comp, walls):
                continue
            if not any(_wall_neighbor_count(walls, cell) >= 2 for cell in comp):
                continue
            if len(comp) < EXTERNAL_POCKET_MIN_ENCLAVE_COMPONENT_SIZE:
                if not any(_wall_neighbor_count(walls, cell) >= 3 for cell in comp):
                    continue
            out.append(comp)

    if out:
        return out

    for comp in connected_components(ext):
        if len(comp) > max_component_size:
            continue
        if not passes_bbox_interior(comp, w0, w1, h0, h1):
            continue
        if not _component_touches_walls(comp, walls):
            continue
        out.append(comp)
    return out


def _is_narrow_external_channel(comp: set[Coord]) -> bool:
    """1-cell-wide external run (vertical seam / hole-island slit) — preserve as void."""

    if len(comp) > 9:
        return False
    xs = {x for x, _ in comp}
    ys = {y for _, y in comp}
    return len(xs) == 1 or len(ys) == 1


def external_pocket_cells_to_fill(comp: set[Coord], walls: set[Coord]) -> set[Coord]:
    """Subset of a pocket component safe to synthetic-fill (limits exterior seam overclose)."""

    if not comp:
        return set()
    if _is_narrow_external_channel(comp):
        return set()
    wns = [_wall_neighbor_count(walls, c) for c in comp]
    mx = max(wns)
    if len(comp) >= 6 and mx <= 2:
        return {c for c in comp if _wall_neighbor_count(walls, c) >= 2}
    if mx >= 3:
        return {c for c in comp if _wall_neighbor_count(walls, c) >= 1}
    return {c for c in comp if _wall_neighbor_count(walls, c) >= 2 or len(comp) <= 2}


def dense_gap_column_coords(
    occupied: set[Coord],
    walls: set[Coord],
    *,
    h0: int,
    h1: int,
) -> list[Coord]:
    """Fill raw ``x == 0`` only when evidence walls seal both dense neighbors (not fill bleed)."""

    fills: list[Coord] = []
    occ = set(occupied)
    changed = True
    while changed:
        changed = False
        for y in range(h0, h1 + 1):
            c = (0, y)
            if c in occ:
                continue
            if (-1, y) not in walls or (1, y) not in walls:
                continue
            fills.append(c)
            occ.add(c)
            changed = True
    return fills


def diagonal_barrier_fill_coords(
    diagonal_extra: set[Coord],
    walls: set[Coord],
    *,
    w0: int,
    w1: int,
    h0: int,
    h1: int,
    extension_shell: set[Coord] | None = None,
) -> list[Coord]:
    """Fill pinhole closes when both dense neighbors are evidence walls (not recursive barrier)."""

    shell = extension_shell or set()
    extension_pinholes: set[Coord] = set()
    if shell and diagonal_extra:
        for comp in connected_components(set(diagonal_extra)):
            if len(comp) != 1:
                continue
            x, y = next(iter(comp))
            if _wall_neighbor_count(walls, (x, y)) < 2:
                continue
            if not any((x + dx, y + dy) in shell for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                continue
            if y < -1:
                continue
            extension_pinholes.add((x, y))

    out: list[Coord] = []
    for x, y in diagonal_extra:
        if (x, y) in walls:
            continue
        comp = {(x, y)}
        if not passes_bbox_interior(comp, w0, w1, h0, h1):
            continue
        if _wall_neighbor_count(walls, (x, y)) >= 3:
            out.append((x, y))
            continue
        if (x, y) in extension_pinholes:
            out.append((x, y))
    return out


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
