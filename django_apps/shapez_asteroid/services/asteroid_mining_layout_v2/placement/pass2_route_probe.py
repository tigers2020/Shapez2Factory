"""
Pass2 stub → exterior / trunk BFS probe (§8 admission + packing shadow only).

``path_cells`` policy (contract, fixed in tests): **exclude** ``output_stub_cell`` and
**exclude** ``goal_cell``; only **intermediate corridor** cells are shadow-reserved for
CP-SAT/greedy. These cells are **not** final routes, ``ROUTED_CONFIRMED``, or
``Pass2Result.blocked_cells_delta``.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BBox,
    BlueprintCell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ReconstructionDTO,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    TransportKind,
)

from .bundle_candidate import (
    CARDINAL_DIRS,
    Pass2BundleCandidate,
    blocked_by_building,
    step_cell,
)
from .pass1_outer import _cheap_escape_resolve_bbox_and_margin, _outside_margin


def _trunk_goal_cells(
    ctx: SolverRunContext,
    transport_kind: TransportKind,
    reconstruction: ReconstructionDTO,
) -> frozenset[BlueprintCell]:
    """Same-TransportKind trunk / seed cells usable as BFS goals (no routing module)."""

    rs = ctx.routing_state
    out: set[BlueprintCell] = set(rs.existing_trunk_cells_by_kind.get(transport_kind, frozenset()))
    for c in rs.trunk_seed_candidates:
        if not blocked_by_building(c, transport_kind, reconstruction):
            out.add(c)
    return frozenset(out)


def _candidate_hard_cells(candidate: Pass2BundleCandidate) -> frozenset[BlueprintCell]:
    cells = {candidate.extractor_cell}
    for ec, _pc, _orient in candidate.extension_cells:
        cells.add(ec)
    return frozenset(cells)


def _can_enter_cell(
    c: BlueprintCell,
    *,
    transport_kind: TransportKind,
    reconstruction: ReconstructionDTO,
    pass1_fixed_cells: frozenset[BlueprintCell],
    candidate_hard: frozenset[BlueprintCell],
) -> bool:
    if c in pass1_fixed_cells or c in candidate_hard:
        return False
    return not blocked_by_building(c, transport_kind, reconstruction)


@dataclass(frozen=True, slots=True)
class Pass2RouteProbe:
    candidate_id: str
    reachable: bool
    path_cells: tuple[BlueprintCell, ...]
    goal_cell: BlueprintCell | None
    reject_reason: str | None


def _reject_unreachable(cid: str) -> Pass2RouteProbe:
    return Pass2RouteProbe(
        candidate_id=cid,
        reachable=False,
        path_cells=(),
        goal_cell=None,
        reject_reason="pass2_stub_not_externally_reachable",
    )


def _bfs_find_goal_cell(
    stub: BlueprintCell,
    *,
    bbox: BBox,
    margin: int,
    trunk_goals: frozenset[BlueprintCell],
    transport_kind: TransportKind,
    reconstruction: ReconstructionDTO,
    pass1_fixed_cells: frozenset[BlueprintCell],
    candidate_hard: frozenset[BlueprintCell],
) -> tuple[BlueprintCell | None, dict[BlueprintCell, BlueprintCell | None]]:
    xmin = min(stub[0], bbox.min_x) - margin - 6
    xmax = max(stub[0], bbox.max_x) + margin + 6
    ymin = min(stub[1], bbox.min_y) - margin - 6
    ymax = max(stub[1], bbox.max_y) + margin + 6

    parent: dict[BlueprintCell, BlueprintCell | None] = {stub: None}
    q: deque[BlueprintCell] = deque([stub])
    goal_cell: BlueprintCell | None = None

    while q:
        cur = q.popleft()
        if _outside_margin(cur, bbox, margin) or cur in trunk_goals:
            goal_cell = cur
            break
        for d in CARDINAL_DIRS:
            nxt = step_cell(cur, d)
            oob = nxt[0] < xmin or nxt[0] > xmax or nxt[1] < ymin or nxt[1] > ymax
            if nxt in parent or oob:
                continue
            if not _can_enter_cell(
                nxt,
                transport_kind=transport_kind,
                reconstruction=reconstruction,
                pass1_fixed_cells=pass1_fixed_cells,
                candidate_hard=candidate_hard,
            ):
                continue
            parent[nxt] = cur
            q.append(nxt)

    return goal_cell, parent


def _intermediate_path_cells(
    goal_cell: BlueprintCell,
    parent: dict[BlueprintCell, BlueprintCell | None],
) -> tuple[BlueprintCell, ...]:
    chain: list[BlueprintCell] = []
    cur: BlueprintCell | None = goal_cell
    while cur is not None:
        chain.append(cur)
        cur = parent[cur]
    chain.reverse()
    return tuple(chain[i] for i in range(1, len(chain) - 1))


def probe_pass2_stub_route(
    candidate: Pass2BundleCandidate,
    *,
    pass1_fixed_cells: frozenset[BlueprintCell],
    reconstruction: ReconstructionDTO,
    ctx: SolverRunContext,
) -> Pass2RouteProbe:
    """BFS from ``output_stub_cell`` to exterior margin or same-kind trunk goals.

    ``pass1_fixed_cells`` = Pass1 equipment ∪ Pass1 output stubs (not all ``full_barrier``:
    belt/pipe traversability uses ``blocked_by_building``).
    """

    cid = candidate.candidate_id
    tk = candidate.transport_kind
    stub = candidate.output_stub_cell
    cand_hard = _candidate_hard_cells(candidate)

    resolved = _cheap_escape_resolve_bbox_and_margin(reconstruction)
    if resolved is None:
        return _reject_unreachable(cid)
    bbox, margin = resolved
    trunk_goals = _trunk_goal_cells(ctx, tk, reconstruction)

    goal_cell, parent = _bfs_find_goal_cell(
        stub,
        bbox=bbox,
        margin=margin,
        trunk_goals=trunk_goals,
        transport_kind=tk,
        reconstruction=reconstruction,
        pass1_fixed_cells=pass1_fixed_cells,
        candidate_hard=cand_hard,
    )

    if goal_cell is None:
        return _reject_unreachable(cid)

    intermediate = _intermediate_path_cells(goal_cell, parent)
    return Pass2RouteProbe(
        candidate_id=cid,
        reachable=True,
        path_cells=intermediate,
        goal_cell=goal_cell,
        reject_reason=None,
    )


__all__ = ["Pass2RouteProbe", "probe_pass2_stub_route"]
