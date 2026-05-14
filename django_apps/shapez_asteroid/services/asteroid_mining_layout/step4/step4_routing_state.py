"""STEP4 committed route 기반 protected corridor state 조립.

§14.2 스냅샷: 이 모듈의 ``_routing_state_from_committed_routes``는 **이미 commit된**
route만 받는다. 미검증 probe/shadow 후보는 여기서 생기지 않으므로
``soft_protected_candidate_corridors``는 빈 리스트로 둔다.
``soft_protected_confirmed_corridors``·``soft_protected_corridors``는 동일한
commit 확정 soft 풀(``soft_cells``)을 반영한다.

§14 / PR4-C: ``existing_layout_analysis``가 주어지면 ELA ``main_trunk_candidate`` 출처인
``solver_hints.trunk_seed_cell_union``을 ``ela_trunk_seed_candidate_corridors``에만
직렬화한다(관측·candidate 분리). 이 키는 ``hard_protected_corridors``에 합쳐지지 않으며
``ROUTING_STATE_KEYS_STEP4_HASH``에 포함되지 않는다.

§14.2.2 (S4): ``hard_protected``는 **output stub**은 항상 증거가 있다. ``path[-1]``(trunk
terminal)은 ``replacement_search_exhausted`` 등가 증명(``trunk_terminal_hard_reason``) 또는
``is_external``로 확인되는 **외부 접점**일 때만 hard에 포함한다(무증거 승격 금지).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Mapping
from typing import Any

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    ALLOWED_HARD_PROMOTION_REASONS,
    CORRIDOR_LIFECYCLE_HARD,
    CORRIDOR_LIFECYCLE_SOFT,
    HARD_PROMOTION_REASON_EXTERNAL_ARTICULATION,
    HARD_PROMOTION_REASON_OUTPUT_STUB,
    HARD_PROMOTION_REASON_REPLACEMENT_SEARCH_EXHAUSTED,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    blocked_cells as _blocked_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    want_role as _want_role,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import step4_goal_trunk_seed
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_contracts import (
    Step4Route,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
    final_validation as _finval,
)


def _coord_lists(cells: frozenset[Coord]) -> list[list[int]]:
    return [[x, y] for x, y in sorted(cells, key=lambda p: (p[1], p[0]))]


def _same_kind_transport_cells(cells: dict[Coord, dict[str, Any]], want_role: str) -> set[Coord]:
    out: set[Coord] = set()
    for coord, row in cells.items():
        if row.get("role") == want_role:
            out.add(coord)
    return out


def _bfs_transport_component(
    start: Coord,
    transport_cells: set[Coord],
    blocked: set[Coord],
) -> set[Coord]:
    """``start``가 속한 같은 transport 4방향 연결 컴포넌트를 반환한다."""

    if start not in transport_cells or start in blocked:
        return set()
    queue: deque[Coord] = deque([start])
    seen: set[Coord] = {start}
    while queue:
        coord = queue.popleft()
        x, y = coord
        for nxt in neighbors4(x, y):
            if nxt in seen or nxt not in transport_cells or nxt in blocked:
                continue
            seen.add(nxt)
            queue.append(nxt)
    return seen


def _soft_cells_for_merged_stub_route(
    route: Step4Route,
    *,
    cells: dict[Coord, dict[str, Any]],
    is_external: Callable[[Coord], bool],
) -> frozenset[Coord]:
    """STEP4 stub-in-trunk shortcut이 사용한 trunk belt/pipe 셀을 soft pool로 보존한다."""

    if len(route.path) != 1 or not route.merged_to_existing:
        return frozenset()
    stub = route.stub_cell
    want_role = _want_role(route.transport_kind)
    transport_now = _same_kind_transport_cells(cells, want_role)
    blocked = set(_blocked_cells(cells))
    trunk_cells = _finval.transport_cells_reaching_external(transport_now, blocked, is_external)
    if stub not in trunk_cells:
        return frozenset()
    comp = _bfs_transport_component(stub, transport_now, blocked)
    return frozenset(comp & trunk_cells)


def _hard_cells_from_coord_list(val: object) -> frozenset[Coord]:
    if not isinstance(val, list):
        return frozenset()
    out: set[Coord] = set()
    for it in val:
        if isinstance(it, (list, tuple)) and len(it) == 2:
            x, y = it[0], it[1]
            if isinstance(x, int) and isinstance(y, int) and x != 0:
                out.add((x, y))
    return frozenset(out)


def compute_hard_promotion_audit(routing_state: Mapping[str, Any] | None) -> dict[str, Any]:
    """Count hard cells missing a valid §14.2.2 ``hard_protected_promotions`` record."""

    if not isinstance(routing_state, dict):
        return {"hard_promotion_without_proof_count": 0, "cells_missing_evidence": []}
    hard_set = _hard_cells_from_coord_list(routing_state.get("hard_protected_corridors"))
    promotions = routing_state.get("hard_protected_promotions")
    if not isinstance(promotions, list) or not promotions:
        return {
            "hard_promotion_without_proof_count": len(hard_set),
            "cells_missing_evidence": _coord_lists(hard_set),
        }
    explained: set[Coord] = set()
    for p in promotions:
        if not isinstance(p, dict):
            continue
        cell = p.get("cell")
        reason = str(p.get("reason") or "")
        if not isinstance(cell, (list, tuple)) or len(cell) != 2:
            continue
        try:
            c = (int(cell[0]), int(cell[1]))
        except (TypeError, ValueError):
            continue
        if reason not in ALLOWED_HARD_PROMOTION_REASONS:
            continue
        explained.add(c)
    missing = hard_set - frozenset(explained)
    return {
        "hard_promotion_without_proof_count": len(missing),
        "cells_missing_evidence": _coord_lists(missing),
    }


def _protected_corridor_hard_by_reason_from_promotions(
    promotions: list[dict[str, Any]],
) -> dict[str, list[list[int]]]:
    buckets: dict[str, set[Coord]] = {}
    for p in promotions:
        if not isinstance(p, dict):
            continue
        cell = p.get("cell")
        reason = str(p.get("reason") or "")
        if not isinstance(cell, (list, tuple)) or len(cell) != 2:
            continue
        try:
            c = (int(cell[0]), int(cell[1]))
        except (TypeError, ValueError):
            continue
        if reason not in ALLOWED_HARD_PROMOTION_REASONS:
            continue
        buckets.setdefault(reason, set()).add(c)
    return {k: _coord_lists(frozenset(v)) for k, v in sorted(buckets.items())}


def _routing_state_from_committed_routes(
    routes: tuple[Step4Route, ...],
    *,
    cells: dict[Coord, dict[str, Any]] | None = None,
    is_external: Callable[[Coord], bool] | None = None,
    existing_layout_analysis: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Step4 committed route에서 P4 reclaim용 hard/soft protected corridor pool을 만든다.

    ``soft_protected_candidate_corridors``는 commit 스냅샷에서 후보가 없으므로 항상 ``[]``.

    ``hard``는 기본적으로 각 route의 ``stub_cell``(output stub)만 포함한다. ``path[-1]``은
    ``trunk_terminal_hard_reason == replacement_search_exhausted_terminal``이거나
    ``reached_external``이고 ``is_external(path[-1])``가 참인 경우에만 hard에 추가한다.
    ELA ``trunk_seed_cell_union``은 ``hard``에 승격되지 않으며,
    ``ela_trunk_seed_candidate_corridors``에만 직렬화한다.
    """

    if not routes:
        return None

    hard: set[Coord] = set()
    soft_confirmed: set[Coord] = set()
    promotions: list[dict[str, Any]] = []
    for route in routes:
        path = tuple(route.path)
        extra_soft: set[Coord] = set()
        if cells is not None and is_external is not None:
            extra_soft.update(
                _soft_cells_for_merged_stub_route(route, cells=cells, is_external=is_external)
            )
        if not path and not extra_soft:
            continue
        soft_confirmed.update(path)
        soft_confirmed.update(extra_soft)
        stub = route.stub_cell
        hard.add(stub)
        rid = route.placement_id or ""
        src_rid = f"route-{rid}" if rid else "route-anon"
        promotions.append(
            {
                "cell": [stub[0], stub[1]],
                "reason": HARD_PROMOTION_REASON_OUTPUT_STUB,
                "placement_id": route.placement_id,
                "source_route_id": src_rid,
                "replacement_search_exhausted": False,
            }
        )
        if path:
            tail = path[-1]
            if tail != stub:
                term_reason: str | None = None
                exhausted_ok = (
                    route.trunk_terminal_hard_reason
                    == HARD_PROMOTION_REASON_REPLACEMENT_SEARCH_EXHAUSTED
                )
                if exhausted_ok:
                    term_reason = HARD_PROMOTION_REASON_REPLACEMENT_SEARCH_EXHAUSTED
                elif is_external is not None and route.reached_external and is_external(tail):
                    term_reason = HARD_PROMOTION_REASON_EXTERNAL_ARTICULATION
                if term_reason is not None:
                    hard.add(tail)
                    promotions.append(
                        {
                            "cell": [tail[0], tail[1]],
                            "reason": term_reason,
                            "placement_id": route.placement_id,
                            "source_route_id": src_rid,
                            "replacement_search_exhausted": term_reason
                            == HARD_PROMOTION_REASON_REPLACEMENT_SEARCH_EXHAUSTED,
                        }
                    )

    soft = soft_confirmed - hard
    hard_cells = frozenset(hard)
    soft_cells = frozenset(soft)
    out: dict[str, Any] = {
        "source": "step4_committed_routes",
        "step4_route_count": len(routes),
        "protected_corridors": {
            "hard": _coord_lists(hard_cells),
            "soft": _coord_lists(soft_cells),
        },
        "hard_protected_corridors": _coord_lists(hard_cells),
        "soft_protected_corridors": _coord_lists(soft_cells),
        "soft_protected_candidate_corridors": [],
        "soft_protected_confirmed_corridors": _coord_lists(soft_cells),
        "corridor_probe_candidates_at_commit": [],
        "corridor_lifecycle_soft_pool": CORRIDOR_LIFECYCLE_SOFT if soft_cells else None,
        "corridor_lifecycle_hard_pool": CORRIDOR_LIFECYCLE_HARD if hard_cells else None,
        "hard_protected_promotions": promotions,
        "protected_corridor_hard_by_reason": _protected_corridor_hard_by_reason_from_promotions(
            promotions
        ),
    }
    _audit = compute_hard_promotion_audit(out)
    out["hard_promotion_without_proof_count"] = int(
        _audit.get("hard_promotion_without_proof_count") or 0
    )
    if existing_layout_analysis is not None:
        ela_seeds = step4_goal_trunk_seed.trunk_seed_union_from_existing_layout(
            existing_layout_analysis
        )
        out["ela_trunk_seed_candidate_corridors"] = _coord_lists(frozenset(ela_seeds))
    return out


__all__ = [
    "_routing_state_from_committed_routes",
    "compute_hard_promotion_audit",
]
