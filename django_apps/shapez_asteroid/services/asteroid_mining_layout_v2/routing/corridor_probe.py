"""Interior ↔ exterior corridor availability (Pass2 / STEP4 pre-check; not final routing)."""

from __future__ import annotations

import heapq
import math
from collections import deque
from collections.abc import Callable

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BBox,
    BlueprintCell,
    is_physical_x,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.corridor import (
    CorridorProbeResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ReconstructionDTO,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    TransportKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.routing import (
    RoutePath,
)

from ..placement.bundle_candidate import (
    CARDINAL_DIRS,
    blocked_by_building,
    step_cell,
)
from ..placement.pass1_outer import (
    _cheap_escape_resolve_bbox_and_margin,
    _outside_margin,
)
from ..placement.pass2_route_probe import (
    _trunk_goal_cells,
)

MIN_PASS2_GATEWAYS = 2
MAX_EGRESS_SEARCH_NODES = 20000
_TOP_K_INTERNAL_ANCHORS = 8


def _bbox_fallback(cells: frozenset[BlueprintCell]) -> BBox | None:
    if not cells:
        return None
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    return BBox(min_x=min(xs), min_y=min(ys), max_x=max(xs), max_y=max(ys))


def _can_transit(
    c: BlueprintCell,
    *,
    transport_kind: TransportKind,
    reconstruction: ReconstructionDTO,
    pass1_fixed_cells: frozenset[BlueprintCell],
) -> bool:
    if c in pass1_fixed_cells:
        return False
    return not blocked_by_building(c, transport_kind, reconstruction)


def interior_anchor_cells_top_k(
    mineable: frozenset[BlueprintCell],
    pass1_fixed_cells: frozenset[BlueprintCell],
    bbox: BBox,
) -> tuple[BlueprintCell, ...]:
    """Deterministic top-K interior mineable cells (Pass1-occupied mineable excluded)."""

    candidates = mineable - pass1_fixed_cells
    if not candidates:
        return ()

    cx = (bbox.min_x + bbox.max_x) / 2.0
    cy = (bbox.min_y + bbox.max_y) / 2.0

    def edge_distance(c: BlueprintCell) -> int:
        x, y = c
        return int(min(x - bbox.min_x, bbox.max_x - x, y - bbox.min_y, bbox.max_y - y))

    def sort_key(c: BlueprintCell) -> tuple[int, float, int, int]:
        x, y = c
        dx, dy = x - cx, y - cy
        ang = math.atan2(dx, -dy)
        if ang < 0.0:
            ang += 2.0 * math.pi
        return (-edge_distance(c), ang, y, x)

    ordered = tuple(sorted(candidates, key=sort_key))
    return ordered[:_TOP_K_INTERNAL_ANCHORS]


def find_reachable_internal_cells(
    *,
    mineable_cells: frozenset[BlueprintCell],
    pass1_fixed_cells: frozenset[BlueprintCell],
    transport_kind: TransportKind,
    reconstruction: ReconstructionDTO,
    ctx: SolverRunContext,
) -> frozenset[BlueprintCell]:
    """Multi-source BFS from interior anchors over traversable cells (excluding ``pass1_fixed``)."""

    resolved = _cheap_escape_resolve_bbox_and_margin(reconstruction)
    if resolved is None:
        return frozenset()
    bbox, margin = resolved
    bbox_eff = reconstruction.asteroid_bbox or _bbox_fallback(mineable_cells)
    if bbox_eff is None:
        return frozenset()

    anchors = interior_anchor_cells_top_k(mineable_cells, pass1_fixed_cells, bbox_eff)
    if not anchors:
        pool = tuple(sorted(mineable_cells - pass1_fixed_cells))
        anchors = pool[:_TOP_K_INTERNAL_ANCHORS]
    if not anchors:
        return frozenset()

    xmin = bbox.min_x - margin - 6
    xmax = bbox.max_x + margin + 6
    ymin = bbox.min_y - margin - 6
    ymax = bbox.max_y + margin + 6

    seen: set[BlueprintCell] = set()
    q: deque[BlueprintCell] = deque()
    for a in anchors:
        if a in seen:
            continue
        if not _can_transit(
            a,
            transport_kind=transport_kind,
            reconstruction=reconstruction,
            pass1_fixed_cells=pass1_fixed_cells,
        ):
            continue
        seen.add(a)
        q.append(a)

    while q:
        cur = q.popleft()
        for d in CARDINAL_DIRS:
            nxt = step_cell(cur, d)
            if nxt in seen:
                continue
            if nxt[0] < xmin or nxt[0] > xmax or nxt[1] < ymin or nxt[1] > ymax:
                continue
            if not _can_transit(
                nxt,
                transport_kind=transport_kind,
                reconstruction=reconstruction,
                pass1_fixed_cells=pass1_fixed_cells,
            ):
                continue
            seen.add(nxt)
            q.append(nxt)

    return frozenset(c for c in seen if c in mineable_cells)


def count_gateway_cells(
    *,
    mineable_cells: frozenset[BlueprintCell],
    pass1_fixed_cells: frozenset[BlueprintCell],
    transport_kind: TransportKind,
    reconstruction: ReconstructionDTO,
    ctx: SolverRunContext,
) -> int:
    """Count distinct exterior-margin / trunk goal cells reachable from interior anchors."""

    probe = probe_pass2_corridor_availability(
        mineable_cells=mineable_cells,
        pass1_fixed_cells=pass1_fixed_cells,
        hard_barrier_cells=frozenset(reconstruction.full_barrier_cells),
        transport_kind=transport_kind,
        reconstruction=reconstruction,
        ctx=ctx,
    )
    return probe.gateway_count


def probe_pass2_corridor_availability(
    *,
    mineable_cells: frozenset[BlueprintCell],
    pass1_fixed_cells: frozenset[BlueprintCell],
    hard_barrier_cells: frozenset[BlueprintCell],
    transport_kind: TransportKind,
    reconstruction: ReconstructionDTO,
    ctx: SolverRunContext,
) -> CorridorProbeResult:
    """BFS from interior anchors to outside margin or same-kind trunk goals (§8-style probe)."""

    del hard_barrier_cells

    resolved = _cheap_escape_resolve_bbox_and_margin(reconstruction)
    if resolved is None:
        return CorridorProbeResult(
            connected=False,
            gateway_count=0,
            reachable_internal_count=0,
            blocked_frontier_cells=frozenset(),
            cheapest_path=None,
            reason="no_bbox_margin",
        )
    bbox, margin = resolved

    bbox_eff = reconstruction.asteroid_bbox or _bbox_fallback(mineable_cells)
    if bbox_eff is None:
        return CorridorProbeResult(
            connected=False,
            gateway_count=0,
            reachable_internal_count=0,
            blocked_frontier_cells=frozenset(),
            cheapest_path=None,
            reason="no_bbox",
        )

    anchors = interior_anchor_cells_top_k(mineable_cells, pass1_fixed_cells, bbox_eff)
    if not anchors:
        pool = tuple(sorted(mineable_cells - pass1_fixed_cells))
        anchors = pool[:_TOP_K_INTERNAL_ANCHORS]

    trunk_goals = _trunk_goal_cells(ctx, transport_kind, reconstruction)

    xmin = bbox.min_x - margin - 6
    xmax = bbox.max_x + margin + 6
    ymin = bbox.min_y - margin - 6
    ymax = bbox.max_y + margin + 6

    parent: dict[BlueprintCell, BlueprintCell | None] = {}
    goals: set[BlueprintCell] = set()
    q: deque[BlueprintCell] = deque()
    for a in anchors:
        if a in parent:
            continue
        if not _can_transit(
            a,
            transport_kind=transport_kind,
            reconstruction=reconstruction,
            pass1_fixed_cells=pass1_fixed_cells,
        ):
            continue
        parent[a] = None
        q.append(a)
        if _outside_margin(a, bbox, margin) or a in trunk_goals:
            goals.add(a)

    expansions = 0
    while q and expansions < MAX_EGRESS_SEARCH_NODES:
        front = q.popleft()
        expansions += 1
        for d in CARDINAL_DIRS:
            nxt = step_cell(front, d)
            if nxt in parent:
                continue
            if nxt[0] < xmin or nxt[0] > xmax or nxt[1] < ymin or nxt[1] > ymax:
                continue
            if not _can_transit(
                nxt,
                transport_kind=transport_kind,
                reconstruction=reconstruction,
                pass1_fixed_cells=pass1_fixed_cells,
            ):
                continue
            parent[nxt] = front
            q.append(nxt)
            if _outside_margin(nxt, bbox, margin) or nxt in trunk_goals:
                goals.add(nxt)

    reachable_internal = frozenset(c for c in parent if c in mineable_cells)
    gateway_count = len(goals)
    connected = gateway_count > 0

    cheapest: RoutePath | None = None
    if connected:
        best_goal = min(goals, key=lambda g: (g[1], g[0]))
        chain: list[BlueprintCell] = []
        walk: BlueprintCell | None = best_goal
        while walk is not None:
            chain.append(walk)
            walk = parent[walk]
        chain.reverse()
        cheapest = RoutePath(transport_kind=transport_kind, cells=tuple(chain))

    frontier: set[BlueprintCell] = set()
    for c in pass1_fixed_cells:
        for d in CARDINAL_DIRS:
            n = step_cell(c, d)
            if n in reachable_internal:
                frontier.add(c)
                break

    reason = None if connected else "no_exterior_or_trunk_goal_reachable"
    return CorridorProbeResult(
        connected=connected,
        gateway_count=gateway_count,
        reachable_internal_count=len(reachable_internal),
        blocked_frontier_cells=frozenset(frontier),
        cheapest_path=cheapest,
        reason=reason,
    )


def lexicographic_dijkstra_min_path(
    *,
    start: BlueprintCell,
    goal_predicate: Callable[[BlueprintCell], bool],
    transport_kind: TransportKind,
    reconstruction: ReconstructionDTO,
    bbox: BBox,
    margin: int,
    cell_step_cost: dict[BlueprintCell, tuple[int, ...]],
    default_step: tuple[int, ...],
) -> tuple[BlueprintCell, ...] | None:
    """Dijkstra on grid with per-cell additive lex tuple costs; deterministic tie by cell."""

    _ = transport_kind, reconstruction

    def add_t(a: tuple[int, ...], b: tuple[int, ...]) -> tuple[int, ...]:
        return tuple(x + y for x, y in zip(a, b, strict=True))

    xmin = bbox.min_x - margin - 6
    xmax = bbox.max_x + margin + 6
    ymin = bbox.min_y - margin - 6
    ymax = bbox.max_y + margin + 6

    zero = (0,) * len(default_step)
    is_goal = goal_predicate
    best: dict[BlueprintCell, tuple[int, ...]] = {start: zero}
    parent: dict[BlueprintCell, BlueprintCell | None] = {start: None}
    heap: list[tuple[tuple[int, ...], BlueprintCell]] = [(zero, start)]
    pops = 0

    while heap and pops < MAX_EGRESS_SEARCH_NODES:
        cost, cur = heapq.heappop(heap)
        pops += 1
        recorded = best.get(cur)
        if recorded is None or cost != recorded:
            continue
        if is_goal(cur):
            chain: list[BlueprintCell] = []
            walk: BlueprintCell | None = cur
            # Parent map must be a tree to ``start``; detect cycles / missing keys.
            seen_back: set[BlueprintCell] = set()
            max_chain = (xmax - xmin + 1) * (ymax - ymin + 1) + 2
            while walk is not None:
                if walk in seen_back or len(chain) > max_chain:
                    return None
                seen_back.add(walk)
                chain.append(walk)
                walk = parent.get(walk)
            chain.reverse()
            return tuple(chain)
        for d in CARDINAL_DIRS:
            nxt = step_cell(cur, d)
            if nxt[0] < xmin or nxt[0] > xmax or nxt[1] < ymin or nxt[1] > ymax:
                continue
            if not is_physical_x(nxt[0]):
                continue
            step = cell_step_cost.get(nxt, default_step)
            if any(x >= 999_999 for x in step):
                continue
            n_cost = add_t(cost, step)
            old = best.get(nxt)
            if old is None or n_cost < old:
                best[nxt] = n_cost
                parent[nxt] = cur
                heapq.heappush(heap, (n_cost, nxt))

    return None


__all__ = [
    "MAX_EGRESS_SEARCH_NODES",
    "MIN_PASS2_GATEWAYS",
    "find_reachable_internal_cells",
    "count_gateway_cells",
    "interior_anchor_cells_top_k",
    "lexicographic_dijkstra_min_path",
    "probe_pass2_corridor_availability",
]
