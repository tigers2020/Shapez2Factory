"""Mineable-adjacent void topology for Pass1 rim gating (STEP 1, pure domain).

Flood ``asteroid_bbox`` expanded by ``external_margin`` from the rectangle border through
cells that are not in ``mineable`` and not in ``void_flood_extra_blockers``. Belt and
pipe are **not** included in ``void_flood_extra_blockers`` so exterior void matches the
same transport-stripped hull idea as interior inference (``full_barrier − belt − pipe``):
void may traverse belt/pipe lattice sites. Platform/other solid rows remain blockers
for the flood so unrelated map solids do not short-circuit the exterior.

**Pass1 rim:** ``outer_rim_mineable_cells`` — mineable cells with a 4-neighbor in that
exterior void flood.
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
    """Exterior void flood and the single Pass1 rim (external-void-adjacent mineable)."""

    external_void_cells: tuple[BlueprintCell, ...]
    outer_rim_mineable_cells: tuple[BlueprintCell, ...]


def compute_mining_void_topology(
    mineable: frozenset[BlueprintCell],
    bbox: BBox,
    margin: int,
    void_flood_extra_blockers: frozenset[BlueprintCell],
) -> MiningVoidTopology:
    """Border flood; void cannot cross ``mineable`` or ``void_flood_extra_blockers``."""

    xmin, xmax = bbox.min_x - margin, bbox.max_x + margin
    ymin, ymax = bbox.min_y - margin, bbox.max_y + margin

    blocked = mineable | void_flood_extra_blockers

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

    outer_rim: set[BlueprintCell] = set()
    for m in mineable:
        for d in _CARDINAL:
            nxt = step_blueprint_cell(m, d)
            if nxt in external:
                outer_rim.add(m)

    return MiningVoidTopology(
        external_void_cells=tuple(sorted(external, key=_cell_sort_key)),
        outer_rim_mineable_cells=tuple(sorted(outer_rim, key=_cell_sort_key)),
    )


__all__ = ["MiningVoidTopology", "compute_mining_void_topology"]
