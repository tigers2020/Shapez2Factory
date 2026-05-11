"""Pass2-A internal fill: mine remaining mineable after Pass1 (transport-only commit gate).

Visits **inner** mineable cells before perimeter cells (inverse of Pass1 outer-first).
Candidates exclude Pass1 extractor/extension bodies, committed transport (including output
stubs), and optional hard barriers. P1 cheap-escape void tiles are never on ``scratch`` and
are not treated as occupied.

Commits only through ``try_commit_pass2_bundle`` (no cheap escape; same route probe gate as
Pass1 minus void feasibility).
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.extraction.shapez_grid import step_cardinal
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.boundary import (
    cells_touching_void,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.extension_topology import (  # noqa: E501
    enumerate_extension_topologies,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_bundle_commit import (  # noqa: E501
    Pass12BundleCandidate,
    Pass12LayoutScratch,
    try_commit_pass2_bundle,
)

_OUTPUT_DIRS: tuple[tuple[int, int], ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))


def mineable_inner_first_order(
    mineable_cells: frozenset[Coord],
    asteroid_cells: frozenset[Coord],
    *,
    priority_seeds: frozenset[Coord] | None = None,
) -> tuple[Coord, ...]:
    """Inner mineable cells first; perimeter-adjacent last; stable by coordinate.

    ``priority_seeds``가 주어지면 inner/perimeter 그룹 안에서 시드에 맨해튼 1칸 인접한
    셀을 그룹 선두로 끌어온다. 그룹 자체(inner > perimeter)는 보전한다. ``None``이면
    기존 출력과 byte-equal (§8.5 Pass2 spine soft priority).
    """

    perimeter = frozenset(cells_touching_void(set(asteroid_cells))) & mineable_cells
    inner = mineable_cells - perimeter

    def _coord_key(c: Coord) -> tuple[int, int]:
        """Pass2 internal-first scan을 위한 중심거리 정렬키다 (§8 Pass2 placement)."""
        return (c[0], c[1])

    if priority_seeds is None or not priority_seeds:
        return tuple(sorted(inner, key=_coord_key)) + tuple(sorted(perimeter, key=_coord_key))

    def _is_priority(c: Coord) -> bool:
        cx, cy = c
        for dx, dy in _OUTPUT_DIRS:
            if (cx + dx, cy + dy) in priority_seeds:
                return True
        return False

    def _ordered(group: frozenset[Coord]) -> tuple[Coord, ...]:
        priority_part = sorted((c for c in group if _is_priority(c)), key=_coord_key)
        rest_part = sorted((c for c in group if not _is_priority(c)), key=_coord_key)
        return tuple(priority_part) + tuple(rest_part)

    return _ordered(inner) + _ordered(perimeter)


def try_place_pass2_internal_bundle(
    *,
    extractor_cell: Coord,
    mineable_cells: frozenset[Coord],
    scratch: Pass12LayoutScratch,
    is_external: Callable[[Coord], bool],
    hard_barrier_cells: frozenset[Coord],
    bundle_hint: dict[str, Any] | None = None,
    replay_events: list[dict[str, Any]] | None = None,
    extra_transport_block_cells: frozenset[Coord] = frozenset(),
    placement_transport_blocked_counter: list[int] | None = None,
) -> bool:
    """Try output directions; commit at most one bundle via ``try_commit_pass2_bundle``."""

    if extractor_cell in hard_barrier_cells:
        return False
    if extractor_cell in scratch.blocked_cells or extractor_cell in scratch.transport_cells:
        return False
    x, y = extractor_cell
    blocked_for_topo = frozenset(scratch.blocked_cells)
    transport_for_topo = frozenset(scratch.transport_cells)
    for dx, dy in _OUTPUT_DIRS:
        stub_cell = step_cardinal(x, y, dx, dy)
        if stub_cell is None:
            continue
        if stub_cell in scratch.transport_cells or stub_cell in extra_transport_block_cells:
            if placement_transport_blocked_counter is not None:
                placement_transport_blocked_counter[0] += 1
            continue
        if stub_cell in scratch.blocked_cells:
            continue
        if stub_cell in hard_barrier_cells:
            continue
        topologies = enumerate_extension_topologies(
            extractor_cell,
            (dx, dy),
            mineable_cells,
            blocked_for_topo,
            transport_for_topo,
            max_extensions=3,
        )
        for topo in topologies:
            ext_cells = topo.extension_cells
            blocked_c = frozenset({extractor_cell}) | ext_cells
            new_tr = frozenset({stub_cell})
            candidate = Pass12BundleCandidate(
                blocked_cells=blocked_c,
                new_transport=new_tr,
                stub_cell=stub_cell,
                extractor_cell=extractor_cell,
                extension_facings=topo.facings,
                extractor_output_dir=(dx, dy),
                p1_cheap_void_cells=None,
                placement_pass="pass2",
            )
            if try_commit_pass2_bundle(
                scratch,
                candidate,
                is_external=is_external,
                bundle_hint=bundle_hint,
                replay_events=replay_events,
            ):
                return True
    return False


def run_pass2_internal_placement_mvp(
    *,
    mineable_cells: frozenset[Coord],
    asteroid_cells: frozenset[Coord],
    scratch: Pass12LayoutScratch,
    is_external: Callable[[Coord], bool],
    hard_barrier_cells: frozenset[Coord] | None = None,
    replay_events: list[dict[str, Any]] | None = None,
    priority_seeds: frozenset[Coord] | None = None,
    extra_transport_block_cells: frozenset[Coord] = frozenset(),
    placement_transport_blocked_counter: list[int] | None = None,
) -> int:
    """Inner-first Pass2 sweep; returns how many extractors were committed.

    ``priority_seeds``가 주어지면 정렬에서 시드 인접 셀을 그룹 선두로 올린다 (§8.5
    Pass2 spine soft priority). 후보 풀·commit 게이트는 변경 없음.
    """

    barriers = hard_barrier_cells if hard_barrier_cells is not None else frozenset()
    placed = 0
    for cell in mineable_inner_first_order(
        mineable_cells, asteroid_cells, priority_seeds=priority_seeds
    ):
        if cell not in mineable_cells:
            continue
        if cell in barriers:
            continue
        if cell in scratch.blocked_cells or cell in scratch.transport_cells:
            continue
        hint: dict[str, Any] = {"pass": "p2_internal_mvp", "extractor_cell": cell}
        if try_place_pass2_internal_bundle(
            extractor_cell=cell,
            mineable_cells=mineable_cells,
            scratch=scratch,
            is_external=is_external,
            hard_barrier_cells=barriers,
            bundle_hint=hint,
            replay_events=replay_events,
            extra_transport_block_cells=extra_transport_block_cells,
            placement_transport_blocked_counter=placement_transport_blocked_counter,
        ):
            placed += 1
    return placed
