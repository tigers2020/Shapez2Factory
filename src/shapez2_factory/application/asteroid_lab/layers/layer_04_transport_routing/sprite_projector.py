"""Project committed routes to SpaceBelt/SpacePipe tiles via catalog lookup."""

from __future__ import annotations

from shapez2_factory.adapters.asteroid_lab.space_transport_catalog_snapshot import (
    EswmMask,
    SpaceTransportCatalogInvalid,
    SpaceTransportTileCatalog,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer04_route import (
    CommittedRoute,
    ProjectedTransportTile,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord

_DIR_ORDER: tuple[str, ...] = ("E", "S", "W", "N")
_DIR_DELTA: dict[str, tuple[int, int]] = {
    "E": (1, 0),
    "S": (0, 1),
    "W": (-1, 0),
    "N": (0, -1),
}

# R0 single-input / single-output masks → (tile suffix, rotation). Used when catalog lacks a mask.
_HEURISTIC_STRAIGHT_AND_TURN: dict[tuple[str, str], tuple[str, int]] = {
    ("W", "E"): ("Forward", 0),
    ("E", "W"): ("Forward", 2),
    ("N", "S"): ("Forward", 1),
    ("S", "N"): ("Forward", 3),
    ("W", "N"): ("LeftTurn", 0),
    ("W", "S"): ("RightTurn", 0),
    ("E", "N"): ("RightTurn", 1),
    ("E", "S"): ("LeftTurn", 1),
    ("N", "E"): ("RightTurn", 2),
    ("N", "W"): ("LeftTurn", 2),
    ("S", "W"): ("RightTurn", 3),
    ("S", "E"): ("LeftTurn", 3),
}


def _mask_for_dirs(directions: frozenset[str]) -> EswmMask:
    return (
        "E" in directions,
        "S" in directions,
        "W" in directions,
        "N" in directions,
    )


def _signature_for_cell(
    path: tuple[Coord, ...],
    coord: Coord,
) -> tuple[EswmMask, EswmMask]:
    idx = path.index(coord)
    inputs: set[str] = set()
    outputs: set[str] = set()
    if idx > 0:
        prev = path[idx - 1]
        dx, dy = coord[0] - prev[0], coord[1] - prev[1]
        for slug, delta in _DIR_DELTA.items():
            if delta == (-dx, -dy):
                inputs.add(slug)
    if idx < len(path) - 1:
        nxt = path[idx + 1]
        dx, dy = nxt[0] - coord[0], nxt[1] - coord[1]
        for slug, delta in _DIR_DELTA.items():
            if delta == (dx, dy):
                outputs.add(slug)
    if not inputs and outputs == frozenset({"E"}):
        inputs.add("W")
    elif inputs == frozenset({"W"}) and not outputs:
        outputs.add("E")
    elif not inputs and outputs == frozenset({"N"}):
        inputs.add("S")
    elif inputs == frozenset({"S"}) and not outputs:
        outputs.add("N")
    if not inputs and not outputs:
        return _mask_for_dirs(frozenset()), _mask_for_dirs(frozenset())
    return _mask_for_dirs(frozenset(inputs)), _mask_for_dirs(frozenset(outputs))


def _dirs_from_mask(mask: EswmMask) -> frozenset[str]:
    return frozenset(slug for slug, on in zip(_DIR_ORDER, mask, strict=True) if on)


def _heuristic_tile_id_and_rotation(
    *,
    transport_kind: str,
    input_mask: EswmMask,
    output_mask: EswmMask,
) -> tuple[str, int] | None:
    ins = _dirs_from_mask(input_mask)
    outs = _dirs_from_mask(output_mask)
    if len(ins) != 1 or len(outs) != 1:
        return None
    in_dir = next(iter(ins))
    out_dir = next(iter(outs))
    hit = _HEURISTIC_STRAIGHT_AND_TURN.get((in_dir, out_dir))
    if hit is None:
        return None
    suffix, rotation = hit
    prefix = "SpacePipe_" if transport_kind == "space_pipe" else "SpaceBelt_"
    return prefix + suffix, rotation


def project_routes_to_tiles(
    *,
    routes: tuple[CommittedRoute, ...],
    transport_kind: str,
    catalog: SpaceTransportTileCatalog,
) -> tuple[ProjectedTransportTile, ...]:
    tiles: list[ProjectedTransportTile] = []
    cell_to_routes: dict[Coord, list[str]] = {}
    for route in routes:
        for cell in route.path_coords:
            cell_to_routes.setdefault(cell, []).append(route.route_id)

    for route in routes:
        for coord in route.path_coords:
            input_mask, output_mask = _signature_for_cell(route.path_coords, coord)
            input_dirs = tuple(
                slug for slug, on in zip(_DIR_ORDER, input_mask, strict=True) if on
            )
            output_dirs = tuple(
                slug for slug, on in zip(_DIR_ORDER, output_mask, strict=True) if on
            )
            tile_id: str
            rotation: int
            try:
                entry = catalog.lookup_io(
                    transport_kind=transport_kind,
                    input_mask=input_mask,
                    output_mask=output_mask,
                )
                tile_id = entry.tile_id
                rotation = entry.canonical_rotation
            except SpaceTransportCatalogInvalid:
                heuristic = _heuristic_tile_id_and_rotation(
                    transport_kind=transport_kind,
                    input_mask=input_mask,
                    output_mask=output_mask,
                )
                if heuristic is None:
                    continue
                tile_id, rotation = heuristic
            tiles.append(
                ProjectedTransportTile(
                    coord=coord,
                    transport_kind=transport_kind,
                    tile_id=tile_id,
                    rotation=rotation,
                    input_dirs=input_dirs,
                    output_dirs=output_dirs,
                    group_id=route.group_id,
                    source_route_ids=tuple(sorted(cell_to_routes.get(coord, [route.route_id]))),
                )
            )
    tiles.sort(key=lambda t: (t.coord[0], t.coord[1], t.tile_id))
    return tuple(tiles)


__all__ = ["project_routes_to_tiles"]
