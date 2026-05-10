"""Cheap 4-connectivity escape check from extractor belt head (STEP2 validator)."""

from __future__ import annotations

from collections import deque

from django_apps.shapez_asteroid.extraction.constants import ASTEROID_EXTERIOR_MARGIN
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

    if use_pipe and rec.solver_pipe_network_cells and start in rec.solver_pipe_network_cells:
        return True

    q: deque[Coord] = deque([start])
    seen: set[Coord] = {start}
    while q:
        cx, cy = q.popleft()
        if is_exterior_coord(cx, cy, rec=rec, exterior_margin=margin):
            return True
        if use_pipe and rec.solver_pipe_network_cells and (cx, cy) in rec.solver_pipe_network_cells:
            return True
        for nx, ny in neighbors4(cx, cy):
            nxy = (nx, ny)
            if nx < bx0 or nx > bx1 or ny < by0 or ny > by1:
                continue
            if nxy in seen:
                continue
            if use_pipe:
                if not pipe_step_allowed(nxy, blocked_cells=blocked_cells):
                    continue
            elif not transport_step_allowed(
                (cx, cy),
                nxy,
                blocked_cells=blocked_cells,
                routed_transport_cells=routed_transport_cells,
                directed_edges=de,
            ):
                continue
            seen.add(nxy)
            q.append(nxy)
    return False
