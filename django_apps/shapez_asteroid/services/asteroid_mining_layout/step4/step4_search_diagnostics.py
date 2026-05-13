"""STEP4 merge search diagnostics: Manhattan goal pre-stats and deterministic goal priority."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord

STEP4_SEARCH_GOAL_ORDERING_MODE = "trunk_manhattan_margin_lex"

_DISTANCE_BUCKETS: tuple[tuple[int, int, str], ...] = (
    (0, 4, "0-4"),
    (5, 8, "5-8"),
    (9, 12, "9-12"),
    (13, 16, "13-16"),
)

_SEARCH_STATS_DIAG_KEYS: frozenset[str] = frozenset(
    {
        "nearest_goal_distance_estimate",
        "goal_count_by_distance_bucket",
        "first_goal_candidate",
        "max_frontier_size",
        "frontier_stop_reason",
        "goal_ordering_mode",
        "exterior_fallback_considered",
        "exterior_fallback_activated",
        "exterior_fallback_reason",
        "primary_existing_trunk_reachable_count",
        "fallback_external_goal_count",
        "heap_pops",
        "stop_reason",
        "dijkstra_reachable_goal_count",
        "dijkstra_reachable_trunk_goal_count",
        "dijkstra_reachable_margin_goal_count",
    }
)


def manhattan_stub_goal(stub_cell: Coord, c: Coord) -> int:
    return abs(int(c[0]) - int(stub_cell[0])) + abs(int(c[1]) - int(stub_cell[1]))


def goal_count_by_distance_bucket(stub_cell: Coord, goal_cells: frozenset[Coord]) -> dict[str, int]:
    out: dict[str, int] = {t[2]: 0 for t in _DISTANCE_BUCKETS}
    out["17+"] = 0
    for c in goal_cells:
        d = manhattan_stub_goal(stub_cell, c)
        placed = False
        for lo, hi, label in _DISTANCE_BUCKETS:
            if lo <= d <= hi:
                out[label] += 1
                placed = True
                break
        if not placed:
            out["17+"] += 1
    return out


def nearest_goal_manhattan_and_first(
    stub_cell: Coord, goal_cells: frozenset[Coord]
) -> tuple[float | None, list[int] | None]:
    """Minimum Manhattan stub→goal; tie ``(abs Δy, abs Δx, y, x)`` on goals achieving the min."""

    if not goal_cells:
        return None, None
    md = min(manhattan_stub_goal(stub_cell, c) for c in goal_cells)
    bests = [c for c in goal_cells if manhattan_stub_goal(stub_cell, c) == md]
    sx, sy = stub_cell
    first = min(bests, key=lambda c: (abs(int(c[1]) - sy), abs(int(c[0]) - sx), c[1], c[0]))
    return float(md), [int(first[0]), int(first[1])]


def merge_goal_union_meta(
    stub_cell: Coord,
    *,
    raw_goal: set[Coord],
    trunk_cells: frozenset[Coord],
    margin_cells: set[Coord],
) -> tuple[frozenset[Coord], dict[str, Any]]:
    """Build Dijkstra ``goal_cells`` = raw §08 goal set ∪ **live** same-kind exterior trunk.

    ``raw_goal`` comes from :func:`build_step4_goal_set` (trunk_seed ∪ margin, or committed ∪
    margin). ``trunk_cells`` is the current map's same-role transport that reaches exterior;
    unioning it is required so the first search can terminate on an existing preserved trunk
    even when ``committed_trunk_by_kind`` is still empty. ``priority_head`` is deterministic
    telemetry only (tier: live trunk → margin → other raw goals).
    """

    union = frozenset(raw_goal | set(trunk_cells))
    if not union:
        return union, {"applied": False, "mode": "none", "priority_head": ()}
    trunk_set = set(trunk_cells)
    margin_set = margin_cells

    def tier(c: Coord) -> int:
        if c in trunk_set:
            return 0
        if c in margin_set:
            return 1
        return 2

    ordered = sorted(
        union,
        key=lambda c: (tier(c), manhattan_stub_goal(stub_cell, c), c[1], c[0]),
    )
    head = tuple([int(c[0]), int(c[1])] for c in ordered[:32])
    return union, {
        "applied": True,
        "mode": STEP4_SEARCH_GOAL_ORDERING_MODE,
        "priority_head": head,
    }


def fill_goal_geometry_search_stats(
    stub_cell: Coord,
    goal_cells: frozenset[Coord] | None,
    search_stats: dict[str, Any],
) -> None:
    """Pre-search Manhattan diagnostics (does not depend on Dijkstra traversal)."""

    if goal_cells:
        nd, fg = nearest_goal_manhattan_and_first(stub_cell, goal_cells)
        search_stats["nearest_goal_distance_estimate"] = nd
        search_stats["first_goal_candidate"] = fg
        search_stats["goal_count_by_distance_bucket"] = goal_count_by_distance_bucket(
            stub_cell, goal_cells
        )
    else:
        search_stats.setdefault("nearest_goal_distance_estimate", None)
        search_stats.setdefault("first_goal_candidate", None)
        search_stats.setdefault("goal_count_by_distance_bucket", {})


def copy_search_diagnostics_to_detail(detail: dict[str, Any], search_stats: dict[str, Any]) -> None:
    for k in _SEARCH_STATS_DIAG_KEYS:
        if k in search_stats:
            detail[k] = search_stats[k]


def search_stats_diagnostic_extras(search_stats: dict[str, Any]) -> dict[str, Any]:
    """Subset of ``search_stats`` for ``build_step4_route_failure_diagnostic`` replay rows."""

    return {k: search_stats[k] for k in sorted(_SEARCH_STATS_DIAG_KEYS) if k in search_stats}
