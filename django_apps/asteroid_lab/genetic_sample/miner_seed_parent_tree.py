"""Equipment parent-tree helpers for miner seed catalog (island-local)."""

from __future__ import annotations

from collections import deque
from typing import Any

from django_apps.asteroid_lab.snapshots.copy_json_coords import entry_island_raw_coord

_MINER_T = frozenset({"Layout_ShapeMiner", "Layout_FluidMiner"})
_EXT_T = frozenset({"Layout_ShapeMinerExtension", "Layout_FluidMinerExtension"})
_BELT_T = frozenset({"SpaceBelt_Forward", "SpacePipe_Forward"})
ISLAND_DIRS: tuple[tuple[str, int, int], ...] = (
    ("n", 0, -1),
    ("e", 1, 0),
    ("s", 0, 1),
    ("w", -1, 0),
)

EquipmentNodes = dict[tuple[int, int], dict[str, Any]]


def entries(root: dict[str, Any]) -> list[dict[str, Any]]:
    bp = root.get("BP")
    if not isinstance(bp, dict):
        return []
    raw = bp.get("Entries")
    return [e for e in raw if isinstance(e, dict)] if isinstance(raw, list) else []


def equipment_nodes(root: dict[str, Any]) -> tuple[tuple[int, int], EquipmentNodes]:
    """Return (miner_xy, nodes) for miner + extensions; belts excluded."""

    miner_xy: tuple[int, int] | None = None
    nodes: EquipmentNodes = {}
    for entry in entries(root):
        tile = str(entry.get("T", ""))
        if tile in _BELT_T:
            continue
        if tile not in _MINER_T and tile not in _EXT_T:
            continue
        coord = entry_island_raw_coord(entry)
        xy = (coord.x, coord.y)
        if tile in _MINER_T:
            if miner_xy is not None:
                msg = "multiple miner entries"
                raise ValueError(msg)
            miner_xy = xy
        nodes[xy] = entry
    if miner_xy is None:
        msg = "miner entry required"
        raise ValueError(msg)
    return miner_xy, nodes


def parent_edges_bfs(
    miner_xy: tuple[int, int],
    nodes: EquipmentNodes,
) -> list[tuple[tuple[int, int], tuple[int, int]]]:
    """Directed child→parent edges on 4-connected equipment tree."""

    visited: set[tuple[int, int]] = {miner_xy}
    parent_of: dict[tuple[int, int], tuple[int, int]] = {}
    queue: deque[tuple[int, int]] = deque([miner_xy])
    while queue:
        current = queue.popleft()
        cx, cy = current
        for _d, dx, dy in ISLAND_DIRS:
            nb = (cx + dx, cy + dy)
            if nb not in nodes or nb in visited:
                continue
            visited.add(nb)
            parent_of[nb] = current
            queue.append(nb)
    ext_keys = [xy for xy in nodes if xy != miner_xy]
    if len(visited) != len(nodes):
        msg = "extension cells must be 4-connected to miner"
        raise ValueError(msg)
    child_edges = [(child, parent_of[child]) for child in ext_keys]
    if len(child_edges) != len(ext_keys):
        msg = "extension parent tree incomplete"
        raise ValueError(msg)
    return child_edges


__all__ = [
    "ISLAND_DIRS",
    "EquipmentNodes",
    "entries",
    "equipment_nodes",
    "parent_edges_bfs",
]
