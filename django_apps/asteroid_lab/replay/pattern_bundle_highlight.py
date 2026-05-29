"""Pattern bundle highlight wire for Lab replay (output-only).

Must not be imported by solver placement, routing, validation, or optimization input code.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from django_apps.asteroid_lab.reconstruction.cell_hull_outline import (
    build_cell_hull_outline_loops,
)
from django_apps.asteroid_lab.snapshots.grid_contract import Coord

METRICS_KEY = "pattern_bundle_highlights"
PALETTE_SIZE = 8
_WIRE_VERSION = 1

_EDGE_NEIGHBOR_OFFSETS: tuple[tuple[int, int], ...] = (
    (0, -1),
    (1, 0),
    (0, 1),
    (-1, 0),
)


class _RimPlacementMiningSource(Protocol):
    extractor_cells: frozenset[Coord]
    extension_cells: frozenset[Coord]
    output_stub_cells: frozenset[Coord]


def mining_occupied_from_rim_placement(placement: _RimPlacementMiningSource) -> frozenset[Coord]:
    """Equipment footprint for L4 highlights (stub/route excluded)."""

    _ = placement.output_stub_cells
    return placement.extractor_cells | placement.extension_cells


def _bundles_adjacent(a: frozenset[Coord], b: frozenset[Coord]) -> bool:
    for x, y in a:
        for dx, dy in _EDGE_NEIGHBOR_OFFSETS:
            if (x + dx, y + dy) in b:
                return True
    return False


def _bundles_share_cells(a: frozenset[Coord], b: frozenset[Coord]) -> bool:
    return bool(a & b)


def _bundles_conflict(a: frozenset[Coord], b: frozenset[Coord]) -> bool:
    """Adjacent or overlapping footprints cannot share a palette slot."""

    if not a or not b:
        return False
    if _bundles_share_cells(a, b):
        return True
    return _bundles_adjacent(a, b)


def assign_bundle_color_indices(
    bundle_occupied_sets: Sequence[frozenset[Coord]],
) -> tuple[int, ...]:
    """Greedy graph coloring on bundle footprint conflict (stable input order)."""

    n = len(bundle_occupied_sets)
    if n == 0:
        return ()
    colors: list[int | None] = [None] * n
    for i in range(n):
        used: set[int] = set()
        for j in range(n):
            if j == i or colors[j] is None:
                continue
            if _bundles_conflict(bundle_occupied_sets[i], bundle_occupied_sets[j]):
                used.add(colors[j])
        pick = 0
        while pick in used:
            pick += 1
        colors[i] = pick % PALETTE_SIZE
    return tuple(c if c is not None else 0 for c in colors)


def build_pattern_bundle_highlights_wire(
    entries: Sequence[tuple[str, frozenset[Coord], str | None]],
) -> dict[str, object]:
    """Build ``pattern_bundle_highlights`` metrics payload or ``{}`` when empty."""

    sorted_entries = sorted(entries, key=lambda row: row[0])
    active = [(key, occ, gene) for key, occ, gene in sorted_entries if occ]
    if not active:
        return {}

    color_indices = assign_bundle_color_indices(tuple(occ for _key, occ, _gene in active))
    bundles: list[dict[str, Any]] = []
    for i, (bundle_key, occupied, gene_key) in enumerate(active):
        loops = build_cell_hull_outline_loops(occupied)
        if not loops:
            continue
        entry: dict[str, Any] = {
            "bundle_key": bundle_key,
            "color_index": color_indices[i],
            "outline_loops": [[[int(x), int(y)] for x, y in loop] for loop in loops],
        }
        if gene_key:
            entry["gene_key"] = gene_key
        bundles.append(entry)

    if not bundles:
        return {}

    return {"version": _WIRE_VERSION, "bundles": bundles}


__all__ = [
    "METRICS_KEY",
    "PALETTE_SIZE",
    "assign_bundle_color_indices",
    "build_pattern_bundle_highlights_wire",
    "mining_occupied_from_rim_placement",
]
