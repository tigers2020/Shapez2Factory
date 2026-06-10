"""Place one minimal routeable inner miner group (m3e east) when feasible."""

from __future__ import annotations

from collections import deque

from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_inner_fill import (
    RouteableInnerGroupPlacement,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)

# Canonical miner_seed_m3e_01 shape footprint, east-facing (y-down frame).
_M3E_EAST_FIELD_OFFSETS: tuple[Coord, ...] = ((-3, 0), (-2, 0), (-1, 0), (0, 0))
_M3E_EAST_STUB_OFFSET: Coord = (1, 0)
_INNER_MINER_THROUGHPUT_FACTOR = 4


def _footprint_at_anchor(anchor: Coord) -> tuple[frozenset[Coord], frozenset[Coord], Coord]:
    ax, ay = anchor
    field_cells = frozenset((ax + dx, ay + dy) for dx, dy in _M3E_EAST_FIELD_OFFSETS)
    miner_cells = frozenset({anchor})
    extension_cells = field_cells - miner_cells
    stub = (ax + _M3E_EAST_STUB_OFFSET[0], ay + _M3E_EAST_STUB_OFFSET[1])
    return miner_cells, extension_cells, stub


def _manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _stub_reaches_connector(
    *,
    complete_map: ReconstructionCompleteMap,
    stub: Coord,
    connector_voids: frozenset[Coord],
    blocked_cells: frozenset[Coord],
) -> bool:
    if not connector_voids:
        return False
    field_cells = complete_map.field_cells
    void_cells = complete_map.external_void_cells - field_cells
    walkable = (field_cells | void_cells) - blocked_cells
    if stub not in walkable:
        return False
    queue: deque[Coord] = deque([stub])
    seen = {stub}
    while queue:
        current = queue.popleft()
        if current in connector_voids:
            return True
        x, y = current
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            nxt = (nx, ny)
            if nxt in seen or nxt not in walkable:
                continue
            seen.add(nxt)
            queue.append(nxt)
    return False


def try_place_first_routeable_inner_group(
    *,
    complete_map: ReconstructionCompleteMap,
    interior_candidates: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    connector_void_coords: frozenset[Coord] = frozenset(),
    placement_index: int = 1,
) -> RouteableInnerGroupPlacement | None:
    """Return the nearest-routable anchor where an m3e east group fits."""

    field_cells = complete_map.field_cells
    ranked_anchors: list[tuple[int, int, int, Coord]] = []
    for anchor in interior_candidates:
        _miner_cells, _extension_cells, stub = _footprint_at_anchor(anchor)
        dist = (
            min(_manhattan(stub, goal) for goal in connector_void_coords)
            if connector_void_coords
            else 0
        )
        ranked_anchors.append((dist, anchor[0], anchor[1], anchor))
    ranked_anchors.sort()

    for _dist, _x, _y, anchor in ranked_anchors:
        miner_cells, extension_cells, stub = _footprint_at_anchor(anchor)
        footprint = miner_cells | extension_cells
        if not footprint <= field_cells:
            continue
        if footprint & blocked_cells:
            continue
        if stub in blocked_cells:
            continue
        if not _stub_reaches_connector(
            complete_map=complete_map,
            stub=stub,
            connector_voids=connector_void_coords,
            blocked_cells=blocked_cells | footprint,
        ):
            continue
        return RouteableInnerGroupPlacement(
            placement_id=f"l4-inner-{placement_index:04d}",
            anchor=anchor,
            miner_cells=miner_cells,
            extension_cells=extension_cells,
            m_output_stub=stub,
            throughput_factor=_INNER_MINER_THROUGHPUT_FACTOR,
        )
    return None


__all__ = ["try_place_first_routeable_inner_group"]
