"""Miner seed catalog equivalence (D₄ parent-tree) and strict layout validation."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from django_apps.asteroid_lab.genetic_sample.miner_seed_parent_tree import (
    ISLAND_DIRS,
    EquipmentNodes,
    entries,
    equipment_nodes,
    parent_edges_bfs,
)
from django_apps.asteroid_lab.snapshots.cell_classifier import classify_blueprint_entry
from django_apps.asteroid_lab.snapshots.copy_json_coords import (
    entry_island_raw_coord,
    entry_raw_r,
    entry_raw_x,
    entry_raw_y,
)
from django_apps.asteroid_lab.snapshots.equipment_bundles import ports_compatible

_BELT_T = frozenset({"SpaceBelt_Forward", "SpacePipe_Forward"})


class MinerSeedLayoutValidationError(ValueError):
    """Strict ingest rejection for miner seed paste layout."""


def _layout_error(exc: ValueError) -> MinerSeedLayoutValidationError:
    return MinerSeedLayoutValidationError(str(exc))


def _island_direction_from_a_to_b(ax: int, ay: int, bx: int, by: int) -> str | None:
    if bx == ax + 1 and by == ay:
        return "e"
    if bx == ax - 1 and by == ay:
        return "w"
    if bx == ax and by == ay + 1:
        return "s"
    if bx == ax and by == ay - 1:
        return "n"
    return None


def _equipment_nodes(root: dict[str, Any]) -> tuple[tuple[int, int], EquipmentNodes]:
    try:
        return equipment_nodes(root)
    except ValueError as exc:
        raise _layout_error(exc) from exc


def _parent_edges_bfs(
    miner_xy: tuple[int, int],
    nodes: EquipmentNodes,
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    try:
        return parent_edges_bfs(miner_xy, nodes)
    except ValueError as exc:
        raise _layout_error(exc) from exc


def _transform_xy(
    x: int,
    y: int,
    *,
    origin: tuple[int, int],
    rot: int,
    flip: int,
) -> tuple[int, int]:
    mx, my = origin
    xr, yr = x - mx, y - my
    for _ in range(rot):
        xr, yr = yr, -xr
    return flip * xr, yr


def _d4_canonical_edges(
    miner_xy: tuple[int, int],
    edges: list[tuple[tuple[int, int], tuple[int, int]]],
) -> tuple[list[list[int]], ...]:
    variants: list[list[list[int]]] = []
    for rot in range(4):
        for flip in (1, -1):
            transformed: list[list[int]] = []
            for (cx, cy), (px, py) in edges:
                tcx, tcy = _transform_xy(cx, cy, origin=miner_xy, rot=rot, flip=flip)
                tpx, tpy = _transform_xy(px, py, origin=miner_xy, rot=rot, flip=flip)
                transformed.append([tcx, tcy, tpx, tpy])
            variants.append(sorted(transformed))
    return tuple(variants)


def equivalence_signature_from_decoded_root(root: dict[str, Any]) -> str:
    """Catalog dedupe key: extension_count + D₄-canonical directed parent edges."""

    from django_apps.asteroid_lab.genetic_sample.miner_seed_topology import count_extensions

    miner_xy, nodes = _equipment_nodes(root)
    edge_list = _parent_edges_bfs(miner_xy, nodes)
    variants = _d4_canonical_edges(miner_xy, edge_list)
    best = min(variants)
    payload = {
        "extension_count": count_extensions(root),
        "edges": best,
    }
    blob = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _assert_extension_faces_parent(entry: dict[str, Any], parent_entry: dict[str, Any]) -> None:
    child_xy = entry_island_raw_coord(entry)
    parent_xy = entry_island_raw_coord(parent_entry)
    child_kind, _ = classify_blueprint_entry(str(entry.get("T")))
    parent_kind, _ = classify_blueprint_entry(str(parent_entry.get("T")))
    direction = _island_direction_from_a_to_b(child_xy.x, child_xy.y, parent_xy.x, parent_xy.y)
    if direction is None:
        msg = "extension and parent are not island 4-neighbors"
        raise MinerSeedLayoutValidationError(msg)
    parent_r = entry_raw_r(parent_entry) if parent_kind.endswith("_extension") else 0
    actual_r = entry_raw_r(entry)
    if not ports_compatible(child_kind, actual_r, parent_kind, parent_r, direction):
        msg = f"extension R {actual_r!r} does not face parent on {direction!r}"
        raise MinerSeedLayoutValidationError(msg)


def assert_miner_seed_layout_strict(root: dict[str, Any]) -> None:
    """Validate §5 strict rules; raise MinerSeedLayoutValidationError on failure."""

    miner_xy, nodes = _equipment_nodes(root)
    belts = [e for e in entries(root) if str(e.get("T", "")) in _BELT_T]
    if len(belts) != 1:
        msg = f"expected exactly one SpaceBelt_Forward, got {len(belts)}"
        raise MinerSeedLayoutValidationError(msg)
    belt = belts[0]
    if str(belt.get("T")) != "SpaceBelt_Forward":
        msg = "shape seeds must use SpaceBelt_Forward"
        raise MinerSeedLayoutValidationError(msg)

    miner_entry = nodes[miner_xy]
    if entry_raw_r(miner_entry) != 0:
        msg = "miner R must be 0 (East)"
        raise MinerSeedLayoutValidationError(msg)

    forward_xy = (miner_xy[0] + 1, miner_xy[1])
    belt_xy = (entry_raw_x(belt), entry_raw_y(belt))
    if belt_xy != forward_xy:
        msg = "belt must be on miner forward island cell (east)"
        raise MinerSeedLayoutValidationError(msg)

    if forward_xy in nodes and forward_xy != miner_xy:
        msg = "extension must not occupy miner forward / output-axis cell"
        raise MinerSeedLayoutValidationError(msg)

    for child_xy, child_entry in nodes.items():
        if child_xy == miner_xy:
            continue
        cx, cy = child_xy
        facing: list[tuple[int, int]] = []
        for _d, dx, dy in ISLAND_DIRS:
            nb = (cx + dx, cy + dy)
            if nb not in nodes:
                continue
            try:
                _assert_extension_faces_parent(child_entry, nodes[nb])
            except MinerSeedLayoutValidationError:
                continue
            facing.append(nb)
        if not facing:
            msg = f"extension at {child_xy} has no port-facing equipment neighbor"
            raise MinerSeedLayoutValidationError(msg)

    edge_list = _parent_edges_bfs(miner_xy, nodes)
    for _child_xy, parent_xy in edge_list:
        if str(nodes[parent_xy].get("T", "")) in _BELT_T:
            msg = "extension parent cannot be belt"
            raise MinerSeedLayoutValidationError(msg)

    parent_map = {c: p for c, p in edge_list}
    for start in parent_map:
        seen: set[tuple[int, int]] = set()
        cur: tuple[int, int] | None = start
        while cur is not None and cur != miner_xy:
            if cur in seen:
                msg = "extension parent graph has a cycle"
                raise MinerSeedLayoutValidationError(msg)
            seen.add(cur)
            cur = parent_map.get(cur)


__all__ = [
    "MinerSeedLayoutValidationError",
    "assert_miner_seed_layout_strict",
    "equivalence_signature_from_decoded_root",
]
