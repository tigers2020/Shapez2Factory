"""STEP4 trunk seed + route goal set skeleton (§08 merge-aware routing MVP).

``trunk_seed_cell_union`` lists **main_trunk_candidate** cells only; orphan / single-cell
artifacts live in ``cleanup_candidate_cell_union`` (ELA) and are **never** read here — see
:func:`trunk_seed_union_from_existing_layout`.

**Terminology (Algorithm §08):**

- **Trunk seed candidates** (``build_trunk_seed_candidates_by_kind``): per ``TransportKind``,
  ``exterior_margin ∪`` same-kind cells from ``trunk_seed_cell_union``.
- **Raw goal set** (``build_step4_goal_set``): first-route → ``candidates ∪ margin``; later →
  ``committed_trunk_by_kind[kind] ∪ margin`` for this STEP4 run only.
- **Dijkstra goal_cells**: ``merge_goal_union_meta`` unions that raw set with **live**
  same-kind exterior-connected trunk from the working map (merge-aware termination).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
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
    "diagnose_trunk_seed_candidate_zero_for_kind",
    "diagnose_trunk_seed_pool_empty",
    "exterior_margin_cells",
    "trunk_seed_union_from_existing_layout",
]


def exterior_margin_cells(
    *,
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    cells: dict[Coord, dict[str, Any]],
    is_external: Callable[[Coord], bool],
    universe_extra: frozenset[Coord] = frozenset(),
) -> set[Coord]:
    """Cells in the routing universe with at least one ``is_external`` 4-neighbor.

    ``universe_extra``: coordinates not guaranteed under ``cells`` keys / mineable / asteroid
    (e.g. Pass2 probe-time belt tiles) that must still be considered for margin adjacency.
    """

    universe = set(cells.keys()) | set(mineable) | set(asteroid) | set(universe_extra)
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
    """Parse ``solver_hints.trunk_seed_cell_union`` (main_trunk_candidate only, §E).

    ``cleanup_candidate_cell_union`` and other ELA keys are **ignored** here so orphans and
    single-cell artifacts never enter trunk seed candidates.
    """

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


def diagnose_trunk_seed_pool_empty(
    *,
    existing_layout_analysis: dict[str, Any] | None,
    cells: dict[Coord, dict[str, Any]],
    margin_cells: set[Coord],
    trunk_seed_by_kind: Mapping[str, set[Coord]],
) -> str | None:
    """Telemetry-only reason when max per-kind trunk seed pool size is zero."""

    mx = max(
        (len(trunk_seed_by_kind.get(k, ())) for k in ("shape_belt", "fluid_pipe")),
        default=0,
    )
    if mx > 0:
        return None
    if not existing_layout_analysis:
        return "no_existing_layout_context"
    hint = trunk_seed_union_from_existing_layout(existing_layout_analysis)
    margin_n = len(margin_cells)
    if not hint:
        if margin_n == 0:
            return "exterior_margin_empty_and_no_seed"
        return "no_main_component"
    if hint and not any(_hint_cell_transport_kinds(c, cells) for c in hint):
        return "main_component_wrong_kind"
    return "all_candidates_filtered_by_policy"


def diagnose_trunk_seed_candidate_zero_for_kind(
    *,
    transport_kind: str,
    existing_layout_analysis: dict[str, Any] | None,
    cells: dict[Coord, dict[str, Any]],
    margin_cells: set[Coord],
    seeds_for_kind: set[Coord],
    existing_reaching: set[Coord],
) -> str | None:
    """Pass2: empty per-kind trunk seed pool (``trunk_seed_candidate_count == 0``)."""

    if len(seeds_for_kind) > 0:
        return None
    if not existing_layout_analysis:
        return "no_existing_layout_context"
    hint = trunk_seed_union_from_existing_layout(existing_layout_analysis)
    margin_n = len(margin_cells)
    if not hint:
        if margin_n == 0:
            return "exterior_margin_empty_and_no_seed"
        return "no_main_component"
    if not any(transport_kind in _hint_cell_transport_kinds(c, cells) for c in hint):
        return "main_component_wrong_kind"
    if margin_n == 0 and not existing_reaching:
        return "main_component_not_external_reachable"
    return "all_candidates_filtered_by_policy"


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
    """§08: raw route goal set **before** merging live map trunk cells.

    **First route (per kind, this STEP4 run):** no cells in ``committed_trunk_by_kind[kind]`` yet
    → ``trunk_seed_candidates_by_kind[kind] ∪ exterior_margin_cells`` (candidates already
    include margin; union keeps the contract explicit).

    **Later routes:** once this run has committed at least one same-kind trunk cell for
    ``kind``, goals are ``committed_trunk_by_kind[kind] ∪ exterior_margin_cells`` only (ELA
    trunk_seed hints are not re-added — merge targets come from committed paths + margin).

    The working-map exterior-connected trunk (same role) is unioned in
    ``merge_goal_union_meta`` for Dijkstra ``goal_cells`` (merge-aware termination).
    """

    existing = set(committed_trunk_by_kind.get(kind, ()))
    if existing:
        return existing | set(exterior_margin_cells)
    seeds = set(trunk_seed_candidates_by_kind.get(kind, ()))
    return seeds | set(exterior_margin_cells)
