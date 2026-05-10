"""P4 reclaim corridor DTOs."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord


@dataclass(frozen=True)
class ProtectedCorridorSets:
    """Hard/soft protected corridor cells for Reclaim exclusion (single source selection)."""

    hard: frozenset[Coord]
    soft: frozenset[Coord]
    source: str
    #: Union of ``trunk_seed_cell_union`` and ``cleanup_candidate_cell_union`` from
    #: ``existing_layout_analysis["solver_hints"]`` when those keys contributed cells
    #: (diagnostics; merged into ``soft`` only, never into ``hard``).
    existing_layout_hints_cells: frozenset[Coord] = frozenset()
