"""Cheap 4-connectivity escape check from extractor belt head (STEP2 validator)."""

from __future__ import annotations

from collections import deque

from django_apps.shapez_asteroid.constants import ASTEROID_EXTERIOR_MARGIN
from django_apps.shapez_asteroid.extraction.shape_miner_rotation import shape_miner_output_cell
from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_reconstruction import (
    AsteroidReconstruction,
    is_exterior_coord,
)

Coord = tuple[int, int]
DirectedEdge = tuple[Coord, Coord]


def transport_step_allowed(
    cur: Coord,
    nxy: Coord,
    *,
    blocked_cells: frozenset[Coord],
    routed_transport_cells: frozenset[Coord],
    directed_edges: frozenset[DirectedEdge],
) -> bool:
    """Whether moving ``cur`` → ``nxy`` is legal for rebuild-mode belt transport."""

    if nxy in blocked_cells:
        return False
    if (nxy, cur) in directed_edges:
        return False
    del routed_transport_cells
    return True


def pipe_step_allowed(nxy: Coord, *, blocked_cells: frozenset[Coord]) -> bool:
    """Pipe reachability: undirected steps; only hard-blocked cells are forbidden."""

    return nxy not in blocked_cells


def _in_search_bounds(nx: int, ny: int, bx0: int, bx1: int, by0: int, by1: int) -> bool:
    return bx0 <= nx <= bx1 and by0 <= ny <= by1


def _cell_reaches_exit_goal(
    cell: Coord,
    *,
    rec: AsteroidReconstruction,
    margin: int,
    use_pipe: bool,
) -> bool:
    cx, cy = cell
    if is_exterior_coord(cx, cy, rec=rec, exterior_margin=margin):
        return True
    net = rec.solver_pipe_network_cells
    return bool(use_pipe and net and cell in net)


def _neighbor_step_ok(
    cur: Coord,
    nxy: Coord,
    *,
    use_pipe: bool,
    blocked_cells: frozenset[Coord],
    routed_transport_cells: frozenset[Coord],
    directed_edges: frozenset[DirectedEdge],
) -> bool:
    if use_pipe:
        return pipe_step_allowed(nxy, blocked_cells=blocked_cells)
    return transport_step_allowed(
        cur,
        nxy,
        blocked_cells=blocked_cells,
        routed_transport_cells=routed_transport_cells,
        directed_edges=directed_edges,
    )


def _cheap_transport_escape_bfs(
    start: Coord,
    *,
    rec: AsteroidReconstruction,
    margin: int,
    use_pipe: bool,
    blocked_cells: frozenset[Coord],
    routed_transport_cells: frozenset[Coord],
    directed_edges: frozenset[DirectedEdge],
    bx0: int,
    bx1: int,
    by0: int,
    by1: int,
) -> bool:
    q: deque[Coord] = deque([start])
    seen: set[Coord] = {start}
    while q:
        cx, cy = q.popleft()
        cur = (cx, cy)
        if _cell_reaches_exit_goal(cur, rec=rec, margin=margin, use_pipe=use_pipe):
            return True
        for nx, ny in neighbors4(cx, cy):
            if not _in_search_bounds(nx, ny, bx0, bx1, by0, by1):
                continue
            nxy = (nx, ny)
            if nxy in seen:
                continue
            if not _neighbor_step_ok(
                cur,
                nxy,
                use_pipe=use_pipe,
                blocked_cells=blocked_cells,
                routed_transport_cells=routed_transport_cells,
                directed_edges=directed_edges,
            ):
                continue
            seen.add(nxy)
            q.append(nxy)
    return False


def cheap_transport_escape_exists(
    *,
    rec: AsteroidReconstruction,
    extractor_core: Coord,
    rotation: int,
    cluster_cells: frozenset[Coord],
    routed_transport_cells: frozenset[Coord],
    additional_blocked_cells: frozenset[Coord] | None = None,
    corridor_soft: frozenset[Coord] | None = None,
    directed_edges: frozenset[tuple[Coord, Coord]] | None = None,
    margin: int = ASTEROID_EXTERIOR_MARGIN,
    transport_kind: str = "belt",
) -> bool:
    """4-BFS from the shape-miner **output** cell (see ``shape_miner_rotation``) to exterior."""

    del corridor_soft  # MVP: reserved corridor scoring only; cheap BFS is optimistic.
    ax = frozenset() if additional_blocked_cells is None else additional_blocked_cells
    de = frozenset() if directed_edges is None else directed_edges
    blocked_cells = frozenset(cluster_cells | ax | rec.transport_hard_block_cells)
    use_pipe = transport_kind == "pipe"

    pad = margin + 2
    bx0, bx1 = rec.x_min - pad, rec.x_max + pad
    by0, by1 = rec.y_min - pad, rec.y_max + pad

    start = shape_miner_output_cell(extractor_core, rotation)
    if start is None or start in blocked_cells:
        return False
    return _cheap_transport_escape_bfs(
        start,
        rec=rec,
        margin=margin,
        use_pipe=use_pipe,
        blocked_cells=blocked_cells,
        routed_transport_cells=routed_transport_cells,
        directed_edges=de,
        bx0=bx0,
        bx1=bx1,
        by0=by0,
        by1=by1,
    )
