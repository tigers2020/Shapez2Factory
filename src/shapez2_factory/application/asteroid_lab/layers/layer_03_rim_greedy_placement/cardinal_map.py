"""Cardinal step deltas on the lab / island raw grid (aligned with layer_02 exterior slots).

Map-facing convention (``equipment_bundles``, Lab JS): north decreases ``y``, south increases ``y``.
"""

from __future__ import annotations

CARDINAL_ORDER: tuple[str, ...] = ("N", "E", "S", "W")

# Uppercase labels match rim anchor ``void_dirs`` and committed ``output_dir`` strings.
CARDINAL_DIR_DELTA: dict[str, tuple[int, int]] = {
    "N": (0, -1),
    "E": (1, 0),
    "S": (0, 1),
    "W": (-1, 0),
}

# Port / bundle wire uses lowercase map-facing dirs (``equipment_bundles``).
_MAP_FACING_DIR_TO_PORT: dict[str, str] = {
    "N": "n",
    "E": "e",
    "S": "s",
    "W": "w",
}


def direction_child_to_parent(child: tuple[int, int], parent: tuple[int, int]) -> str | None:
    """Direction from ``child`` toward ``parent`` on the island/lab grid (``x == 0`` allowed)."""

    dx = parent[0] - child[0]
    dy = parent[1] - child[1]
    for name, (ddx, ddy) in CARDINAL_DIR_DELTA.items():
        if dx == ddx and dy == ddy:
            return _MAP_FACING_DIR_TO_PORT[name]
    return None


__all__ = [
    "CARDINAL_DIR_DELTA",
    "CARDINAL_ORDER",
    "direction_child_to_parent",
]
