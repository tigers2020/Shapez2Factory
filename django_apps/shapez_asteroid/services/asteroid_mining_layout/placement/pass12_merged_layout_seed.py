"""Seed Pass12LayoutScratch from merged with_transport+final map (preserve-first).

Mineable cells that already hold extractors/extensions must block Pass1/Pass2 from
treating them as empty slots (see ``scratch_from_working_map`` mineable-only blocked rule).
"""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from enum import StrEnum
from typing import Any

from django.conf import settings

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import (
    output_offset_r,
    rotation_r_for_output_direction,
    shape_miner_output_cell,
)
from django_apps.shapez_asteroid.extraction.shapez_grid import (
    neighbors4,
    require_cardinal_unit_toward,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    MAX_PASS12_NEAREST_TRANSPORT_TRACE_HOPS,
    MAX_PASS12_RECOVERY_BFS_HOPS,
    MAX_PASS12_RECOVERY_PROBES_PER_MINER,
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


class PreserveDropReason(StrEnum):
    """Fixed taxonomy for preserve-first merged-seed extractor drops (histogram / CI)."""

    NO_ADJACENT_TRANSPORT = "NO_ADJACENT_TRANSPORT"
    NO_MATCHING_STUB = "NO_MATCHING_STUB"
    NO_VALID_ROTATION = "NO_VALID_ROTATION"
    ORPHAN_COMPONENT = "ORPHAN_COMPONENT"
    NON_CARDINAL_OUTPUT = "NON_CARDINAL_OUTPUT"
    MIXED_KIND_CONFLICT = "MIXED_KIND_CONFLICT"
    INVALID_EXISTING_ROW = "INVALID_EXISTING_ROW"


class RecoverabilityClass(StrEnum):
    """Salvageability tier above ``PreserveDropReason`` (trace / dashboards; static rules)."""

    TRIVIAL = "TRIVIAL"
    LOCAL_ROTATION = "LOCAL_ROTATION"
    NEAR_TRANSPORT = "NEAR_TRANSPORT"
    NEEDS_REROUTE = "NEEDS_REROUTE"
    UNRECOVERABLE = "UNRECOVERABLE"


def _detail_adjacent_same_kind_transport(detail: Mapping[str, Any], want_wr: str) -> bool:
    """True when a cardinal neighbour row already matches ``want_wr`` (belt/pipe role)."""

    for key in ("adjacent_transport_cells", "adjacent_cardinal_cells"):
        cells = detail.get(key)
        if not isinstance(cells, list):
            continue
        for e in cells:
            if isinstance(e, dict) and e.get("role") == want_wr:
                return True
    rot = detail.get("rotation_probe_summary")
    if isinstance(rot, list):
        for e in rot:
            if isinstance(e, dict) and e.get("matches") is True:
                return True
    return False


def _recoverability_band_from_nearest_hops(
    hops: int, *, max_recovery_bfs_hops: int
) -> RecoverabilityClass:
    """TRIVIAL / NEAR_TRANSPORT / NEEDS_REROUTE from integer BFS hop distance."""

    if hops <= 1:
        return RecoverabilityClass.TRIVIAL
    if hops <= max_recovery_bfs_hops:
        return RecoverabilityClass.NEAR_TRANSPORT
    return RecoverabilityClass.NEEDS_REROUTE


def recoverability_class_for_preserve_drop_detail(
    detail: Mapping[str, Any],
    *,
    max_recovery_bfs_hops: int = MAX_PASS12_RECOVERY_BFS_HOPS,
) -> RecoverabilityClass:
    """Map a single drop detail dict to ``RecoverabilityClass`` (reviewer static table v1)."""

    raw = detail.get("preserve_drop_reason") or detail.get("reason")
    try:
        pdr = PreserveDropReason(str(raw)) if raw is not None else None
    except ValueError:
        pdr = None
    if pdr is None:
        return RecoverabilityClass.NEEDS_REROUTE
    hops_raw = detail.get("nearest_same_kind_transport_hops")
    hops = int(hops_raw) if isinstance(hops_raw, int) else None
    want_wr = str(detail.get("expected_stub_role") or "")

    if pdr in (PreserveDropReason.ORPHAN_COMPONENT, PreserveDropReason.INVALID_EXISTING_ROW):
        return RecoverabilityClass.UNRECOVERABLE
    if pdr == PreserveDropReason.MIXED_KIND_CONFLICT:
        return RecoverabilityClass.NEEDS_REROUTE
    if pdr == PreserveDropReason.NON_CARDINAL_OUTPUT:
        return RecoverabilityClass.LOCAL_ROTATION
    if pdr == PreserveDropReason.NO_VALID_ROTATION:
        if want_wr and _detail_adjacent_same_kind_transport(detail, want_wr):
            return RecoverabilityClass.TRIVIAL
        return RecoverabilityClass.LOCAL_ROTATION
    if pdr == PreserveDropReason.NO_MATCHING_STUB:
        if hops is None:
            return RecoverabilityClass.NEEDS_REROUTE
        return _recoverability_band_from_nearest_hops(
            hops,
            max_recovery_bfs_hops=max_recovery_bfs_hops,
        )
    if pdr == PreserveDropReason.NO_ADJACENT_TRANSPORT:
        if hops is None:
            return RecoverabilityClass.UNRECOVERABLE
        return _recoverability_band_from_nearest_hops(
            hops,
            max_recovery_bfs_hops=max_recovery_bfs_hops,
        )
    return RecoverabilityClass.NEEDS_REROUTE


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


def _cardinal_neighbor_cell_summaries(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
) -> list[dict[str, Any]]:
    """All existing cardinal neighbors with role/layout_kind (debug / drop trace)."""

    x, y = miner
    out: list[dict[str, Any]] = []
    for nxt in neighbors4(x, y):
        row = cells.get(nxt)
        if row is None:
            continue
        rv = row.get("role")
        role_s = str(rv) if isinstance(rv, str) else None
        out.append(
            {
                "cell": [int(nxt[0]), int(nxt[1])],
                "role": role_s,
                "layout_kind": layout_kind(row),
            }
        )
    out.sort(key=lambda e: (e["cell"][1], e["cell"][0]))
    return out


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


def _nearest_same_role_transport_bfs(
    start: Coord,
    *,
    want_wr: str,
    cells: Mapping[Coord, dict[str, Any]],
    max_hops: int,
) -> tuple[int | None, Coord | None]:
    """Cardinal BFS on ``cells`` keys until a row with ``role == want_wr`` (transport trace)."""

    if start not in cells:
        return None, None
    q: deque[Coord] = deque([start])
    dist: dict[Coord, int] = {start: 0}
    visits = 0
    while q:
        c = q.popleft()
        visits += 1
        if visits > 50_000:
            return None, None
        d0 = dist[c]
        row = cells.get(c)
        if row is not None and row.get("role") == want_wr:
            return d0, c
        if d0 >= max_hops:
            continue
        x, y = c
        for v in neighbors4(x, y):
            if v not in cells or v in dist:
                continue
            dist[v] = d0 + 1
            q.append(v)
    return None, None


def _rotation_probe_summary(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
    transport_kind: str,
    raw_r: Any,
) -> list[dict[str, Any]]:
    """Per-rotation stub trace; probe order matches ``_first_rotation_with_matching_stub``."""

    wr = want_role(transport_kind)
    order: list[int] = []
    if isinstance(raw_r, int):
        order.append(raw_r % 4)
    for r in range(4):
        if r not in order:
            order.append(r)
    out: list[dict[str, Any]] = []
    for cand_r in order:
        sc = shape_miner_output_cell(miner, cand_r)
        if sc is None:
            out.append({"r": cand_r, "stub_cell": None, "stub_role": None, "matches": False})
            continue
        st = cells.get(sc)
        role = st.get("role") if st is not None else None
        role_s = str(role) if isinstance(role, str) else None
        out.append(
            {
                "r": cand_r,
                "stub_cell": [int(sc[0]), int(sc[1])],
                "stub_role": role_s,
                "matches": st is not None and role == wr,
            }
        )
    return out


def _relaxed_stub_matches_row(row: dict[str, Any], want_wr: str) -> bool:
    """Recovery-only: infer belt/pipe stub from ``layout_kind`` when ``role`` is wrong."""

    role = row.get("role")
    if role == want_wr:
        return True
    lk = (layout_kind(row) or "").lower()
    building_like = (
        "fluid_miner",
        "fluid_extension",
        "shape_miner",
        "shape_extension",
    )
    if want_wr == "pipe":
        return "pipe" in lk and lk not in building_like
    if want_wr == "belt":
        return "belt" in lk and lk not in building_like
    return False


def _first_rotation_with_relaxed_stub_match(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
    transport_kind: str,
    raw_r: Any,
) -> int | None:
    """Like ``_first_rotation_with_matching_stub`` but uses ``_relaxed_stub_matches_row``."""

    wr = want_role(transport_kind)
    order: list[int] = []
    if isinstance(raw_r, int):
        order.append(raw_r % 4)
    for r in range(4):
        if r not in order:
            order.append(r)
    n = 0
    for cand_r in order:
        n += 1
        if n > MAX_PASS12_RECOVERY_PROBES_PER_MINER:
            break
        sc = shape_miner_output_cell(miner, cand_r)
        if sc is None:
            continue
        st = cells.get(sc)
        if st is not None and _relaxed_stub_matches_row(st, wr):
            return cand_r
    return None


def _neighbor_stub_coords_relaxed(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
    transport_kind: str,
    *,
    use_relaxed: bool,
) -> tuple[Coord, ...]:
    wr = want_role(transport_kind)
    found: list[Coord] = []
    x, y = miner
    for nxt in neighbors4(x, y):
        row = cells.get(nxt)
        if row is None:
            continue
        if row.get("role") == wr:
            found.append(nxt)
        elif use_relaxed and _relaxed_stub_matches_row(row, wr):
            found.append(nxt)
    return tuple(sorted(found, key=lambda p: (p[1], p[0])))


def _routed_ok_at_rotation(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
    transport_kind: str,
    eff_r: int,
) -> bool:
    wr = want_role(transport_kind)
    stub_cell = shape_miner_output_cell(miner, eff_r)
    if stub_cell is None:
        return False
    st = cells.get(stub_cell)
    if st is None:
        return False
    if st.get("role") == wr:
        return True
    return _relaxed_stub_matches_row(st, wr)


def _attempt_preserve_stub_recovery(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
    transport_kind: str,
    row_m: dict[str, Any],
    neighbor_stub_coords: tuple[Coord, ...],
    eff_r: int | None,
    routed_ok: bool,
) -> tuple[tuple[Coord, ...], int | None, bool, dict[str, Any]] | None:
    """Optional relaxed stub inference; returns new state + provenance, or ``None``."""

    if not getattr(settings, "SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY", False):
        return None
    if routed_ok or neighbor_stub_coords:
        return None
    relaxed_coords = _neighbor_stub_coords_relaxed(miner, cells, transport_kind, use_relaxed=True)
    if relaxed_coords == ():
        return None
    new_eff = _rotation_from_sorted_neighbor_stub(miner, relaxed_coords)
    if new_eff is None:
        new_eff = _first_rotation_with_relaxed_stub_match(
            miner, cells, transport_kind, row_m.get("r")
        )
    if new_eff is None:
        return None
    new_routed = _routed_ok_at_rotation(miner, cells, transport_kind, new_eff)
    if not new_routed:
        return None
    provenance: dict[str, Any] = {
        "applied": True,
        "recovery_mode": ["relaxed_layout_kind_stub_match", "rotation_recovered"],
        "miner_cell": [int(miner[0]), int(miner[1])],
        "original_rotation": (int(row_m["r"]) % 4) if isinstance(row_m.get("r"), int) else None,
        "recovered_rotation": int(new_eff),
        "relaxed_stub_coords": [[int(c[0]), int(c[1])] for c in relaxed_coords],
        "recovery_bfs_hops_budget": MAX_PASS12_RECOVERY_BFS_HOPS,
        "recovery_probe_budget": MAX_PASS12_RECOVERY_PROBES_PER_MINER,
    }
    return relaxed_coords, new_eff, new_routed, provenance


def _classify_preserve_drop_reason(
    *,
    want_wr: str,
    cardinals: list[dict[str, Any]],
    nearest_hops: int | None,
) -> PreserveDropReason:
    roles = [c.get("role") for c in cardinals if isinstance(c.get("role"), str)]
    belt_pipe = [r for r in roles if r in ("belt", "pipe")]
    if belt_pipe and not any(r == want_wr for r in belt_pipe):
        return PreserveDropReason.MIXED_KIND_CONFLICT
    if belt_pipe and any(r == want_wr for r in belt_pipe):
        return PreserveDropReason.NO_VALID_ROTATION
    if nearest_hops is not None and nearest_hops >= 1:
        return PreserveDropReason.NO_MATCHING_STUB
    if nearest_hops is None:
        return PreserveDropReason.ORPHAN_COMPONENT
    return PreserveDropReason.NO_ADJACENT_TRANSPORT


def _miner_missing_stub_drop_eligibility(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
    *,
    merged_seed_miner_count: int,
    existing_layout_source_kind: str | None,
) -> tuple[bool, int | None]:
    """Whether this miner hits the preserve-first missing-stub drop path + nearest hops."""

    if not (_preserve_first_hard_gate(existing_layout_source_kind) and merged_seed_miner_count > 1):
        return False, None
    row_m = cells.get(miner)
    if row_m is None or row_m.get("role") != "occupied":
        return False, None
    if layout_kind(row_m) not in EXTRACTORS_SHAPE | EXTRACTORS_FLUID:
        return False, None
    tk = transport_kind_for_extractor(row_m)
    if tk is None:
        return False, None
    eff_r = _first_rotation_with_matching_stub(miner, cells, tk, row_m.get("r"))
    neighbor_stub_coords = _neighbor_stub_coords_for_kind(miner, cells, tk)
    if eff_r is None:
        eff_r = _rotation_from_sorted_neighbor_stub(miner, neighbor_stub_coords)
    stub_cell = shape_miner_output_cell(miner, eff_r) if eff_r is not None else None
    wr = want_role(tk)
    st = cells.get(stub_cell) if stub_cell is not None else None
    routed_ok = st is not None and st.get("role") == wr
    would_drop = not routed_ok and len(neighbor_stub_coords) == 0
    if not would_drop:
        return False, None
    nhops, _ncell = _nearest_same_role_transport_bfs(
        miner,
        want_wr=wr,
        cells=cells,
        max_hops=MAX_PASS12_NEAREST_TRANSPORT_TRACE_HOPS,
    )
    return True, nhops


def _recovery_proximity_sort_key(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
    *,
    merged_seed_miner_count: int,
    existing_layout_source_kind: str | None,
) -> tuple[int, int, int, int]:
    """Lower tuple sorts earlier: non-drop miners first, then drop miners by nearest hops."""

    wd, nh = _miner_missing_stub_drop_eligibility(
        miner,
        cells,
        merged_seed_miner_count=merged_seed_miner_count,
        existing_layout_source_kind=existing_layout_source_kind,
    )
    if not wd:
        return (0, 0, miner[1], miner[0])
    if nh is None:
        return (1, 10**9, miner[1], miner[0])
    return (1, nh, miner[1], miner[0])


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
    merged_seed_miner_count = len(miners)
    if getattr(settings, "SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY", False):
        miners = sorted(
            miners,
            key=lambda m: _recovery_proximity_sort_key(
                m,
                cells,
                merged_seed_miner_count=merged_seed_miner_count,
                existing_layout_source_kind=existing_layout_source_kind,
            ),
        )

    extension_owner: dict[Coord, Coord] = {}
    seeded_groups = 0
    seeded_routed_records = 0
    preserved_bundle_extractor_cells = 0
    preserved_bundle_extension_cells = 0
    preserved_unrouted_extractor_count = 0
    preserved_missing_stub_drop_extractor_count = 0
    preserved_stripped_rotation_fallback_count = 0
    missing_stub_drop_details: list[dict[str, Any]] = []
    preserve_drop_reason_counts: dict[str, int] = {}
    recoverability_class_counts: dict[str, int] = {}
    preserved_recovery_traces: list[dict[str, Any]] = []
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

        would_drop_unrecoverable = (
            _preserve_first_hard_gate(existing_layout_source_kind)
            and merged_seed_miner_count > 1
            and tk is not None
            and not routed_ok
            and len(neighbor_stub_coords) == 0
        )
        if would_drop_unrecoverable:
            assert tk is not None
            rec = _attempt_preserve_stub_recovery(
                miner, cells, tk, row_m, neighbor_stub_coords, eff_r, routed_ok
            )
            if rec is not None:
                neighbor_stub_coords, eff_r, routed_ok, _prov = rec
                preserved_recovery_traces.append(dict(_prov))
                if routed_ok and eff_r is not None and tk is not None:
                    stub_cell = shape_miner_output_cell(miner, eff_r)

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
                and merged_seed_miner_count > 1
                and tk is not None
                and not routed_ok
                and len(neighbor_stub_coords) == 0
            )
            if drop_unrecoverable:
                assert tk is not None
                preserved_missing_stub_drop_extractor_count += 1
                wr_exp = want_role(tk)
                cardinals = _cardinal_neighbor_cell_summaries(miner, cells)
                transport_adj = [e for e in cardinals if e.get("role") in ("belt", "pipe")]
                nhops, ncell = _nearest_same_role_transport_bfs(
                    miner,
                    want_wr=wr_exp,
                    cells=cells,
                    max_hops=MAX_PASS12_NEAREST_TRANSPORT_TRACE_HOPS,
                )
                pdr = _classify_preserve_drop_reason(
                    want_wr=wr_exp,
                    cardinals=cardinals,
                    nearest_hops=nhops,
                )
                prev_n = preserve_drop_reason_counts.get(pdr.value, 0)
                preserve_drop_reason_counts[pdr.value] = prev_n + 1
                raw_rr = row_m.get("r")
                existing_row_r = int(raw_rr) % 4 if isinstance(raw_rr, int) else None
                rot_summary = (
                    _rotation_probe_summary(miner, cells, tk, row_m.get("r"))
                    if tk is not None
                    else []
                )
                detail_row: dict[str, Any] = {
                    "miner_cell": [int(miner[0]), int(miner[1])],
                    "reason": pdr.value,
                    "preserve_drop_reason": pdr.value,
                    "transport_kind": tk,
                    "expected_stub_role": wr_exp,
                    "pass12_merged_seed_miner_count": merged_seed_miner_count,
                    "nearest_same_kind_transport_hops": nhops,
                    "nearest_same_kind_transport_cell": (
                        None if ncell is None else [int(ncell[0]), int(ncell[1])]
                    ),
                    "rotation_probe_summary": rot_summary,
                    "matching_adjacent_stub_coords": [
                        [int(c[0]), int(c[1])] for c in neighbor_stub_coords
                    ],
                    "adjacent_transport_cells": transport_adj,
                    "adjacent_cardinal_cells": cardinals,
                    "existing_row_r": existing_row_r,
                    "recovered_r": eff_r,
                }
                _rc = recoverability_class_for_preserve_drop_detail(detail_row)
                detail_row["recoverability_class"] = _rc.value
                recoverability_class_counts[_rc.value] = (
                    recoverability_class_counts.get(_rc.value, 0) + 1
                )
                missing_stub_drop_details.append(detail_row)
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
        "pass12_merged_seed_miner_count": merged_seed_miner_count,
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
        "pass12_preserved_missing_stub_drop_details": missing_stub_drop_details,
        "pass12_preserve_drop_reason_counts": dict(
            sorted(preserve_drop_reason_counts.items(), key=lambda kv: kv[0])
        ),
        "pass12_recoverability_class_counts": dict(
            sorted(recoverability_class_counts.items(), key=lambda kv: kv[0])
        ),
        "pass12_preserved_recovery_traces": preserved_recovery_traces,
        "pass12_preserved_recovery_success_count": len(preserved_recovery_traces),
        "pass12_preserved_stripped_rotation_fallback_count": (
            preserved_stripped_rotation_fallback_count
        ),
    }
