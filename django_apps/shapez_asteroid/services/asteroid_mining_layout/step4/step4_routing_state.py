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
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    CORRIDOR_LIFECYCLE_HARD,
    CORRIDOR_LIFECYCLE_SOFT,
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


def _routing_state_from_committed_routes(
    routes: tuple[Step4Route, ...],
    *,
    cells: dict[Coord, dict[str, Any]] | None = None,
    is_external: Callable[[Coord], bool] | None = None,
    existing_layout_analysis: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    """Step4 committed route에서 P4 reclaim용 hard/soft protected corridor pool을 만든다.

    ``soft_protected_candidate_corridors``는 commit 스냅샷에서 후보가 없으므로 항상 ``[]``.

    ``hard``는 각 route의 ``stub_cell``과 ``path[-1]``(있을 때)만 포함한다. ELA
    ``trunk_seed_cell_union``은 ``hard``에 승격되지 않으며, ``existing_layout_analysis``가
    주어지면 ``ela_trunk_seed_candidate_corridors``에 별도 직렬화한다.
    """

    if not routes:
        return None

    hard: set[Coord] = set()
    soft_confirmed: set[Coord] = set()
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
        hard.add(route.stub_cell)
        if path:
            hard.add(path[-1])

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
    }
    if existing_layout_analysis is not None:
        ela_seeds = step4_goal_trunk_seed.trunk_seed_union_from_existing_layout(
            existing_layout_analysis
        )
        out["ela_trunk_seed_candidate_corridors"] = _coord_lists(frozenset(ela_seeds))
    return out
