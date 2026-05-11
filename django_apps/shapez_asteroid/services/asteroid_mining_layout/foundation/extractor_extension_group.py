"""Blueprint-only maximized extractor group: extensions owned via parent-facing ``r``.

``layout_kind`` in ``EXTENSIONS`` uses the same ``r`` convention as Pass1 merge
(``output_offset_r`` = step toward parent). Owned extensions are the least fixpoint of
``parent(ext) in {extractor} ∪ owned`` (no plain adjacency counting).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import output_offset_r
from django_apps.shapez_asteroid.extraction.shapez_grid import step_cardinal
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    EXTENSIONS,
    PASS12_MAX_EXTENSION_TILES,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    layout_kind,
)

__all__ = [
    "extension_parent_coord",
    "owned_extension_cells_for_extractor",
    "route_extractor_is_maximized_group",
]


def extension_parent_coord(cell: Coord, row: Mapping[str, Any]) -> Coord | None:
    """Parent cell of an extension row using ``r`` → cardinal step; ``None`` if unresolved."""

    if layout_kind(row) not in EXTENSIONS:
        return None
    raw_r = row.get("r")
    if not isinstance(raw_r, int):
        return None
    dx, dy = output_offset_r(raw_r)
    return step_cardinal(cell[0], cell[1], dx, dy)


def owned_extension_cells_for_extractor(
    cells: Mapping[Coord, Mapping[str, Any]],
    extractor_cell: Coord,
) -> frozenset[Coord]:
    """Extensions whose parent chain reaches ``extractor_cell`` (orientation-resolved)."""

    owned: set[Coord] = set()
    # Monotone closure: add ext when parent is extractor or already-owned extension.
    changed = True
    while changed:
        changed = False
        for c in sorted(cells.keys(), key=lambda p: (p[1], p[0])):
            if c in owned:
                continue
            row = cells.get(c)
            if row is None:
                continue
            if layout_kind(row) not in EXTENSIONS:
                continue
            p = extension_parent_coord(c, row)
            if p is None:
                continue
            if p == extractor_cell or p in owned:
                owned.add(c)
                changed = True
    return frozenset(owned)


def route_extractor_is_maximized_group(
    *,
    extractor_cell: Coord,
    placement_id: str | None,
    placement_records: Mapping[str, Any] | None,
    cells: Mapping[Coord, Mapping[str, Any]],
) -> bool:
    """True iff this extractor has exactly ``PASS12_MAX_EXTENSION_TILES`` owned extensions."""

    if placement_id and placement_records is not None and placement_id in placement_records:
        rec = placement_records[placement_id]
        ext_cells = getattr(rec, "extension_cells", None)
        if ext_cells is None and isinstance(rec, Mapping):
            ext_cells = rec.get("extension_cells")
        if ext_cells is None:
            return False
        return len(tuple(ext_cells)) == PASS12_MAX_EXTENSION_TILES
    return len(owned_extension_cells_for_extractor(cells, extractor_cell)) == PASS12_MAX_EXTENSION_TILES
