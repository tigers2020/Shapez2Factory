"""STEP4 route-failure replay overlay (output-only; never used for routing decisions).

Bounded, deterministic coordinate samples for STEP10 / ``solver_replay`` consumers.
See ``documents/Algorithm/mining_solver_cursor_sessions/14_step10_replay_ui.md`` §16.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridor_read_factory import (  # noqa: E501
    protected_corridors_overlay_from_routing_state,
)

STEP4_REPLAY_OVERLAY_VERSION = 1

# Row-level caps (single failure).
_ROW_COORD_SAMPLE_CAP = 48
_ROW_FRONTIER_SAMPLE_CAP = 32

# Aggregate caps (merged across failures + corridors).
_AGG_COORD_SAMPLE_CAP = 96
_AGG_FRONTIER_SAMPLE_CAP = 64
_AGG_NEAREST_BLOCKED_CAP = 24
_CORRIDOR_COORD_CAP = 128


def _sorted_cell_pairs(cells: frozenset[Coord] | set[Coord], *, limit: int) -> list[list[int]]:
    if not cells or limit <= 0:
        return []
    ordered = sorted(cells, key=lambda c: (int(c[1]), int(c[0])))
    return [[int(c[0]), int(c[1])] for c in ordered[:limit]]


def build_step4_row_replay_overlay(
    *,
    placement_id: str | None,
    stub_cell: Coord,
    near: Sequence[Mapping[str, Any]],
    nearest_blocked_cell: list[int] | None,
    nearest_blocked_zone: str | None,
    goal_cells: frozenset[Coord],
    reachable_goals: frozenset[Coord],
    trunk_cells: frozenset[Coord],
    margin_cells: set[Coord],
    trunk_seed_cells: frozenset[Coord] | None,
) -> dict[str, Any]:
    """Per-failure-row overlay (JSON-friendly; small)."""

    frontier: list[list[int]] = []
    seen: set[tuple[int, int]] = set()
    for entry in near:
        if not isinstance(entry, Mapping):
            continue
        reason = str(entry.get("reason") or "")
        if reason == "ok":
            continue
        cell = entry.get("cell")
        if not isinstance(cell, (list, tuple)) or len(cell) < 2:
            continue
        try:
            pair = (int(cell[0]), int(cell[1]))
        except (TypeError, ValueError):
            continue
        if pair in seen or pair[0] == 0:
            continue
        seen.add(pair)
        frontier.append([pair[0], pair[1]])
    frontier.sort(key=lambda p: (p[1], p[0]))
    frontier = frontier[:_ROW_FRONTIER_SAMPLE_CAP]

    nb_cells: list[list[int]] = []
    nb_zones: list[str | None] = []
    if nearest_blocked_cell is not None and len(nearest_blocked_cell) >= 2:
        try:
            nb_cells.append([int(nearest_blocked_cell[0]), int(nearest_blocked_cell[1])])
        except (TypeError, ValueError):
            pass
        nb_zones.append(nearest_blocked_zone)

    ts = trunk_seed_cells or frozenset()
    margin_fs = frozenset(margin_cells)
    pids: list[str] = []
    if isinstance(placement_id, str) and placement_id:
        pids.append(placement_id)
    return {
        "overlay_version": STEP4_REPLAY_OVERLAY_VERSION,
        "failed_stub_cells": [[int(stub_cell[0]), int(stub_cell[1])]],
        "failed_placement_ids": pids,
        "blocked_frontier_sample": frontier,
        "nearest_blocked_cell": nb_cells,
        "nearest_blocked_zone": nb_zones,
        "route_goal_cells_sample": _sorted_cell_pairs(goal_cells, limit=_ROW_COORD_SAMPLE_CAP),
        "reachable_goal_cells_sample": _sorted_cell_pairs(
            reachable_goals, limit=_ROW_COORD_SAMPLE_CAP
        ),
        "existing_trunk_cells_sample": _sorted_cell_pairs(trunk_cells, limit=_ROW_COORD_SAMPLE_CAP),
        "trunk_seed_cells_sample": _sorted_cell_pairs(ts, limit=_ROW_COORD_SAMPLE_CAP),
        "exterior_margin_cells_sample": _sorted_cell_pairs(margin_fs, limit=_ROW_COORD_SAMPLE_CAP),
    }


def merge_step4_route_failure_replay_overlay(
    *,
    routing_failures: Sequence[Mapping[str, Any]],
    routing_state: Mapping[str, Any] | None,
    quarantined_placements: Sequence[str],
    rolled_back_placements: Sequence[str],
) -> dict[str, Any]:
    """Merge row overlays + routing_state corridors into one bounded replay blob."""

    stubs: list[list[int]] = []
    frontier_acc: list[list[int]] = []
    goals_acc: list[list[int]] = []
    reach_acc: list[list[int]] = []
    trunk_acc: list[list[int]] = []
    seed_acc: list[list[int]] = []
    margin_acc: list[list[int]] = []
    nb_cells: list[list[int]] = []
    nb_zones: list[str | None] = []

    seen_stub: set[tuple[int, int]] = set()
    seen_pid: set[str] = set()
    seen_frontier: set[tuple[int, int]] = set()
    seen_goals: set[tuple[int, int]] = set()
    seen_reach: set[tuple[int, int]] = set()
    seen_trunk: set[tuple[int, int]] = set()
    seen_seed: set[tuple[int, int]] = set()
    seen_margin: set[tuple[int, int]] = set()

    def _take_pairs(
        src: list[list[int]],
        into: list[list[int]],
        cap: int,
        seen: set[tuple[int, int]],
    ) -> None:
        for p in src:
            if len(into) >= cap:
                return
            if len(p) < 2:
                continue
            try:
                t = (int(p[0]), int(p[1]))
            except (TypeError, ValueError):
                continue
            if t[0] == 0 or t in seen:
                continue
            seen.add(t)
            into.append([t[0], t[1]])

    for row in routing_failures:
        if not isinstance(row, Mapping):
            continue
        det = row.get("step4_route_failure_detail")
        ov = det.get("step4_replay_overlay") if isinstance(det, Mapping) else None
        if not isinstance(ov, Mapping):
            continue
        for p in ov.get("failed_stub_cells") or []:
            if isinstance(p, (list, tuple)) and len(p) >= 2 and len(stubs) < _AGG_COORD_SAMPLE_CAP:
                try:
                    t = (int(p[0]), int(p[1]))
                except (TypeError, ValueError):
                    continue
                if t[0] == 0 or t in seen_stub:
                    continue
                seen_stub.add(t)
                stubs.append([t[0], t[1]])
        for pid in ov.get("failed_placement_ids") or []:
            if isinstance(pid, str) and pid:
                seen_pid.add(pid)
        bf = list(ov.get("blocked_frontier_sample") or [])
        _take_pairs(bf, frontier_acc, _AGG_FRONTIER_SAMPLE_CAP, seen_frontier)
        rg = list(ov.get("route_goal_cells_sample") or [])
        _take_pairs(rg, goals_acc, _AGG_COORD_SAMPLE_CAP, seen_goals)
        rr = list(ov.get("reachable_goal_cells_sample") or [])
        _take_pairs(rr, reach_acc, _AGG_COORD_SAMPLE_CAP, seen_reach)
        et = list(ov.get("existing_trunk_cells_sample") or [])
        _take_pairs(et, trunk_acc, _AGG_COORD_SAMPLE_CAP, seen_trunk)
        ss = list(ov.get("trunk_seed_cells_sample") or [])
        _take_pairs(ss, seed_acc, _AGG_COORD_SAMPLE_CAP, seen_seed)
        em = list(ov.get("exterior_margin_cells_sample") or [])
        _take_pairs(em, margin_acc, _AGG_COORD_SAMPLE_CAP, seen_margin)
        for i, cell in enumerate(ov.get("nearest_blocked_cell") or []):
            if len(nb_cells) >= _AGG_NEAREST_BLOCKED_CAP:
                break
            if isinstance(cell, (list, tuple)) and len(cell) >= 2:
                try:
                    nb_cells.append([int(cell[0]), int(cell[1])])
                except (TypeError, ValueError):
                    continue
                zl = ov.get("nearest_blocked_zone") or []
                z = zl[i] if i < len(zl) else None
                nb_zones.append(z if isinstance(z, str) else None)

    stubs.sort(key=lambda p: (p[1], p[0]))
    pids_out = sorted(seen_pid)
    frontier_acc.sort(key=lambda p: (p[1], p[0]))
    goals_acc.sort(key=lambda p: (p[1], p[0]))
    reach_acc.sort(key=lambda p: (p[1], p[0]))
    trunk_acc.sort(key=lambda p: (p[1], p[0]))
    seed_acc.sort(key=lambda p: (p[1], p[0]))
    margin_acc.sort(key=lambda p: (p[1], p[0]))

    pc = protected_corridors_overlay_from_routing_state(routing_state)
    hard = list(pc.get("hard") or [])
    soft = list(pc.get("soft") or [])
    hard.sort(key=lambda p: (p[1], p[0]))
    soft.sort(key=lambda p: (p[1], p[0]))
    hard = hard[:_CORRIDOR_COORD_CAP]
    soft = soft[:_CORRIDOR_COORD_CAP]

    qset = sorted({str(x) for x in quarantined_placements if isinstance(x, str) and x})
    rset = sorted({str(x) for x in rolled_back_placements if isinstance(x, str) and x})

    return {
        "overlay_version": STEP4_REPLAY_OVERLAY_VERSION,
        "failed_stub_cells": stubs[:_AGG_COORD_SAMPLE_CAP],
        "failed_placement_ids": pids_out,
        "blocked_frontier_sample": frontier_acc[:_AGG_FRONTIER_SAMPLE_CAP],
        "nearest_blocked_cell": nb_cells[:_AGG_NEAREST_BLOCKED_CAP],
        "nearest_blocked_zone": nb_zones[:_AGG_NEAREST_BLOCKED_CAP],
        "route_goal_cells_sample": goals_acc[:_AGG_COORD_SAMPLE_CAP],
        "reachable_goal_cells_sample": reach_acc[:_AGG_COORD_SAMPLE_CAP],
        "existing_trunk_cells_sample": trunk_acc[:_AGG_COORD_SAMPLE_CAP],
        "trunk_seed_cells_sample": seed_acc[:_AGG_COORD_SAMPLE_CAP],
        "exterior_margin_cells_sample": margin_acc[:_AGG_COORD_SAMPLE_CAP],
        "hard_protected_corridors": hard,
        "soft_protected_corridors": soft,
        "quarantined_placements": qset,
        "rolled_back_placements": rset,
    }


__all__ = [
    "STEP4_REPLAY_OVERLAY_VERSION",
    "build_step4_row_replay_overlay",
    "merge_step4_route_failure_replay_overlay",
]
