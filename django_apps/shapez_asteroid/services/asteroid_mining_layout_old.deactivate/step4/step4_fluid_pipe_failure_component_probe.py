"""Read-only STEP4 ``fluid_pipe`` failure component probe (debug / NDJSON only).

Uses the same step legality as ``step4_dijkstra`` / ``_bfs_reachable_from_stub``:
``neighbors4``, ``blocked`` (stub exempt), and ``step4_step_cost`` on the step target.
Not imported from routing search code paths.
"""

from __future__ import annotations

from collections import Counter, deque
from collections.abc import Callable, Mapping
from typing import Any

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_routing_permission as _s4rp,
)

_MAX_BFS_VISITS = 50_000
_FRONTIER_SAMPLE_MAX = 12


def _neighbor_reason(
    n: Coord,
    *,
    stub_cell: Coord,
    want_role: str,
    blocked: frozenset[Coord],
    hard_extras: frozenset[Coord],
    cells: dict[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    cheap_reuse_cells: frozenset[Coord] | None,
) -> str:
    """Aligned with ``step4_route_failure_detail._neighbor_block_reason``."""

    if n in hard_extras:
        return "hard_protected"
    if n in blocked and n != stub_cell:
        return "blocked"
    if (
        _s4rp.step4_step_cost(
            n,
            want_role=want_role,
            cells=cells,
            mineable=mineable,
            asteroid=asteroid,
            is_external=is_external,
            cheap_reuse_cells=cheap_reuse_cells,
        )
        is None
    ):
        return "step_cost_none"
    return "ok"


def _manhattan(a: Coord, b: Coord) -> int:
    return abs(int(a[0]) - int(b[0])) + abs(int(a[1]) - int(b[1]))


def _goal_source_bucket(
    g: Coord,
    *,
    trunk_cells: frozenset[Coord],
    margin_cells: set[Coord],
    trunk_seed: frozenset[Coord],
) -> str:
    """Disjoint buckets: trunk > margin > seed."""

    if g in trunk_cells:
        return "existing_trunk"
    if g in margin_cells:
        return "exterior_margin"
    if g in trunk_seed:
        return "trunk_seed"
    return "unclassified"


def build_step4_fluid_pipe_failure_component_probe(
    *,
    stub_cell: Coord,
    want_role: str,
    goal_cells: frozenset[Coord],
    trunk_cells: frozenset[Coord],
    trunk_seed_candidates_by_kind: Mapping[str, set[Coord]],
    margin_cells: set[Coord],
    blocked: frozenset[Coord],
    hard_extras: frozenset[Coord],
    cells: dict[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    cheap_reuse_cells: frozenset[Coord] | None,
    transport_kind: str,
) -> dict[str, Any] | None:
    """Return probe dict for ``fluid_pipe`` only; ``None`` for other kinds."""

    if transport_kind != "fluid_pipe":
        return None

    seed_pool = trunk_seed_candidates_by_kind.get(transport_kind) or set()
    trunk_seed = frozenset(seed_pool)

    visited: set[Coord] = {stub_cell}
    q: deque[Coord] = deque([stub_cell])
    visits = 0
    while q:
        c = q.popleft()
        visits += 1
        if visits > _MAX_BFS_VISITS:
            break
        x, y = c
        for v in neighbors4(x, y):
            if v in blocked and v != stub_cell:
                continue
            if (
                _s4rp.step4_step_cost(
                    v,
                    want_role=want_role,
                    cells=cells,
                    mineable=mineable,
                    asteroid=asteroid,
                    is_external=is_external,
                    cheap_reuse_cells=cheap_reuse_cells,
                )
                is None
            ):
                continue
            if v not in visited:
                visited.add(v)
                q.append(v)

    stub_reachable_cell_count = len(visited)

    unreachable = [g for g in goal_cells if g not in visited]
    nearest_unreachable_goal_cell: list[int] | None = None
    nearest_unreachable_goal_manhattan: int | None = None
    if unreachable:
        unreachable.sort(
            key=lambda g: (_manhattan(stub_cell, g), int(g[1]), int(g[0])),
        )
        pick = unreachable[0]
        nearest_unreachable_goal_manhattan = _manhattan(stub_cell, pick)
        nearest_unreachable_goal_cell = [int(pick[0]), int(pick[1])]

    boundary_cells: set[Coord] = set()
    for u in visited:
        ux, uy = u
        for v in neighbors4(ux, uy):
            if v not in visited:
                boundary_cells.add(v)

    reason_ctr: Counter[str] = Counter()
    for v in boundary_cells:
        reason_ctr[
            _neighbor_reason(
                v,
                stub_cell=stub_cell,
                want_role=want_role,
                blocked=blocked,
                hard_extras=hard_extras,
                cells=cells,
                mineable=mineable,
                asteroid=asteroid,
                is_external=is_external,
                cheap_reuse_cells=cheap_reuse_cells,
            )
        ] += 1

    frontier_reachable = sorted(
        (u for u in visited if any(n not in visited for n in neighbors4(u[0], u[1]))),
        key=lambda c: (int(c[1]), int(c[0])),
    )
    sample = frontier_reachable[:_FRONTIER_SAMPLE_MAX]
    reachable_frontier_boundary_sample = [[int(c[0]), int(c[1])] for c in sample]

    def _src_counts(goal_subset: frozenset[Coord]) -> dict[str, int]:
        out = {"existing_trunk": 0, "exterior_margin": 0, "trunk_seed": 0}
        for g in goal_subset:
            b = _goal_source_bucket(
                g,
                trunk_cells=trunk_cells,
                margin_cells=margin_cells,
                trunk_seed=trunk_seed,
            )
            if b in out:
                out[b] += 1
        return out

    goal_source_counts = _src_counts(goal_cells)
    reachable_goals = frozenset(g for g in goal_cells if g in visited)
    reachable_goal_source_counts = _src_counts(reachable_goals)

    return {
        "stub_reachable_cell_count": int(stub_reachable_cell_count),
        "nearest_unreachable_goal_cell": nearest_unreachable_goal_cell,
        "nearest_unreachable_goal_manhattan": nearest_unreachable_goal_manhattan,
        "reachable_frontier_boundary_sample": reachable_frontier_boundary_sample,
        "blocked_reason_counts_near_frontier": dict(sorted(reason_ctr.items())),
        "goal_source_counts": goal_source_counts,
        "reachable_goal_source_counts": reachable_goal_source_counts,
    }
