"""P4 reclaim corridor DTOs."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    CORRIDOR_LIFECYCLE_CANDIDATE,
    CORRIDOR_LIFECYCLE_DISCARDED,
    CORRIDOR_LIFECYCLE_HARD,
    CORRIDOR_LIFECYCLE_SOFT,
)
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


@dataclass(frozen=True)
class ProtectedCorridors:
    """Read-only hard/soft pools plus layout-hint *candidate* cells (P3-A read model)."""

    hard: frozenset[Coord]
    soft: frozenset[Coord]
    candidate: frozenset[Coord]
    #: Same diagnostic ``source`` string as :class:`ProtectedCorridorSets`.
    source: str = ""
    #: Routing/shadow probe cells (never promoted to ``soft`` without commit); trace-only.
    probe_candidate_cells: frozenset[Coord] = frozenset()
    #: Probe cells/stubs recorded as discarded after failed probe (not exclusion pools).
    probe_discarded_cells: frozenset[Coord] = frozenset()

    @property
    def existing_layout_hints_cells(self) -> frozenset[Coord]:
        """Alias of ``candidate`` for code paths that used :class:`ProtectedCorridorSets`."""

        return self.candidate


def corridor_lifecycle_state_for_cell(pc: ProtectedCorridors, c: Coord) -> str | None:
    """Document §14 lifecycle label for ``c`` (first matching tier wins)."""

    if c in pc.hard:
        return CORRIDOR_LIFECYCLE_HARD
    if c in pc.soft:
        return CORRIDOR_LIFECYCLE_SOFT
    if c in pc.probe_discarded_cells:
        return CORRIDOR_LIFECYCLE_DISCARDED
    if c in pc.probe_candidate_cells or c in pc.candidate:
        return CORRIDOR_LIFECYCLE_CANDIDATE
    return None


__all__ = [
    "ProtectedCorridorSets",
    "ProtectedCorridors",
    "corridor_lifecycle_state_for_cell",
]
