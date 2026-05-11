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
    rotation_r_for_output_direction,
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


def _preserve_first_hard_gate(existing_layout_source_kind: str | None) -> bool:
    """True when Pass1 must not clear unrouted merged bundles (fluid existing maps only)."""

    return existing_layout_source_kind == "existing_fluid_layout"


def _strip_provisional_placement_row_keys(row: dict[str, Any]) -> dict[str, Any]:
    """Remove row FSM markers that would fail final geometry validation on preserved copies."""

    out = dict(row)
    for key in ("placement_state", "placement_commit_state"):
        v = out.get(key)
        if isinstance(v, str) and v.lower() in ("quarantined_unrouted", "provisional_placed"):
            out.pop(key, None)
    return out


def _first_rotation_with_matching_stub(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
    transport_kind: str,
    raw_r: Any,
) -> int | None:
    """Prefer declared ``r`` when its stub matches; else first ``r`` in 0..3 with matching stub."""

    wr = want_role(transport_kind)
    order: list[int] = []
    if isinstance(raw_r, int):
        order.append(raw_r % 4)
    for r in range(4):
        if r not in order:
            order.append(r)
    for cand_r in order:
        sc = shape_miner_output_cell(miner, cand_r)
        if sc is None:
            continue
        st = cells.get(sc)
        if st is not None and st.get("role") == wr:
            return cand_r
    return None


def _neighbor_stub_coords_for_kind(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
    transport_kind: str,
) -> tuple[Coord, ...]:
    """Cardinal neighbours whose mining-map role matches this extractor transport kind."""

    wr = want_role(transport_kind)
    x, y = miner
    found: list[Coord] = []
    for nxt in neighbors4(x, y):
        row = cells.get(nxt)
        if row is not None and row.get("role") == wr:
            found.append(nxt)
    return tuple(sorted(found, key=lambda p: (p[1], p[0])))


def _rotation_from_sorted_neighbor_stub(
    miner: Coord,
    neighbor_stubs: tuple[Coord, ...],
) -> int | None:
    """Pick deterministic stub among cardinally adjacent belt/pipe cells and yield ``r``."""

    for stub in neighbor_stubs:
        dx, dy = stub[0] - miner[0], stub[1] - miner[1]
        if dx != 0 and dy != 0:
            continue
        try:
            return rotation_r_for_output_direction(dx, dy)
        except ValueError:
            continue
    return None


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
    existing_layout_source_kind: str | None = None,
) -> dict[str, Any]:
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
    preserved_bundle_extractor_cells = 0
    preserved_bundle_extension_cells = 0
    preserved_unrouted_extractor_count = 0
    preserved_missing_stub_drop_extractor_count = 0
    preserved_stripped_rotation_fallback_count = 0
    for miner in miners:
        exts = _bfs_extensions_from_miner(miner, cells, mineable, extension_owner)
        parent_by_cell = _parent_tree_for_miner_and_extensions(miner, exts, cells, mineable)

        row_m = cells[miner]
        tk = transport_kind_for_extractor(row_m)
        neighbor_stub_coords: tuple[Coord, ...] = ()
        eff_r: int | None = None
        stub_cell: Coord | None = None
        routed_ok = False
        if tk is not None:
            eff_r = _first_rotation_with_matching_stub(miner, cells, tk, row_m.get("r"))
            neighbor_stub_coords = _neighbor_stub_coords_for_kind(miner, cells, tk)
            if eff_r is None:
                eff_r = _rotation_from_sorted_neighbor_stub(miner, neighbor_stub_coords)
            if eff_r is not None:
                stub_cell = shape_miner_output_cell(miner, eff_r)
                wr = want_role(tk)
                st = cells.get(stub_cell) if stub_cell is not None else None
                routed_ok = st is not None and st.get("role") == wr
        else:
            raw_only = row_m.get("r")
            if isinstance(raw_only, int):
                eff_r = raw_only % 4
                stub_cell = shape_miner_output_cell(miner, eff_r)

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
            preserved_bundle_extractor_cells += 1
            preserved_bundle_extension_cells += len(exts)
        elif _preserve_first_hard_gate(existing_layout_source_kind) or len(miners) == 1:
            # Fluid existing maps: block every unrouted bundle (multi-miner half-preserve guard).
            # Any map with a single merged miner: always block the bundle when not ROUTED_CONFIRMED
            # so Pass1 cannot erase the lone body (``raw_asteroid_field`` and legacy behavior).
            drop_unrecoverable = (
                _preserve_first_hard_gate(existing_layout_source_kind)
                and len(miners) > 1
                and tk is not None
                and not routed_ok
                and len(neighbor_stub_coords) == 0
            )
            if drop_unrecoverable:
                preserved_missing_stub_drop_extractor_count += 1
                seeded_groups += 1
                continue

            scratch.blocked_cells |= {miner} | set(exts)
            miner_row = _strip_provisional_placement_row_keys(row_m)
            if tk is not None and neighbor_stub_coords and not routed_ok:
                miner_row.pop("r", None)
                preserved_stripped_rotation_fallback_count += 1
            elif eff_r is not None:
                miner_row["r"] = eff_r
            scratch.preserved_mining_row_overrides[miner] = miner_row
            for ext in exts:
                scratch.preserved_mining_row_overrides[ext] = _strip_provisional_placement_row_keys(
                    dict(cells[ext])
                )
            preserved_bundle_extractor_cells += 1
            preserved_bundle_extension_cells += len(exts)
            preserved_unrouted_extractor_count += 1
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

    sk = existing_layout_source_kind or "unspecified"
    return {
        "pass12_preserved_equipment_groups": seeded_groups,
        "pass12_preserved_routed_placement_records": seeded_routed_records,
        "pass12_preserve_first_source_kind": sk,
        "pass12_preserved_bundle_extractor_cells": preserved_bundle_extractor_cells,
        "pass12_preserved_bundle_extension_cells": preserved_bundle_extension_cells,
        "pass12_preserved_routed_confirmed_count": seeded_routed_records,
        "pass12_preserved_unrouted_extractor_count": preserved_unrouted_extractor_count,
        "pass12_preserved_missing_stub_drop_extractor_count": (
            preserved_missing_stub_drop_extractor_count
        ),
        "pass12_preserved_stripped_rotation_fallback_count": (
            preserved_stripped_rotation_fallback_count
        ),
    }
