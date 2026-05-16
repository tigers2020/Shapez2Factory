"""4-neighbor helpers for transport component grouping (A6; ORM-free)."""

from __future__ import annotations

from typing import Iterator

from django_apps.asteroid_lab.services.dto import DecodedCellDTO


def cell_position_key(cell: DecodedCellDTO) -> tuple[int, int, int | None]:
    return (cell.x, cell.y, cell.layer)


def sort_key_xy_layer(cell: DecodedCellDTO) -> tuple[int, int, int]:
    """Stable ordering; ``None`` layer sorts before negative real layers."""

    layer = cell.layer
    layer_key = layer if layer is not None else -10**12
    return (cell.x, cell.y, layer_key)


def iter_four_neighbors(x: int, y: int, layer: int | None) -> Iterator[tuple[int, int, int | None]]:
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        yield (x + dx, y + dy, layer)


def is_transport_tile(cell: DecodedCellDTO) -> bool:
    return cell.cell_kind in ("space_pipe", "space_belt")
