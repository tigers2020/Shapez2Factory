"""Canonical internal-transport counts (Pass3, baselines, reclaim net metrics).

Internal transport tiles are same-kind belt/pipe cells whose coordinates are **not**
``is_external`` (world / blueprint exit predicate). This replaces the legacy
``transport ∩ mineable_and_asteroid_coords(final)`` intersection, which was often empty
because belt rows are not ``inferred``/``occupied`` rows in ``final_mining_map``.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord


def internal_transport_cell_frozenset(
    transport_cell_coords: Iterable[Coord],
    *,
    is_external: Callable[[Coord], bool],
) -> frozenset[Coord]:
    """Belt/pipe coords treated as *internal* for optimization metrics (not ``is_external``)."""

    return frozenset(c for c in transport_cell_coords if not is_external(c))


def count_internal_transport_cells(
    transport_cell_coords: Iterable[Coord],
    *,
    is_external: Callable[[Coord], bool],
) -> int:
    return len(internal_transport_cell_frozenset(transport_cell_coords, is_external=is_external))


def count_internal_transport_tiles_for_role(
    cells: Mapping[Coord, Mapping[str, Any]],
    *,
    want_role: str,
    is_external: Callable[[Coord], bool],
) -> int:
    """Count cells with ``role == want_role`` that are internal per ``is_external``."""

    coords = (c for c, row in cells.items() if row.get("role") == want_role)
    return count_internal_transport_cells(coords, is_external=is_external)
