"""STEP4 committed route 기반 protected corridor state 조립.

§14.2 스냅샷: 이 모듈의 ``_routing_state_from_committed_routes``는 **이미 commit된**
route만 받는다. 미검증 probe/shadow 후보는 여기서 생기지 않으므로
``soft_protected_candidate_corridors``는 빈 리스트로 둔다.
``soft_protected_confirmed_corridors``·``soft_protected_corridors``는 동일한
commit 확정 soft 풀(``soft_cells``)을 반영한다.
"""

from __future__ import annotations

from collections import deque
from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.extraction.shapez_grid import neighbors4
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    blocked_cells as _blocked_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    want_role as _want_role,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_contracts import (
    Step4Route,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    transport_cells_reaching_external,
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
    trunk_cells = transport_cells_reaching_external(transport_now, blocked, is_external)
    if stub not in trunk_cells:
        return frozenset()
    comp = _bfs_transport_component(stub, transport_now, blocked)
    return frozenset(comp & trunk_cells)


def _routing_state_from_committed_routes(
    routes: tuple[Step4Route, ...],
    *,
    cells: dict[Coord, dict[str, Any]] | None = None,
    is_external: Callable[[Coord], bool] | None = None,
) -> dict[str, Any] | None:
    """Step4 committed route에서 P4 reclaim용 hard/soft protected corridor pool을 만든다.

    ``soft_protected_candidate_corridors``는 commit 스냅샷에서 후보가 없으므로 항상 ``[]``.
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
    return {
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
    }
