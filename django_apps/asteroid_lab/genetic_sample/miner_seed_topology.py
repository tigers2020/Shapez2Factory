"""Island-local topology signatures for miner seed GeneticSample rows."""

from __future__ import annotations

import hashlib
import json
from typing import Any

from django_apps.asteroid_lab.snapshots.copy_json_coords import (
    entry_raw_r,
    entry_raw_x,
    entry_raw_y,
)

_MINER_T = frozenset({"Layout_ShapeMiner", "Layout_FluidMiner"})
_EXT_T = frozenset({"Layout_ShapeMinerExtension", "Layout_FluidMinerExtension"})
_BELT_T = frozenset({"SpaceBelt_Forward", "SpacePipe_Forward"})


def throughput_factor_for_extension_count(extension_count: int) -> int:
    if extension_count < 0 or extension_count > 3:
        msg = "extension_count must be 0..3"
        raise ValueError(msg)
    return 4 * (1 + extension_count)


def _entries(root: dict[str, Any]) -> list[dict[str, Any]]:
    bp = root.get("BP")
    if not isinstance(bp, dict):
        return []
    raw = bp.get("Entries")
    return list(raw) if isinstance(raw, list) else []


def count_extensions(root: dict[str, Any]) -> int:
    return sum(1 for e in _entries(root) if e.get("T") in _EXT_T)


def topology_signature_from_decoded_root(root: dict[str, Any]) -> str:
    """Stable hash: island-local cells relative to miner; roles not fluid-specific types."""

    entries = _entries(root)
    miner_xy: tuple[int, int] | None = None
    cells: list[tuple[int, int, str, int]] = []
    for e in entries:
        t = str(e.get("T", ""))
        x, y, r = entry_raw_x(e), entry_raw_y(e), entry_raw_r(e)
        if t in _MINER_T:
            role = "miner"
            miner_xy = (x, y)
        elif t in _EXT_T:
            role = "ext"
        elif t in _BELT_T:
            role = "belt"
        else:
            continue
        cells.append((x, y, role, r))
    if miner_xy is None:
        msg = "miner entry required for topology signature"
        raise ValueError(msg)
    mx, my = miner_xy
    rel = sorted(
        [(x - mx, y - my, role, r) for x, y, role, r in cells],
        key=lambda c: (c[0], c[1], c[2]),
    )
    payload = {"cells": rel}
    blob = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


__all__ = [
    "count_extensions",
    "throughput_factor_for_extension_count",
    "topology_signature_from_decoded_root",
]
