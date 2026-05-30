"""Shim — relocated to ``shapez2_factory.domain.asteroid_lab.transport_components`` (PR-CLI-2c)."""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.transport_components import (
    cell_position_key,
    is_transport_tile,
    iter_four_neighbors,
    sort_key_xy_layer,
)

__all__ = [
    "cell_position_key",
    "is_transport_tile",
    "iter_four_neighbors",
    "sort_key_xy_layer",
]
