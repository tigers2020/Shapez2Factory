"""Equipment bundles: port-compatible connected components (replay overlay only).

Ports are **decode-rotation–aligned** sets at R=0, calibrated against a real asteroid
blueprint (see tests). Two extractors never share an edge even if facing ports match.
Each ``cells_json`` entry includes ``bundle_edges`` (hull toward non-bundle neighbors) and
``bundle_links`` (same-bundle grid neighbors for Lab gap bridges).
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from django_apps.asteroid_lab.snapshots.asteroid_map_coords import (
    iter_four_neighbors_map,
    left_of,
    right_of,
)

# Cardinal dirs aligned with ``iter_four_neighbors_map`` and Lab JS ``bundle_edges``.
# Map step: east = ``right_of(x)``, west = ``left_of(x)``, south = ``y + 1``, north = ``y - 1``.
_DIR_ORDER: tuple[str, str, str, str] = ("n", "e", "s", "w")

_OPPOSITE: dict[str, str] = {"n": "s", "s": "n", "e": "w", "w": "e"}

_EQUIPMENT_KINDS: frozenset[str] = frozenset(
    {
        "fluid_miner",
        "fluid_miner_extension",
        "shape_miner",
        "shape_miner_extension",
    }
)

# Extractors do not link to each other (no shared duct); extensions still chain by ports.
_MINER_KINDS: frozenset[str] = frozenset({"fluid_miner", "shape_miner"})


def _equipment_family(cell_kind: str) -> str | None:
    if cell_kind.startswith("fluid_"):
        return "fluid"
    if cell_kind.startswith("shape_"):
        return "shape"
    return None


def _as_int(val: Any) -> int:
    if val is None:
        return 0
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, int):
        return val
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def _rotate_dir_clockwise(d: str, quarter_turns: int) -> str:
    k = quarter_turns % 4
    if k == 0:
        return d
    i = _DIR_ORDER.index(d)
    return _DIR_ORDER[(i + k) % 4]


def _rotate_set(dirs: frozenset[str], quarter_turns: int) -> frozenset[str]:
    k = quarter_turns % 4
    if k == 0:
        return dirs
    return frozenset(_rotate_dir_clockwise(d, k) for d in dirs)


@dataclass(frozen=True, slots=True)
class EquipmentPorts:
    """Open equipment connection directions in map space (n/e/s/w)."""

    input_dirs: frozenset[str]
    output_dirs: frozenset[str]


# Base ports at rotation 0 — calibrated on a real asteroid blueprint (shape miners/extensions):
# input from ``e`` (field / upstream), outputs on ``n``, ``s``, ``w`` (T excluding east).
# ``rotation`` is decode ``R`` (quarter-turns from East at 0, increasing CW on the map); port dirs
# rotate CW by ``rotation % 4``. Lab sprite display uses ``LAB_SPRITE_REGISTRY`` only;
# do not duplicate that math here or bundle topology drifts.
_BASE_PORTS_R0: dict[str, tuple[frozenset[str], frozenset[str]]] = {
    "fluid_miner": (frozenset({"e"}), frozenset({"n", "s", "w"})),
    "fluid_miner_extension": (frozenset({"e"}), frozenset({"n", "s", "w"})),
    "shape_miner": (frozenset({"e"}), frozenset({"n", "s", "w"})),
    "shape_miner_extension": (frozenset({"e"}), frozenset({"n", "s", "w"})),
}


def equipment_ports(cell_kind: str, rotation: int) -> EquipmentPorts | None:
    """Return ports for ``cell_kind`` at ``rotation`` (quarter turns), or None if not equipment."""

    if cell_kind not in _EQUIPMENT_KINDS:
        return None
    base = _BASE_PORTS_R0.get(cell_kind)
    if base is None:
        return None
    ins0, outs0 = base
    q = _as_int(rotation) % 4
    return EquipmentPorts(
        input_dirs=_rotate_set(ins0, q),
        output_dirs=_rotate_set(outs0, q),
    )


def direction_from_a_to_b(ax: int, ay: int, bx: int, by: int) -> str | None:
    """Direction from cell A toward cell B if 4-neighbors on the asteroid map; else None."""

    if ax == 0 or bx == 0:
        return None
    if bx == right_of(ax) and by == ay:
        return "e"
    if bx == left_of(ax) and by == ay:
        return "w"
    if bx == ax and by == ay + 1:
        return "s"
    if bx == ax and by == ay - 1:
        return "n"
    return None


def _port_linked(
    ports_a: EquipmentPorts,
    ports_b: EquipmentPorts,
    dir_ab: str,
    cell_kind_a: str,
    cell_kind_b: str,
) -> bool:
    if cell_kind_a in _MINER_KINDS and cell_kind_b in _MINER_KINDS:
        return False
    dir_ba = _OPPOSITE[dir_ab]
    forward = dir_ab in ports_a.output_dirs and dir_ba in ports_b.input_dirs
    # B -> A: B emits along ``dir_ba``; A must accept along ``dir_ab`` toward B.
    backward = dir_ba in ports_b.output_dirs and dir_ab in ports_a.input_dirs
    return forward or backward


def _layer_key(row: Mapping[str, Any]) -> int | None:
    if "layer" not in row or row["layer"] is None:
        return None
    return _as_int(row["layer"])


def _cell_pos_key(row: Mapping[str, Any]) -> tuple[int, int, int | None]:
    return (_as_int(row["x"]), _as_int(row["y"]), _layer_key(row))


_Pos = tuple[int, int, int | None]


def _pos_sort_tuple(p: _Pos) -> tuple[int, int, int]:
    layer_key = -(10**9) if p[2] is None else int(p[2])
    return (p[0], p[1], layer_key)


class _UnionFind:
    def __init__(self, keys: Sequence[_Pos]) -> None:
        self._p: dict[_Pos, _Pos] = {k: k for k in keys}

    def find(self, k: _Pos) -> _Pos:
        parent = self._p[k]
        if parent != k:
            self._p[k] = self.find(parent)
        return self._p[k]

    def union(self, a: _Pos, b: _Pos) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self._p[rb] = ra


def _iter_equipment_rows(
    rows: Sequence[Mapping[str, Any]],
) -> Iterator[tuple[_Pos, Mapping[str, Any], EquipmentPorts, str, str]]:
    for row in rows:
        ck = str(row.get("cell_kind") or "")
        if ck not in _EQUIPMENT_KINDS:
            continue
        fam = _equipment_family(ck)
        if fam is None:
            continue
        x = _as_int(row.get("x"))
        if x == 0:
            continue
        ports = equipment_ports(ck, _as_int(row.get("rotation")))
        if ports is None:
            continue
        yield (_cell_pos_key(row), row, ports, fam, ck)


def _bundle_edges_for_cell(
    pos: _Pos,
    bundle_positions: frozenset[_Pos],
) -> str:
    x, y, layer = pos
    parts: list[str] = []
    for nx, ny, nl in iter_four_neighbors_map(x, y, layer):
        npos = (nx, ny, nl)
        d = direction_from_a_to_b(x, y, nx, ny)
        if d is None:
            continue
        if npos not in bundle_positions:
            parts.append(d)
    return "".join(sorted(parts, key=lambda s: _DIR_ORDER.index(s)))


def _bundle_links_for_cell(
    pos: _Pos,
    bundle_positions: frozenset[_Pos],
) -> str:
    """Directions toward a grid neighbor inside the same bundle (Lab gap bridges)."""

    x, y, layer = pos
    parts: list[str] = []
    for nx, ny, nl in iter_four_neighbors_map(x, y, layer):
        npos = (nx, ny, nl)
        d = direction_from_a_to_b(x, y, nx, ny)
        if d is None:
            continue
        if npos in bundle_positions:
            parts.append(d)
    return "".join(sorted(parts, key=lambda s: _DIR_ORDER.index(s)))


def build_equipment_bundles(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Group equipment cells by undirected port-compatible adjacency (same layer, same family)."""

    items = list(_iter_equipment_rows(rows))
    if not items:
        return []

    pos_to_row: dict[_Pos, Mapping[str, Any]] = {}
    pos_to_ports: dict[_Pos, EquipmentPorts] = {}
    pos_to_family: dict[_Pos, str] = {}
    pos_to_kind: dict[_Pos, str] = {}
    for pos, row, ports, fam, ck in items:
        pos_to_row[pos] = row
        pos_to_ports[pos] = ports
        pos_to_family[pos] = fam
        pos_to_kind[pos] = ck

    keys = list(pos_to_row)
    uf = _UnionFind(keys)

    for pos, _row, ports_a, fam_a, ck_a in items:
        x, y, layer = pos
        for nx, ny, nl in iter_four_neighbors_map(x, y, layer):
            npos = (nx, ny, nl)
            if npos not in pos_to_row:
                continue
            if pos_to_family[npos] != fam_a:
                continue
            dir_ab = direction_from_a_to_b(x, y, nx, ny)
            if dir_ab is None:
                continue
            ports_b = pos_to_ports[npos]
            ck_b = pos_to_kind[npos]
            if _port_linked(ports_a, ports_b, dir_ab, ck_a, ck_b):
                uf.union(pos, npos)

    groups: dict[_Pos, list[_Pos]] = {}
    for pos in keys:
        root = uf.find(pos)
        groups.setdefault(root, []).append(pos)

    bundle_blocks: list[dict[str, Any]] = []
    sorted_roots = sorted(groups, key=lambda r: min(groups[r], key=_pos_sort_tuple))
    for bundle_id, root in enumerate(sorted_roots, start=1):
        positions = sorted(groups[root], key=_pos_sort_tuple)
        bundle_set = frozenset(positions)
        cells_json: list[dict[str, Any]] = []
        for pos in positions:
            row = pos_to_row[pos]
            edges = _bundle_edges_for_cell(pos, bundle_set)
            links = _bundle_links_for_cell(pos, bundle_set)
            cell_out = dict(row)
            cell_out["bundle_edges"] = edges
            cell_out["bundle_links"] = links
            cells_json.append(cell_out)
        bundle_blocks.append({"bundle_id": bundle_id, "cells_json": cells_json})

    return bundle_blocks
