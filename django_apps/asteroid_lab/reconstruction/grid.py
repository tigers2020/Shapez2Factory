"""Working bbox and coordinate enumeration for reconstruction (2D x,y; layer ignored)."""

from __future__ import annotations

from collections.abc import Iterator

from django_apps.asteroid_lab.snapshots.transport_components import iter_four_neighbors

Coord = tuple[int, int]


def padded_bbox_bounds(
    wall_coords: set[Coord],
    *,
    pad: int = 1,
) -> tuple[int, int, int, int] | None:
    """Return inclusive (w0, w1, h0, h1) padded around wall_coords, or None if empty."""

    if not wall_coords:
        return None
    xs = [x for x, _ in wall_coords]
    ys = [y for _, y in wall_coords]
    mn_x, mx_x = min(xs), max(xs)
    mn_y, mx_y = min(ys), max(ys)
    w0, w1 = mn_x - pad, mx_x + pad
    if w0 == 0:
        w0 = -1
    h0, h1 = mn_y - pad, mx_y + pad
    return (w0, w1, h0, h1)


def iter_bbox_cells(
    w0: int,
    w1: int,
    h0: int,
    h1: int,
    *,
    include_raw_x_zero: bool = False,
) -> list[Coord]:
    """All integer coords in the inclusive bbox.

    By default skips ``x == 0`` (legacy dense-gap convention). When the blueprint has
    explicit raw ``X == 0`` entries, pass ``include_raw_x_zero=True`` so the seam column
    participates in walkable/flood topology.
    """

    out: list[Coord] = []
    for x in range(w0, w1 + 1):
        if x == 0 and not include_raw_x_zero:
            continue
        for y in range(h0, h1 + 1):
            out.append((x, y))
    return out


def reconstruction_cardinal_neighbors(
    x: int,
    y: int,
    *,
    include_raw_x_zero: bool,
) -> Iterator[Coord]:
    """Cardinal neighbors for flood/components (map coords or grid when seam included)."""

    if include_raw_x_zero:
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            yield (x + dx, y + dy)
        return
    for nx, ny, _nl in iter_four_neighbors(x, y, None):
        yield (nx, ny)
