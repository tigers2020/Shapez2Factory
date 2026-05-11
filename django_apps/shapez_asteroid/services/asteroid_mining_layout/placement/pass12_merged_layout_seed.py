"""Seed Pass12LayoutScratch from merged with_transport+final map (preserve-first).

Mineable cells that already hold extractors/extensions must block Pass1/Pass2 from
treating them as empty slots (see ``scratch_from_working_map`` mineable-only blocked rule).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from typing import Any

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import (
    output_offset_r,
    shape_miner_output_cell,
)
from django_apps.shapez_asteroid.extraction.shapez_grid import (
    neighbors4,
    require_cardinal_unit_toward,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_contracts import (
    Pass12LayoutScratch,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
    make_placement_id,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    EXTENSIONS,
    EXTRACTORS_FLUID,
    EXTRACTORS_SHAPE,
    layout_kind,
    transport_kind_for_extractor,
    want_role,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
    final_validation as _final_validation,
)


def _mining_building_neighbors(
    c: Coord, cells: Mapping[Coord, dict[str, Any]], mineable: frozenset[Coord]
) -> tuple[Coord, ...]:
    x, y = c
    out: list[Coord] = []
    for n in neighbors4(x, y):
        if n not in mineable or n not in cells:
            continue
        row = cells[n]
        if row.get("role") != "occupied":
            continue
        lk = layout_kind(row)
        if lk in EXTRACTORS_SHAPE | EXTRACTORS_FLUID | EXTENSIONS:
            out.append(n)
    return tuple(sorted(out, key=lambda p: (p[1], p[0])))


def _bfs_extensions_from_miner(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
    extension_owner: dict[Coord, Coord],
) -> frozenset[Coord]:
    """Extensions reachable from ``miner`` without crossing another extractor."""

    found: set[Coord] = set()
    q: deque[Coord] = deque()
    for n in _mining_building_neighbors(miner, cells, mineable):
        lk = layout_kind(cells[n])
        if lk not in EXTENSIONS:
            continue
        prev = extension_owner.get(n)
        if prev is not None and prev != miner:
            continue
        extension_owner[n] = miner
        found.add(n)
        q.append(n)
    while q:
        cur = q.popleft()
        for n in _mining_building_neighbors(cur, cells, mineable):
            lk = layout_kind(cells[n])
            if lk in EXTRACTORS_SHAPE | EXTRACTORS_FLUID:
                if n != miner:
                    continue
            if lk not in EXTENSIONS:
                continue
            prev = extension_owner.get(n)
            if prev is not None and prev != miner:
                continue
            if n not in extension_owner:
                extension_owner[n] = miner
            if n not in found:
                found.add(n)
                q.append(n)
    return frozenset(found)


def _extension_facing_parent(ext: Coord, parent_by_cell: dict[Coord, Coord]) -> tuple[int, int]:
    p = parent_by_cell[ext]
    if p == ext:
        return (1, 0)
    return require_cardinal_unit_toward(ext, p)


def _parent_tree_for_miner_and_extensions(
    miner: Coord,
    exts: frozenset[Coord],
    cells: Mapping[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
) -> dict[Coord, Coord]:
    """BFS parent links from ``miner`` through ``exts`` only."""

    parent_by_cell: dict[Coord, Coord] = {miner: miner}
    q: deque[Coord] = deque([miner])
    seen = {miner}
    while q:
        cur = q.popleft()
        for n in _mining_building_neighbors(cur, cells, mineable):
            if n not in exts:
                continue
            if n in seen:
                continue
            parent_by_cell[n] = cur
            seen.add(n)
            q.append(n)
    return parent_by_cell


def seed_pass12_scratch_from_merged_existing(
    merged_mining_map: list[dict[str, Any]],
    *,
    mineable: frozenset[Coord],
    scratch: Pass12LayoutScratch,
) -> dict[str, int]:
    """Populate scratch with extractors/extensions already on mineable in ``merged_mining_map``.

    Creates ``PlacementCommitRecord`` rows in ``ROUTED_CONFIRMED`` when stub transport matches
    the extractor kind so STEP4 treats them as finalized bundles.

    Returns count stats for solver summary (caller merges into pass12_stats).
    """

    cells = _final_validation.cells_dict_from_mining_map(merged_mining_map)
    miners: list[Coord] = []
    for c, row in cells.items():
        if c not in mineable or row.get("role") != "occupied":
            continue
        lk = layout_kind(row)
        if lk in EXTRACTORS_SHAPE | EXTRACTORS_FLUID:
            miners.append(c)
    miners.sort(key=lambda p: (p[1], p[0]))

    extension_owner: dict[Coord, Coord] = {}
    seeded_groups = 0
    seeded_routed_records = 0
    for miner in miners:
        exts = _bfs_extensions_from_miner(miner, cells, mineable, extension_owner)
        parent_by_cell = _parent_tree_for_miner_and_extensions(miner, exts, cells, mineable)

        row_m = cells[miner]
        raw_r = row_m.get("r")
        tk = transport_kind_for_extractor(row_m)
        eff_r: int | None = int(raw_r) if isinstance(raw_r, int) else None
        if eff_r is None and tk is not None:
            wr_probe = want_role(tk)
            for cand_r in range(4):
                sc = shape_miner_output_cell(miner, cand_r)
                if sc and cells.get(sc, {}).get("role") == wr_probe:
                    eff_r = cand_r
                    break
        stub_cell: Coord | None = None
        routed_ok = False
        if eff_r is not None and tk is not None:
            stub_cell = shape_miner_output_cell(miner, eff_r)
            if stub_cell is not None:
                st = cells.get(stub_cell)
                wr = want_role(tk)
                if st is not None and st.get("role") == wr:
                    routed_ok = True

        ext_tuple = tuple(sorted(exts, key=lambda p: (p[1], p[0])))

        if routed_ok and tk is not None and stub_cell is not None and eff_r is not None:
            scratch.blocked_cells |= {miner} | set(exts)
            scratch.extractor_cells.add(miner)
            scratch.extractor_output_dirs[miner] = output_offset_r(eff_r)
            for ext in sorted(exts, key=lambda p: (p[1], p[0])):
                if ext in parent_by_cell and parent_by_cell[ext] != ext:
                    scratch.extension_facings[ext] = _extension_facing_parent(ext, parent_by_cell)
            scratch.next_placement_seq += 1
            pid = make_placement_id("pass1", scratch.next_placement_seq)
            scratch.placement_records[pid] = PlacementCommitRecord(
                placement_id=pid,
                placement_pass="pass1",
                extractor_cell=miner,
                extension_cells=ext_tuple,
                stub_cell=stub_cell,
                transport_kind=tk,
                state=PlacementCommitState.ROUTED_CONFIRMED,
                route_id="preserve_merged_seed",
            )
            seeded_routed_records += 1
        elif len(miners) == 1:
            # Single mineable extractor with no confirmed stub link: block Pass1/Pass2 and
            # keep merged rows. (Multi-miner maps leave cells unblocked when unrouted so Pass1
            # can still replace misaligned miners without perturbing belt fixtures.)
            scratch.blocked_cells |= {miner} | set(exts)
            scratch.preserved_mining_row_overrides[miner] = dict(row_m)
            for ext in exts:
                scratch.preserved_mining_row_overrides[ext] = dict(cells[ext])
        seeded_groups += 1

    for c, row in cells.items():
        if c not in mineable or row.get("role") != "occupied":
            continue
        if layout_kind(row) not in EXTENSIONS:
            continue
        if c in scratch.blocked_cells:
            continue
        scratch.blocked_cells.add(c)
        nbrs = _mining_building_neighbors(c, cells, mineable)
        parent: Coord | None = None
        for n in nbrs:
            lk_n = layout_kind(cells[n])
            if lk_n in EXTRACTORS_SHAPE | EXTRACTORS_FLUID | EXTENSIONS:
                parent = n
                break
        if parent is not None:
            scratch.extension_facings[c] = require_cardinal_unit_toward(c, parent)
        else:
            scratch.extension_facings[c] = (1, 0)

    return {
        "pass12_preserved_equipment_groups": seeded_groups,
        "pass12_preserved_routed_placement_records": seeded_routed_records,
    }
