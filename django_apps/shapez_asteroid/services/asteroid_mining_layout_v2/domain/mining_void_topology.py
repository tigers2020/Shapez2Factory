"""Mineable-adjacent void topology for Pass1 rim gating (STEP 1, pure domain).

Flood ``asteroid_bbox`` expanded by ``external_margin`` from the rectangle border through
cells that are not in ``mineable`` and not in ``permanent_blocking`` (belt / pipe /
platform / other solid mineable blockers). Classifies **external** vs **internal** void
for diagnostics only. **Pass1 uses a single rim:** ``outer_rim_mineable_cells`` — mineable
cells with a 4-neighbor in external void (true exterior). Internal void has no separate
rim field; when a hole is filled with mineable, that boundary is not a Pass1 rim.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BBox,
    BlueprintCell,
    is_physical_x,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.grid import (
    step_blueprint_cell,
)

_CARDINAL: tuple[tuple[int, int], ...] = ((0, -1), (1, 0), (0, 1), (-1, 0))


def _cell_sort_key(c: BlueprintCell) -> tuple[int, int]:
    return (c[1], c[0])


@dataclass(frozen=True, slots=True)
class MiningVoidTopology:
    """Void sets and the single Pass1 rim (external-void-adjacent mineable) in ``bbox ± margin``."""

    external_void_cells: tuple[BlueprintCell, ...]
    internal_void_cells: tuple[BlueprintCell, ...]
    outer_rim_mineable_cells: tuple[BlueprintCell, ...]


def compute_mining_void_topology(
    mineable: frozenset[BlueprintCell],
    bbox: BBox,
    margin: int,
    permanent_blocking: frozenset[BlueprintCell],
) -> MiningVoidTopology:
    """Border flood in the expanded bbox; mineable and permanent cells block traversal."""

    xmin, xmax = bbox.min_x - margin, bbox.max_x + margin
    ymin, ymax = bbox.min_y - margin, bbox.max_y + margin

    blocked = mineable | permanent_blocking

    def in_rect(c: BlueprintCell) -> bool:
        x, y = c
        return xmin <= x <= xmax and ymin <= y <= ymax

    rect_cells: list[BlueprintCell] = []
    for x in range(xmin, xmax + 1):
        if not is_physical_x(x):
            continue
        for y in range(ymin, ymax + 1):
            rect_cells.append((x, y))

    border: list[BlueprintCell] = []
    for x, y in rect_cells:
        if x == xmin or x == xmax or y == ymin or y == ymax:
            border.append((x, y))

    q: deque[BlueprintCell] = deque()
    external: set[BlueprintCell] = set()
    for c in border:
        if c in blocked:
            continue
        if c not in external:
            external.add(c)
            q.append(c)

    while q:
        cur = q.popleft()
        for d in _CARDINAL:
            nxt = step_blueprint_cell(cur, d)
            if not in_rect(nxt) or nxt in blocked or nxt in external:
                continue
            external.add(nxt)
            q.append(nxt)

    internal: set[BlueprintCell] = set()
    for c in rect_cells:
        if c in blocked or c in external:
            continue
        internal.add(c)

    outer_rim: set[BlueprintCell] = set()
    for m in mineable:
        for d in _CARDINAL:
            nxt = step_blueprint_cell(m, d)
            if nxt in external:
                outer_rim.add(m)

    return MiningVoidTopology(
        external_void_cells=tuple(sorted(external, key=_cell_sort_key)),
        internal_void_cells=tuple(sorted(internal, key=_cell_sort_key)),
        outer_rim_mineable_cells=tuple(sorted(outer_rim, key=_cell_sort_key)),
    )


__all__ = ["MiningVoidTopology", "compute_mining_void_topology"]
