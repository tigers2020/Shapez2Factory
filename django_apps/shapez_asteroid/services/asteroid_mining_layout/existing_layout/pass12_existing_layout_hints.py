"""Pass12 existing-layout solver hint parsing."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord


def _coord_pairs_from_json_list(raw: Any) -> set[Coord]:
    pairs: set[Coord] = set()
    if not isinstance(raw, list):
        return pairs
    for it in raw:
        if isinstance(it, (list, tuple)) and len(it) >= 2:
            x, y = it[0], it[1]
            if isinstance(x, int) and isinstance(y, int) and x != 0:
                pairs.add((x, y))
    return pairs


def pass12_transport_related_block_extra_cells(
    existing_layout_analysis: dict[str, Any] | None,
) -> frozenset[Coord]:
    """Optional coords (not belt/pipe on ``working_map``) treated as transport-block for metrics.

    Belt/pipe occupancy is tracked on ``Pass12LayoutScratch.transport_cells``. This union is
    only explicit STEP 0.5 / replay overlays: fixed stubs, committed route cells, and
    hard/soft protected corridors when listed on ``existing_layout_analysis`` (see plan §Pass12).
    """

    if not isinstance(existing_layout_analysis, dict):
        return frozenset()
    cells: set[Coord] = set()
    for key in (
        "pass12_fixed_output_stub_cells",
        "pass12_committed_route_cells",
        "pass12_hard_protected_corridor_cells",
        "pass12_soft_protected_corridor_cells",
    ):
        cells |= _coord_pairs_from_json_list(existing_layout_analysis.get(key))
    return frozenset(cells)


def solver_hint_coord_union(solver_hints: dict[str, Any]) -> frozenset[Coord]:
    """Parse trunk/cleanup pair lists from §E ``solver_hints``."""

    pairs: set[Coord] = set()
    for key in ("trunk_seed_cell_union", "cleanup_candidate_cell_union"):
        raw = solver_hints.get(key)
        if not isinstance(raw, list):
            continue
        for it in raw:
            if isinstance(it, (list, tuple)) and len(it) >= 2:
                x, y = it[0], it[1]
                if isinstance(x, int) and isinstance(y, int) and x != 0:
                    pairs.add((x, y))
    return frozenset(pairs)


def pass12_existing_layout_barrier_meta(
    existing_layout_analysis: dict[str, Any] | None,
    *,
    mineable: frozenset[Coord],
) -> tuple[frozenset[Coord], dict[str, Any]]:
    """ELA solver_hints -> Pass2 hard_barrier(mineable hints) + summary meta."""

    meta: dict[str, Any] = {
        "existing_layout_source_kind": None,
        "existing_layout_hint_coord_count": 0,
        "existing_layout_barrier_cell_count": 0,
    }
    if not isinstance(existing_layout_analysis, dict):
        return frozenset(), meta
    meta["existing_layout_source_kind"] = existing_layout_analysis.get("source_kind")
    sh = existing_layout_analysis.get("solver_hints")
    if not isinstance(sh, dict):
        return frozenset(), meta
    hinted = solver_hint_coord_union(sh)
    meta["existing_layout_hint_coord_count"] = len(hinted)
    barriers = frozenset(c for c in hinted if c in mineable)
    meta["existing_layout_barrier_cell_count"] = len(barriers)
    return barriers, meta
