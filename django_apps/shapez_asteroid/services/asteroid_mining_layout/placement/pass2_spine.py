"""Pass-2 spine helpers: void corridor from extension-adjacent seeds toward external anchor."""

from __future__ import annotations

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4, step_cardinal
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    trace_event,
)

_EXTENSION_ROLES = frozenset({"extension", "fluid_extension"})


def _sig(delta: int) -> int:
    """좌표 부호를 spine 후보 방향 판정용으로 축약한다 (§8 Pass2 spine).

    상세: documents/Algorithm/mining_solver_cursor_sessions/07_step3_pass2_placement.md"""
    return (delta > 0) - (delta < 0)


def spine_seed_voids_adjacent_extensions(
    buildings: dict[Coord, str],
    asteroid_cells: set[Coord],
) -> set[Coord]:
    """Void cells cardinally adjacent to a pass-1 extension tile (spine entry candidates)."""

    seeds: set[Coord] = set()
    for cell, role in buildings.items():
        if role not in _EXTENSION_ROLES:
            continue
        x, y = cell
        for nxt in neighbors4(x, y):
            if nxt in asteroid_cells:
                continue
            if nxt in buildings:
                continue
            seeds.add(nxt)
    trace_event(
        f"{__name__}.spine_seed_voids_adjacent_extensions",
        "exit",
        {
            "n_seeds": len(seeds),
            "n_extension_tiles": sum(
                1 for _c, role in buildings.items() if role in _EXTENSION_ROLES
            ),
            "n_buildings": len(buildings),
            "n_asteroid_cells": len(asteroid_cells),
        },
    )
    return seeds


def monotone_straight_void_path_to_goal(
    start: Coord,
    goal: Coord,
    *,
    asteroid_cells: set[Coord],
    occupied_for_walk: set[Coord],
) -> list[Coord] | None:
    """Axis-aligned monotone steps toward ``goal``.

    Each stepped cell must not be rock interior (``asteroid_cells``) nor blocked occupied
    (building bodies and reserved tiles such as existing outlets). Pure transport-only
    cells are *not* included in ``occupied_for_walk`` so an existing spine may be reused.
    """

    if start == goal:
        trace_event(
            f"{__name__}.monotone_straight_void_path_to_goal",
            "ok_trivial",
            {"path_len": 0, "start": start, "goal": goal},
        )
        return []

    cur = start
    path: list[Coord] = []
    seen: set[Coord] = {start}
    for _ in range(4096):
        if cur == goal:
            trace_event(
                f"{__name__}.monotone_straight_void_path_to_goal",
                "ok",
                {"path_len": len(path), "start": start, "goal": goal},
            )
            return path
        dx = goal[0] - cur[0]
        dy = goal[1] - cur[1]
        if dx != 0 and (abs(dx) >= abs(dy) or dy == 0):
            step = (_sig(dx), 0)
        elif dy != 0:
            step = (0, _sig(dy))
        else:
            trace_event(
                f"{__name__}.monotone_straight_void_path_to_goal",
                "fail_no_step",
                {
                    "cur": cur,
                    "goal": goal,
                    "path_len": len(path),
                    "manhattan_remaining": abs(goal[0] - cur[0]) + abs(goal[1] - cur[1]),
                },
            )
            return None
        nxt = step_cardinal(cur[0], cur[1], step[0], step[1])
        if nxt is None or nxt in seen:
            trace_event(
                f"{__name__}.monotone_straight_void_path_to_goal",
                "fail_blocked_or_seen",
                {"cur": cur, "goal": goal, "nxt": nxt, "path_len": len(path)},
            )
            return None
        if nxt in asteroid_cells or nxt in occupied_for_walk:
            trace_event(
                f"{__name__}.monotone_straight_void_path_to_goal",
                "fail_rock_or_occupied",
                {"cur": cur, "goal": goal, "nxt": nxt, "path_len": len(path)},
            )
            return None
        path.append(nxt)
        seen.add(nxt)
        cur = nxt
    trace_event(
        f"{__name__}.monotone_straight_void_path_to_goal",
        "fail_step_limit",
        {"start": start, "goal": goal, "path_len": len(path)},
    )
    return None
