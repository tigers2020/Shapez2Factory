"""Orphan same-kind transport island → exterior margin bootstrap (Algorithm §08).

Physical connector only: never writes ``solver_hints.trunk_seed_cell_union`` or
``hard_protected_corridors`` directly. After a successful commit, callers re-run
``analyze_existing_layout_from_mining_map`` so ``main_trunk_candidate`` / trunk seeds
derive from **reachable** transport cells.
"""

from __future__ import annotations

import copy
from collections import deque
from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.existing_layout.existing_layout_analysis import (  # noqa: E501
    analyze_existing_layout_from_mining_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.existing_layout.existing_layout_components import (  # noqa: E501
    role_transport_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    blocked_cells,
    collect_routing_jobs,
    mineable_and_asteroid_coords,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    want_role as routing_want_role,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_goal_trunk_seed import (  # noqa: E501
    exterior_margin_cells,
    trunk_seed_union_from_existing_layout,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_merge_routing import (
    _margin_universe_extra_from_map_list,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_reachability import (
    _probe_transport_materialization_row,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_routing_permission import (  # noqa: E501
    step4_step_cost,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    cells_dict_from_mining_map,
    transport_cells_reaching_external,
    validate_final_mining_layout,
)

MIN_ORPHAN_ISLAND_CELLS = 2

__all__ = [
    "MIN_ORPHAN_ISLAND_CELLS",
    "empty_orphan_island_bootstrap_trace",
    "try_commit_orphan_island_external_bootstrap",
]


def empty_orphan_island_bootstrap_trace() -> dict[str, Any]:
    return {
        "bootstrap_attempted": False,
        "bootstrap_committed": False,
        "bootstrap_transport_kind": None,
        "bootstrap_source_component_id": None,
        "bootstrap_start_cell": None,
        "bootstrap_goal_cell": None,
        "bootstrap_route_length": None,
        "bootstrap_internal_transport_added": None,
        "bootstrap_failure_reason": None,
        "external_reachable_transport_after_bootstrap_count": None,
        "external_reachable_transport_before_bootstrap_count": None,
    }


def _transport_block_for_kind(ela: dict[str, Any], transport_kind: str) -> dict[str, Any] | None:
    if transport_kind == "fluid_pipe":
        t = ela.get("transport")
        if isinstance(t, dict) and str(t.get("transport_kind") or "") == "fluid_pipe":
            return t
        byk = ela.get("transport_by_kind")
        if isinstance(byk, dict):
            fb = byk.get("fluid_pipe")
            if isinstance(fb, dict):
                return fb
    if transport_kind == "shape_belt":
        t = ela.get("transport")
        if isinstance(t, dict) and str(t.get("transport_kind") or "") == "shape_belt":
            return t
        byk = ela.get("transport_by_kind")
        if isinstance(byk, dict):
            sb = byk.get("shape_belt")
            if isinstance(sb, dict):
                return sb
    return None


def _infer_transport_kind_for_bootstrap(ela: dict[str, Any]) -> str | None:
    sk = str(ela.get("source_kind") or "")
    if sk == "existing_fluid_layout":
        return "fluid_pipe"
    if sk == "existing_shape_layout":
        return "shape_belt"
    return None


def _orphan_singleton_component(block: dict[str, Any]) -> dict[str, Any] | None:
    if int(block.get("component_count") or 0) != 1:
        return None
    if block.get("main_component_id") is not None:
        return None
    comps = block.get("components") or []
    if not isinstance(comps, list) or len(comps) != 1:
        return None
    row = comps[0]
    if not isinstance(row, dict):
        return None
    if str(row.get("status") or "") != "orphan_component":
        return None
    if int(row.get("cell_count") or 0) < MIN_ORPHAN_ISLAND_CELLS:
        return None
    return row


def _parse_component_cells(comp: dict[str, Any]) -> frozenset[Coord]:
    raw = comp.get("cells") or []
    out: set[Coord] = set()
    if not isinstance(raw, list):
        return frozenset()
    for pair in raw:
        if isinstance(pair, (list, tuple)) and len(pair) >= 2:
            x, y = int(pair[0]), int(pair[1])
            if x != 0:
                out.add((x, y))
    return frozenset(out)


def _external_reachable_same_kind_count(
    cells: dict[Coord, dict[str, Any]],
    *,
    transport_kind: str,
    is_external: Callable[[Coord], bool],
) -> int:
    wr = routing_want_role(transport_kind)
    tset = role_transport_cells(cells, wr)
    if not tset:
        return 0
    reach = transport_cells_reaching_external(set(tset), set(blocked_cells(cells)), is_external)
    return len(reach)


def _bfs_connector_to_margin(
    *,
    cells: dict[Coord, dict[str, Any]],
    orphan: frozenset[Coord],
    margin: set[Coord],
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    want_wr: str,
) -> tuple[list[Coord], Coord] | None:
    """Return (path including orphan tail .. goal_cell) or None.

    Path is ordered from some ``o in orphan`` through Stepping cells to ``goal_cell`` in margin.
    """

    if not margin:
        return None
    parent: dict[Coord, Coord | None] = {}
    q: deque[Coord] = deque()
    for o in orphan:
        parent[o] = None
        q.append(o)
    visited = set(orphan)
    goal_cell: Coord | None = None
    while q:
        c = q.popleft()
        if c in margin and c not in orphan:
            goal_cell = c
            break
        x, y = c
        for n in neighbors4(x, y):
            if n in visited:
                continue
            if n in orphan:
                visited.add(n)
                parent[n] = c
                q.append(n)
                continue
            sc = step4_step_cost(
                n,
                want_role=want_wr,
                cells=cells,
                mineable=mineable,
                asteroid=asteroid,
                is_external=is_external,
                cheap_reuse_cells=None,
            )
            if sc is None:
                continue
            visited.add(n)
            parent[n] = c
            q.append(n)
            if n in margin:
                goal_cell = n
                break
        if goal_cell is not None:
            break
    if goal_cell is None:
        return None
    path_rev: list[Coord] = []
    cur: Coord | None = goal_cell
    while cur is not None:
        path_rev.append(cur)
        cur = parent.get(cur)
    path = list(reversed(path_rev))
    return path, goal_cell


def _apply_new_transport_rows(
    map_rows: list[dict[str, Any]],
    new_segments: dict[Coord, dict[str, Any]],
) -> None:
    by_xy: dict[Coord, int] = {}
    for i, row in enumerate(map_rows):
        x, y = row.get("x"), row.get("y")
        if isinstance(x, int) and isinstance(y, int) and x != 0:
            by_xy[(x, y)] = i
    for c, row in new_segments.items():
        if c in by_xy:
            map_rows[by_xy[c]] = row
        else:
            map_rows.append(row)


def try_commit_orphan_island_external_bootstrap(
    *,
    mining_map_rows: list[dict[str, Any]],
    final_mining_map: list[dict[str, Any]],
    is_external: Callable[[Coord], bool],
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Optionally mutate ``mining_map_rows`` in-place; return (trace, fresh_ela_or_none).

    ``fresh_ela`` is returned only when ``bootstrap_committed`` is True (re-analyzed map).
    """

    trace = empty_orphan_island_bootstrap_trace()
    ela0 = analyze_existing_layout_from_mining_map(mining_map_rows, is_external=is_external)
    tk = _infer_transport_kind_for_bootstrap(ela0)
    if tk is None:
        trace["bootstrap_failure_reason"] = "ineligible_source_kind"
        return trace, None

    block = _transport_block_for_kind(ela0, tk)
    if not isinstance(block, dict):
        trace["bootstrap_failure_reason"] = "no_transport_block"
        return trace, None

    orphan_comp = _orphan_singleton_component(block)
    if orphan_comp is None:
        trace["bootstrap_failure_reason"] = "no_orphan_island_pattern"
        return trace, None

    trace["bootstrap_attempted"] = True
    trace["bootstrap_transport_kind"] = tk
    trace["bootstrap_source_component_id"] = int(orphan_comp.get("component_id", -1))

    trial_map = copy.deepcopy(mining_map_rows)
    cells = {k: dict(v) for k, v in cells_dict_from_mining_map(trial_map).items()}
    mineable, asteroid = mineable_and_asteroid_coords(final_mining_map)
    want_wr = routing_want_role(tk)

    ext_before = _external_reachable_same_kind_count(
        cells, transport_kind=tk, is_external=is_external
    )
    trace["external_reachable_transport_before_bootstrap_count"] = ext_before
    if ext_before > 0:
        trace["bootstrap_failure_reason"] = "already_external_reachable_transport"
        return trace, None

    jobs = collect_routing_jobs(cells)
    if not any(j[2] == tk for j in jobs):
        trace["bootstrap_failure_reason"] = "no_matching_miner_jobs"
        return trace, None

    orphan = _parse_component_cells(orphan_comp)
    if len(orphan) < MIN_ORPHAN_ISLAND_CELLS:
        trace["bootstrap_failure_reason"] = "orphan_too_small"
        return trace, None

    margin_universe_extra = _margin_universe_extra_from_map_list(
        trial_map, cells_keys=set(cells.keys())
    )
    margin = exterior_margin_cells(
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        is_external=is_external,
        universe_extra=margin_universe_extra,
    )

    bfs = _bfs_connector_to_margin(
        cells=cells,
        orphan=orphan,
        margin=margin,
        mineable=mineable,
        asteroid=asteroid,
        is_external=is_external,
        want_wr=want_wr,
    )
    if bfs is None:
        trace["bootstrap_failure_reason"] = "geometry_no_path"
        return trace, None
    path, goal_cell = bfs
    new_coords = [c for c in path if c not in orphan]
    if not new_coords:
        trace["bootstrap_failure_reason"] = "no_new_connector_cells"
        return trace, None

    start_cell = path[0] if path and path[0] in orphan else next(iter(orphan))
    trace["bootstrap_start_cell"] = [int(start_cell[0]), int(start_cell[1])]
    trace["bootstrap_goal_cell"] = [int(goal_cell[0]), int(goal_cell[1])]
    trace["bootstrap_route_length"] = int(len(path))

    new_segments: dict[Coord, dict[str, Any]] = {}
    for c in new_coords:
        new_segments[c] = _probe_transport_materialization_row(c, transport_kind=tk)
        cells[c] = dict(new_segments[c])

    _apply_new_transport_rows(trial_map, new_segments)

    report = validate_final_mining_layout(trial_map)
    if not report.geometry_valid or not report.connectivity_valid:
        trace["bootstrap_failure_reason"] = "commit_validation_failed"
        return trace, None

    ext_after = _external_reachable_same_kind_count(
        cells, transport_kind=tk, is_external=is_external
    )
    trace["external_reachable_transport_after_bootstrap_count"] = ext_after
    if ext_after <= 0:
        trace["bootstrap_failure_reason"] = "post_commit_not_external_reachable"
        return trace, None

    mining_map_rows[:] = trial_map
    trace["bootstrap_committed"] = True
    trace["bootstrap_internal_transport_added"] = int(len(new_coords))
    ela1 = analyze_existing_layout_from_mining_map(mining_map_rows, is_external=is_external)
    return trace, ela1


def trunk_seed_hint_count_from_ela(ela: dict[str, Any] | None) -> int:
    """Telemetry helper: count coords in ``trunk_seed_cell_union`` (main trunk hint only)."""

    if not ela:
        return 0
    return len(trunk_seed_union_from_existing_layout(ela))
