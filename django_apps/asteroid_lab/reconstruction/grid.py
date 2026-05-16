"""Working bbox and coordinate enumeration for reconstruction (2D x,y; layer ignored)."""

from __future__ import annotations

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


def iter_bbox_cells(w0: int, w1: int, h0: int, h1: int) -> list[Coord]:
    """All integer coords in the inclusive bbox, skipping ``x == 0`` (dense gap convention)."""

    out: list[Coord] = []
    for x in range(w0, w1 + 1):
        if x == 0:
            continue
        for y in range(h0, h1 + 1):
            out.append((x, y))
    return out
