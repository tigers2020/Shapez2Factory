"""Place routeable inner miner groups (m3e east) until target or exhaustion."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_inner_fill import (
    RouteableInnerGroupPlacement,
)
from shapez2_factory.application.asteroid_lab.layers.layer_04_transport_routing.space_lift_routing import (  # noqa: E501
    lift_void_egress_for_stub,
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


def _stub_has_lift_egress(
    *,
    complete_map: ReconstructionCompleteMap,
    stub: Coord,
    connector_void_coords: frozenset[Coord],
) -> bool:
    if not connector_void_coords:
        return True
    return (
        lift_void_egress_for_stub(
            stub=stub,
            complete_map=complete_map,
            connector_void_coords=connector_void_coords,
        )
        is not None
    )


def try_place_one_routeable_inner_group(
    *,
    complete_map: ReconstructionCompleteMap,
    interior_candidates: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    connector_void_coords: frozenset[Coord] = frozenset(),
    placement_index: int = 1,
    prefer_connector_distance: bool = True,
) -> RouteableInnerGroupPlacement | None:
    """Return a lift-feasible anchor where an m3e east group fits."""

    field_cells = complete_map.field_cells
    if prefer_connector_distance and connector_void_coords:
        ranked: list[tuple[int, int, int, Coord]] = []
        for anchor in interior_candidates:
            _miner_cells, _extension_cells, stub = _footprint_at_anchor(anchor)
            dist = min(_manhattan(stub, goal) for goal in connector_void_coords)
            ranked.append((dist, anchor[0], anchor[1], anchor))
        ranked.sort()
        ordered_anchors = [anchor for *_prefix, anchor in ranked]
    else:
        ordered_anchors = sorted(interior_candidates, key=lambda c: (c[1], c[0]))

    for anchor in ordered_anchors:
        miner_cells, extension_cells, stub = _footprint_at_anchor(anchor)
        footprint = miner_cells | extension_cells
        if not footprint <= field_cells:
            continue
        if footprint & blocked_cells:
            continue
        if stub in blocked_cells:
            continue
        if not _stub_has_lift_egress(
            complete_map=complete_map,
            stub=stub,
            connector_void_coords=connector_void_coords,
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


def place_routeable_inner_groups(
    *,
    complete_map: ReconstructionCompleteMap,
    interior_candidates: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    connector_void_coords: frozenset[Coord] = frozenset(),
    max_groups: int,
) -> tuple[RouteableInnerGroupPlacement, ...]:
    """Greedy loop: place non-overlapping inner routeable groups up to ``max_groups``."""

    if max_groups <= 0:
        return ()
    placed: list[RouteableInnerGroupPlacement] = []
    occupied = set(blocked_cells)
    for index in range(1, max_groups + 1):
        group = try_place_one_routeable_inner_group(
            complete_map=complete_map,
            interior_candidates=interior_candidates,
            blocked_cells=frozenset(occupied),
            connector_void_coords=connector_void_coords,
            placement_index=index,
            prefer_connector_distance=False,
        )
        if group is None:
            break
        placed.append(group)
        occupied |= group.miner_cells | group.extension_cells | {group.m_output_stub}
    return tuple(placed)


def try_place_first_routeable_inner_group(
    *,
    complete_map: ReconstructionCompleteMap,
    interior_candidates: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    connector_void_coords: frozenset[Coord] = frozenset(),
    placement_index: int = 1,
) -> RouteableInnerGroupPlacement | None:
    return try_place_one_routeable_inner_group(
        complete_map=complete_map,
        interior_candidates=interior_candidates,
        blocked_cells=blocked_cells,
        connector_void_coords=connector_void_coords,
        placement_index=placement_index,
    )


__all__ = [
    "place_routeable_inner_groups",
    "try_place_first_routeable_inner_group",
    "try_place_one_routeable_inner_group",
]
