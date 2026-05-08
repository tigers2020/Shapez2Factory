"""Shape miner rotation → belt output side; extensions on the opposite side (straight chain).

Uses the same XY grid as blueprint decoding: **+X east, +Y south** (screen-down).
East/west steps use ``shapez_grid.step_cardinal`` so **x == 0** is never used (columns
``-1`` and ``+1`` are one step apart).

``R % 4`` selects which edge of the 1×1 core the **belt/pipe output** attaches to
(items exit toward that neighbour). **Extensions** attach on the opposite edge and
continue in a straight line away from the output (entrance chain).

This mapping is **provisional** until verified against in-game miner variants; the
code centralizes it so we can swap for asset-derived tables later.
"""

from __future__ import annotations

from django_apps.shapez_asteroid.extraction.shapez_grid import step_cardinal

Coord = tuple[int, int]

# R=0 east, then clockwise in world (+Y = south).
_OUTPUT_UNIT: tuple[tuple[int, int], ...] = (
    (1, 0),
    (0, 1),
    (-1, 0),
    (0, -1),
)


def output_offset_r(r: int) -> tuple[int, int]:
    return _OUTPUT_UNIT[r % 4]


def shape_miner_output_cell(core: Coord, r: int) -> Coord | None:
    dx, dy = output_offset_r(r)
    return step_cardinal(core[0], core[1], dx, dy)


def shape_miner_extension_positions(
    core: Coord, r: int, extension_count: int
) -> tuple[Coord, ...] | None:
    """Cells opposite the output, collinear with the core; ``None`` if any step is illegal."""

    if extension_count <= 0:
        return tuple()
    ox, oy = output_offset_r(r)
    wx, wy = -ox, -oy
    cur_x, cur_y = core
    got: list[Coord] = []
    for _ in range(extension_count):
        nxt = step_cardinal(cur_x, cur_y, wx, wy)
        if nxt is None:
            return None
        got.append(nxt)
        cur_x, cur_y = nxt
    return tuple(got)
