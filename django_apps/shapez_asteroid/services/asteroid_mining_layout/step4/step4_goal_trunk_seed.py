"""STEP4 trunk seed + goal set skeleton (§08 merge-aware routing MVP).

``trunk_seed_cell_union`` from existing layout analysis excludes orphan/single-cell
artifacts (they live under ``cleanup_candidate_cell_union`` in ELA).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    EXTRACTORS_FLUID,
    EXTRACTORS_SHAPE,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    layout_kind as _layout_kind,
)

__all__ = [
    "build_step4_goal_set",
    "build_trunk_seed_candidates_by_kind",
    "exterior_margin_cells",
    "trunk_seed_union_from_existing_layout",
]


def exterior_margin_cells(
    *,
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    cells: dict[Coord, dict[str, Any]],
    is_external: Callable[[Coord], bool],
) -> set[Coord]:
    """Cells in the routing universe with at least one ``is_external`` 4-neighbor."""

    universe = set(cells.keys()) | set(mineable) | set(asteroid)
    out: set[Coord] = set()
    for c in universe:
        x, y = c
        if x == 0:
            continue
        for n in neighbors4(x, y):
            if is_external(n):
                out.add(c)
                break
    return out


def trunk_seed_union_from_existing_layout(
    existing_layout_analysis: dict[str, Any] | None,
) -> set[Coord]:
    """Parse ``solver_hints.trunk_seed_cell_union`` (main_trunk_candidate only, §E)."""

    if not existing_layout_analysis:
        return set()
    sh = existing_layout_analysis.get("solver_hints")
    if not isinstance(sh, dict):
        return set()
    raw = sh.get("trunk_seed_cell_union")
    if not isinstance(raw, list):
        return set()
    out: set[Coord] = set()
    for pair in raw:
        if isinstance(pair, (list, tuple)) and len(pair) >= 2:
            x, y = int(pair[0]), int(pair[1])
            if x != 0:
                out.add((x, y))
    return out


def _hint_cell_transport_kinds(c: Coord, cells: dict[Coord, dict[str, Any]]) -> set[str]:
    """Map a hinted cell to transport kinds that may treat it as same-kind trunk seed."""

    row = cells.get(c)
    if row is None:
        return {"shape_belt", "fluid_pipe"}
    role = row.get("role")
    if role == "belt":
        return {"shape_belt"}
    if role == "pipe":
        return {"fluid_pipe"}
    lk = _layout_kind(row)
    if lk is None:
        return set()
    if lk in EXTRACTORS_SHAPE:
        return {"shape_belt"}
    if lk in EXTRACTORS_FLUID:
        return {"fluid_pipe"}
    return set()


def build_trunk_seed_candidates_by_kind(
    *,
    exterior_margin: set[Coord],
    hint_union: set[Coord],
    cells: dict[Coord, dict[str, Any]],
) -> dict[str, set[Coord]]:
    """Per-``TransportKind`` union: exterior margin ∪ same-kind ELA trunk_seed cells."""

    out: dict[str, set[Coord]] = {
        "shape_belt": set(exterior_margin),
        "fluid_pipe": set(exterior_margin),
    }
    for c in hint_union:
        for tk in _hint_cell_transport_kinds(c, cells):
            out.setdefault(tk, set()).add(c)
    return out


def build_step4_goal_set(
    kind: str,
    *,
    committed_trunk_by_kind: dict[str, set[Coord]],
    exterior_margin_cells: set[Coord],
    trunk_seed_candidates_by_kind: dict[str, set[Coord]],
) -> set[Coord]:
    """§3.2: first-route vs subsequent-route goal set (set semantics, before ``frozenset``)."""

    existing = set(committed_trunk_by_kind.get(kind, ()))
    if existing:
        return existing | set(exterior_margin_cells)
    seeds = set(trunk_seed_candidates_by_kind.get(kind, ()))
    return seeds | set(exterior_margin_cells)
