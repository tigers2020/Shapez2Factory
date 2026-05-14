"""Pass2-only bounded STEP4-legality reachability (no Dijkstra, no telemetry imports).

BFS expansion is restricted to a **finite universe** (``cells`` keys ∪ ``mineable`` ∪
``asteroid`` ∪ probe transport ∪ margin ∪ goals) so open-default ``step4_step_cost`` tiles
outside the Pass12 probe snapshot cannot absorb the visit budget. Pass2 safety precheck only;
STEP4 Dijkstra is unchanged.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_failure_category as _s4fc,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_routing_permission as _s4_perm,
)

__all__ = [
    "PASS2_STEP4_REACHABILITY_MAX_VISITS",
    "Pass2StubBoundedStep4Reachability",
    "pass2_stub_bounded_step4_reachability_precheck",
]

# Align with ``step4_route_failure_detail._MAX_REACHABLE_GOAL_BFS_VISITS`` scale; Pass2-only cap.
PASS2_STEP4_REACHABILITY_MAX_VISITS = 50_000


def _probe_transport_materialization_row(
    coord: Coord,
    *,
    transport_kind: str,
) -> dict[str, Any]:
    x, y = coord
    if transport_kind == "fluid_pipe":
        return {
            "x": int(x),
            "y": int(y),
            "role": "pipe",
            "layout_kind": "fluid_pipe_segment",
            "surface": "fluid",
        }
    if transport_kind == "shape_belt":
        return {
            "x": int(x),
            "y": int(y),
            "role": "belt",
            "layout_kind": "shape_belt_segment",
            "surface": "shape",
        }
    raise ValueError(f"unsupported transport_kind={transport_kind!r}")


def _build_probe_cells(
    cells_base: dict[Coord, dict[str, Any]],
    transport_probe: frozenset[Coord],
    transport_kind: str,
) -> dict[Coord, dict[str, Any]]:
    cells: dict[Coord, dict[str, Any]] = {k: dict(v) for k, v in cells_base.items()}
    for c in transport_probe:
        if c not in cells:
            cells[c] = _probe_transport_materialization_row(c, transport_kind=transport_kind)
    return cells


def _neighbor_block_reason(
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
    """Same contract as ``step4_route_failure_detail._neighbor_block_reason`` (STEP4 legality)."""

    if n in hard_extras:
        return "hard_protected"
    if n in blocked and n != stub_cell:
        return "blocked"
    if (
        _s4_perm.step4_step_cost(
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


def _stub_neighbor_diag(
    stub_cell: Coord,
    *,
    want_role: str,
    blocked: frozenset[Coord],
    hard_extras: frozenset[Coord],
    cells: dict[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    cheap_reuse_cells: frozenset[Coord] | None,
) -> list[dict[str, Any]]:
    sx, sy = stub_cell
    near: list[dict[str, Any]] = []
    for n in neighbors4(sx, sy):
        near.append(
            {
                "cell": [int(n[0]), int(n[1])],
                "reason": _neighbor_block_reason(
                    n,
                    stub_cell=stub_cell,
                    want_role=want_role,
                    blocked=blocked,
                    hard_extras=hard_extras,
                    cells=cells,
                    mineable=mineable,
                    asteroid=asteroid,
                    is_external=is_external,
                    cheap_reuse_cells=cheap_reuse_cells,
                ),
            }
        )
    return near


@dataclass(frozen=True)
class Pass2StubBoundedStep4Reachability:
    """Bounded STEP4-legality BFS from ``stub_cell`` (Pass2 probe snapshot)."""

    reachable: bool
    reachable_goal_count: int
    reachable_existing_trunk_count: int
    reachable_exterior_margin_count: int
    stop_reason: str
    visits: int
    blocked_reason_near_stub: list[dict[str, Any]]
    stub_isolated_geometry: bool


def pass2_stub_bounded_step4_reachability_precheck(
    *,
    stub_cell: Coord,
    want_role: str,
    transport_kind: str,
    cells_base: dict[Coord, dict[str, Any]],
    transport_probe: frozenset[Coord],
    blocked_probe: frozenset[Coord],
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    is_external: Callable[[Coord], bool],
    goal_cells: frozenset[Coord],
    trunk_cells: frozenset[Coord],
    margin_cells: set[Coord],
    cheap_reuse_cells: frozenset[Coord] | None = None,
    max_visits: int = PASS2_STEP4_REACHABILITY_MAX_VISITS,
) -> Pass2StubBoundedStep4Reachability:
    """STEP4 ``step4_step_cost``-legal BFS cap; no Dijkstra, not a routing input."""

    cells = _build_probe_cells(cells_base, transport_probe, transport_kind=transport_kind)
    hard_extras: frozenset[Coord] = frozenset()
    cheap = cheap_reuse_cells
    near = _stub_neighbor_diag(
        stub_cell,
        want_role=want_role,
        blocked=blocked_probe,
        hard_extras=hard_extras,
        cells=cells,
        mineable=mineable,
        asteroid=asteroid,
        is_external=is_external,
        cheap_reuse_cells=cheap,
    )
    stub_iso = _s4fc.stub_isolated_neighbor_geometry(near)
    if stub_iso:
        return Pass2StubBoundedStep4Reachability(
            reachable=False,
            reachable_goal_count=0,
            reachable_existing_trunk_count=0,
            reachable_exterior_margin_count=0,
            stop_reason="stub_isolated",
            visits=0,
            blocked_reason_near_stub=near,
            stub_isolated_geometry=True,
        )

    margin_f = frozenset(margin_cells)
    goals = frozenset(goal_cells)
    if not goals:
        return Pass2StubBoundedStep4Reachability(
            reachable=False,
            reachable_goal_count=0,
            reachable_existing_trunk_count=0,
            reachable_exterior_margin_count=0,
            stop_reason="no_goals",
            visits=0,
            blocked_reason_near_stub=near,
            stub_isolated_geometry=False,
        )

    universe = frozenset(
        set(cells.keys())
        | set(mineable)
        | set(asteroid)
        | set(transport_probe)
        | set(margin_f)
        | set(goals)
    )

    visited: set[Coord] = {stub_cell}
    q: deque[Coord] = deque([stub_cell])
    visits = 0
    stop_reason = "exhausted"
    while q:
        c = q.popleft()
        visits += 1
        if visits >= max_visits:
            stop_reason = "budget"
            break
        if c in goals:
            stop_reason = "success"
            break
        x, y = c
        for v in neighbors4(x, y):
            if v not in universe:
                continue
            if v in blocked_probe and v != stub_cell:
                continue
            if (
                _s4_perm.step4_step_cost(
                    v,
                    want_role=want_role,
                    cells=cells,
                    mineable=mineable,
                    asteroid=asteroid,
                    is_external=is_external,
                    cheap_reuse_cells=cheap,
                )
                is None
            ):
                continue
            if v not in visited:
                visited.add(v)
                q.append(v)

    reachable_goals = frozenset(visited & goals)
    rgc = len(reachable_goals)
    r_trunk = len(reachable_goals & trunk_cells)
    r_margin = len(reachable_goals & margin_f)
    reachable = rgc > 0
    return Pass2StubBoundedStep4Reachability(
        reachable=reachable,
        reachable_goal_count=rgc,
        reachable_existing_trunk_count=r_trunk,
        reachable_exterior_margin_count=r_margin,
        stop_reason=stop_reason,
        visits=visits,
        blocked_reason_near_stub=near,
        stub_isolated_geometry=False,
    )
