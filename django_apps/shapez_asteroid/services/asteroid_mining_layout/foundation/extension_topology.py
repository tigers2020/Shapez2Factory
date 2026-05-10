"""Canonical P1-B: deterministic extension topologies for Pass1 (pure generator).

Enumerates up to ``max_extensions`` tiles on the three cardinal sides of an extractor
that are not the output/stub side, plus extension-to-extension chains. Each extension
faces its parent (cardinal vector from extension cell toward parent).

Placement commit still runs through ``try_commit_pass1_bundle``; route probe there is a
**placement safety gate**, not STEP4 final merge-aware routing.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from functools import partial

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import (
    rotation_r_for_output_direction,
)
from django_apps.shapez_asteroid.extraction.shapez_grid import step_cardinal
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord

# Deterministic cardinal order (matches Pass1 output scan).
_CARD_ORDER: tuple[tuple[int, int], ...] = ((1, 0), (-1, 0), (0, 1), (0, -1))


@dataclass(frozen=True)
class ExtensionTopologyCandidate:
    """Extension cells and parent-facing cardinals (toward parent)."""

    facings: frozenset[tuple[Coord, int, int]]

    @property
    def extension_count(self) -> int:
        """P1-B extension chain에 포함된 extension 수를 돌려준다 (§3.1 extractor/extension)."""
        return len(self.facings)

    @property
    def extension_cells(self) -> frozenset[Coord]:
        """P1-B extension chain의 셀 집합을 돌려준다 (§3.1 extractor/extension)."""
        return frozenset(c for c, _, _ in self.facings)


def rotation_r_for_extension_facing_parent(toward_parent: tuple[int, int]) -> int:
    """Map parent-facing cardinal to blueprint ``r`` (same convention as shape miner output)."""

    return rotation_r_for_output_direction(toward_parent[0], toward_parent[1])


def _facings_from_placed(placed: list[tuple[Coord, Coord]]) -> frozenset[tuple[Coord, int, int]]:
    """placed parent chain을 parent-facing extension signature로 변환한다.

        P1-B extension chain 정렬 전 표준 형태다 (§3.1-3.3).

    상세: documents/Algorithm/mining_solver_cursor_sessions/01_project_overview.md"""
    out: list[tuple[Coord, int, int]] = []
    for cell, parent in placed:
        out.append((cell, parent[0] - cell[0], parent[1] - cell[1]))
    return frozenset(out)


_SigKey = tuple[tuple[int, int, int, int], ...]


def _sort_key_topo(f: frozenset[tuple[Coord, int, int]]) -> tuple[int, _SigKey]:
    """P1-B extension chain 후보의 결정적 정렬키를 만든다.

        extension 수를 우선하고 좌표 signature로 tie-break한다 (§7 Pass1 placement).

    상세: documents/Algorithm/mining_solver_cursor_sessions/06_step2_pass1_placement.md"""
    n = len(f)
    sig = tuple(sorted((c[0], c[1], dx, dy) for c, dx, dy in f))
    return (-n, sig)


def _extension_cell_is_placeable(
    c: Coord,
    *,
    stub: Coord,
    extractor_cell: Coord,
    mineable_cells: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    transport_cells: frozenset[Coord],
) -> bool:
    """candidate extension 셀이 Pass1 배치 가능 영역인지 검사한다 (§7 Pass1 placement)."""
    if c == stub:
        return False
    if c == extractor_cell:
        return False
    if c not in mineable_cells:
        return False
    if c in blocked_cells:
        return False
    return c not in transport_cells


def _emit_unique_facings(
    facing_set: frozenset[tuple[Coord, int, int]],
    seen: set[frozenset[tuple[Coord, int, int]]],
    out: list[ExtensionTopologyCandidate],
) -> None:
    """중복 없는 ExtensionTopologyCandidate를 결과에 추가한다 (§7 Pass1 placement)."""
    if facing_set in seen:
        return
    seen.add(facing_set)
    out.append(ExtensionTopologyCandidate(facing_set))


def _iter_next_extension_placements(
    parents: list[Coord],
    occupied: set[Coord],
    placeable: Callable[[Coord], bool],
) -> Iterable[tuple[Coord, Coord]]:
    """부모 셀에서 한 칸 뻗는 유효한 (child, parent) 후보를 결정적 순서로 낸다."""
    for p in parents:
        px, py = p
        for dx, dy in _CARD_ORDER:
            ch = step_cardinal(px, py, dx, dy)
            if ch is None:
                continue
            if ch in occupied:
                continue
            if not placeable(ch):
                continue
            yield ch, p


def _dfs_extension_placements(
    placed: list[tuple[Coord, Coord]],
    *,
    extractor_cell: Coord,
    max_extensions: int,
    seen: set[frozenset[tuple[Coord, int, int]]],
    out: list[ExtensionTopologyCandidate],
    placeable: Callable[[Coord], bool],
) -> None:
    """extractor/extension parent chain을 DFS로 확장한다 (§7 Pass1 placement)."""
    _emit_unique_facings(_facings_from_placed(placed), seen, out)
    if len(placed) >= max_extensions:
        return
    occupied: set[Coord] = {extractor_cell} | {c for c, _ in placed}
    parents = [extractor_cell] + sorted(
        [c for c, _ in placed],
        key=lambda z: (z[0], z[1]),
    )
    for ch, par in _iter_next_extension_placements(parents, occupied, placeable):
        _dfs_extension_placements(
            placed + [(ch, par)],
            extractor_cell=extractor_cell,
            max_extensions=max_extensions,
            seen=seen,
            out=out,
            placeable=placeable,
        )


def enumerate_extension_topologies(
    extractor_cell: Coord,
    output_direction: tuple[int, int],
    mineable_cells: frozenset[Coord],
    blocked_cells: frozenset[Coord],
    transport_cells: frozenset[Coord],
    *,
    max_extensions: int = 3,
) -> tuple[ExtensionTopologyCandidate, ...]:
    """All distinct extension sets (0..max_extensions) with valid parent chains.

    The output neighbour (stub cell) never hosts an extension. Extensions must lie in
    ``mineable_cells`` and avoid ``blocked_cells`` / ``transport_cells`` / ``extractor_cell``.
    Results are sorted by: more extensions first, then stable coordinate signature.
    """

    ex, ey = extractor_cell
    stub = step_cardinal(ex, ey, output_direction[0], output_direction[1])
    if stub is None:
        return (ExtensionTopologyCandidate(frozenset()),)

    placeable: Callable[[Coord], bool] = partial(
        _extension_cell_is_placeable,
        stub=stub,
        extractor_cell=extractor_cell,
        mineable_cells=mineable_cells,
        blocked_cells=blocked_cells,
        transport_cells=transport_cells,
    )
    seen: set[frozenset[tuple[Coord, int, int]]] = set()
    out: list[ExtensionTopologyCandidate] = []
    _dfs_extension_placements(
        [],
        extractor_cell=extractor_cell,
        max_extensions=max_extensions,
        seen=seen,
        out=out,
        placeable=placeable,
    )
    out.sort(key=lambda cand: _sort_key_topo(cand.facings))
    return tuple(out)
