"""Blueprint grid helpers: **no tile at x == 0**.

양의 열과 음의 열 사이에 **0열이 없다**.
동서 이웃은 ``x == 1`` 과 ``x == -1`` 만 해당한다.
한 칸 이동으로 ``-1 ↔ 1`` 만 허용된다(``0`` 경유 없음).
남북은 ``x == 0`` 세로선이 존재하지 않으므로, 해당 선상에서의 북·남 스텝은 불가하다.

Pathfinding, reachability, and miner extension lines must use these steps so routes
never visit ``(0, y)`` and east/west moves across the missing column jump ``-1 ↔ 1``.
"""

from __future__ import annotations

Coord = tuple[int, int]


def is_legal_xy(x: int, y: int) -> bool:
    return x != 0


def step_cardinal(x: int, y: int, dx: int, dy: int) -> Coord | None:
    """One cardinal step; never rests on ``x == 0`` (skips the non-existent column)."""

    if dx == 0 and dy == 0:
        return None
    nx, ny = x + dx, y + dy
    if dx == 0:
        if nx == 0:
            return None
        return (nx, ny)
    # east/west
    if nx != 0:
        return (nx, ny)
    if dx == 1 and x == -1:
        return (1, ny)
    if dx == -1 and x == 1:
        return (-1, ny)
    return None


def neighbors4(x: int, y: int) -> tuple[Coord, ...]:
    out: list[Coord] = []
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        c = step_cardinal(x, y, dx, dy)
        if c is not None:
            out.append(c)
    return tuple(out)


def layout_column_x(x: int) -> int:
    """Column index monotonic with sorted ``uniqueXs`` (x>0 stored as ``x-1``)."""

    if x > 0:
        return x - 1
    return x


def shapez_manhattan(a: Coord, b: Coord) -> int:
    return abs(layout_column_x(a[0]) - layout_column_x(b[0])) + abs(a[1] - b[1])


def cores_shapez_adjacent(a: Coord, b: Coord) -> bool:
    """True when two extractor cores share an edge on the real (no-x0) map."""

    return shapez_manhattan(a, b) == 1
