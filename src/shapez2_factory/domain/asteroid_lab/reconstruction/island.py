"""Non-transport asteroid islands and uniform ``cell_kind`` stamping (post-reconstruction)."""

from __future__ import annotations

from collections import Counter, deque
from collections.abc import Iterable
from dataclasses import replace

from shapez2_factory.domain.asteroid_lab.reconstruction.evidence import (
    ASTEROID_FIELD_KINDS,
    evidence_field_kind,
    inferred_field_kind_from_removed_miner_extension,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.fill import ASTEROID_SHAPE_FIELD
from shapez2_factory.domain.asteroid_lab.reconstruction.grid import Coord
from shapez2_factory.domain.asteroid_lab.service_dtos import DecodedCellDTO
from shapez2_factory.domain.asteroid_lab.transport_components import (
    is_transport_tile,
    iter_four_neighbors,
    sort_key_xy_layer,
)

CellKey = tuple[int, int, int | None]


def build_original_evidence_by_xy(
    original_cells: Iterable[DecodedCellDTO],
    removed_building_cells: Iterable[DecodedCellDTO],
) -> dict[Coord, str]:
    """Decoded ``asteroid_*_field`` plus implied kinds at stripped miner/extension anchors."""

    m: dict[Coord, str] = {}
    for c in original_cells:
        k = evidence_field_kind(c)
        if k in ASTEROID_FIELD_KINDS:
            m[(c.x, c.y)] = k
    for c in removed_building_cells:
        hint = inferred_field_kind_from_removed_miner_extension(c)
        if hint is None:
            continue
        xy = (c.x, c.y)
        if xy not in m:
            m[xy] = hint
    return m


def _allow_edge(a: DecodedCellDTO, b: DecodedCellDTO, evidence: dict[Coord, str]) -> bool:
    """False when both endpoints carry conflicting original ``asteroid_*`` evidence."""

    ka = evidence.get((a.x, a.y))
    kb = evidence.get((b.x, b.y))
    if ka in ASTEROID_FIELD_KINDS and kb in ASTEROID_FIELD_KINDS and ka != kb:
        return False
    return True


def _vote_xy_set(
    island_keys: set[CellKey], key_to_cell: dict[CellKey, DecodedCellDTO]
) -> set[Coord]:
    """Island member coords plus 4-neighbors of ``topology_fill`` synthetic cells only.

    Neighbors of every decoded ring cell would pull in distant wall anchors (e.g. top-row
    stripped miners) and break strict per-hole / tie semantics; only holes need wall-only
    evidence at adjacent stripped coordinates.
    """

    coords: set[Coord] = set()
    for k in island_keys:
        c = key_to_cell[k]
        coords.add((c.x, c.y))
        raw = c.raw_entry_json
        if isinstance(raw, dict) and raw.get("_reconstruction") == "topology_fill":
            for nx, ny, _nl in iter_four_neighbors(c.x, c.y, c.layer):
                coords.add((nx, ny))
    return coords


def _is_topology_fill_cell(cell: DecodedCellDTO) -> bool:
    raw = cell.raw_entry_json
    return isinstance(raw, dict) and raw.get("_reconstruction") == "topology_fill"


def _is_stamp_target(cell: DecodedCellDTO) -> bool:
    return cell.cell_kind in ASTEROID_FIELD_KINDS or _is_topology_fill_cell(cell)


def _is_traversable_for_island(cell: DecodedCellDTO) -> bool:
    """Stamp targets plus ``unknown`` bridges (walls are not recolored)."""

    return _is_stamp_target(cell) or cell.cell_kind == "unknown"


def resolve_island_kind(
    island_keys: set[CellKey],
    key_to_cell: dict[CellKey, DecodedCellDTO],
    original_evidence_by_xy: dict[Coord, str],
) -> str:
    """Strict fluid vs shape majority on vote coords; tie or no evidence → shape field."""

    vote_xys = _vote_xy_set(island_keys, key_to_cell)
    counts = Counter(
        original_evidence_by_xy[xy] for xy in vote_xys if xy in original_evidence_by_xy
    )
    if counts["asteroid_fluid_field"] > counts["asteroid_shape_field"]:
        return "asteroid_fluid_field"
    return ASTEROID_SHAPE_FIELD


def stamp_islands_uniform(
    out_cells: tuple[DecodedCellDTO, ...],
    *,
    original_cells: Iterable[DecodedCellDTO],
    removed_building_cells: Iterable[DecodedCellDTO],
) -> tuple[DecodedCellDTO, ...]:
    """Uniform ``asteroid_*_field`` on stamp targets; ``unknown`` walls stay traversable only."""

    evidence = build_original_evidence_by_xy(original_cells, removed_building_cells)
    key_to_cell: dict[CellKey, DecodedCellDTO] = {(c.x, c.y, c.layer): c for c in out_cells}
    stamp_target_keys = {
        k for k, c in key_to_cell.items() if not is_transport_tile(c) and _is_stamp_target(c)
    }
    traversable_keys = {
        k
        for k, c in key_to_cell.items()
        if not is_transport_tile(c) and _is_traversable_for_island(c)
    }

    visited: set[CellKey] = set()
    stamp_by_key: dict[CellKey, str] = {}

    for start_key in sorted(traversable_keys):
        if start_key in visited:
            continue
        comp: set[CellKey] = set()
        q: deque[CellKey] = deque([start_key])
        visited.add(start_key)
        comp.add(start_key)
        while q:
            k = q.popleft()
            cur = key_to_cell[k]
            for nx, ny, nl in iter_four_neighbors(cur.x, cur.y, cur.layer):
                nk = (nx, ny, nl)
                if nk not in traversable_keys or nk in visited:
                    continue
                nxt = key_to_cell[nk]
                if not _allow_edge(cur, nxt, evidence):
                    continue
                visited.add(nk)
                comp.add(nk)
                q.append(nk)

        targets_in_comp = {k for k in comp if k in stamp_target_keys}
        if not targets_in_comp:
            continue
        kind = resolve_island_kind(targets_in_comp, key_to_cell, evidence)
        for k in targets_in_comp:
            stamp_by_key[k] = kind

    out: list[DecodedCellDTO] = []
    for c in out_cells:
        k = (c.x, c.y, c.layer)
        if k in stamp_by_key:
            out.append(replace(c, cell_kind=stamp_by_key[k]))
        else:
            out.append(c)
    return tuple(sorted(out, key=sort_key_xy_layer))
