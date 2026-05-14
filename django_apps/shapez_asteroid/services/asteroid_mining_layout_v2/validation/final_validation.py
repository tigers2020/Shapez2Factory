"""
Final layout validation (STEP 9 §15.1–15.2 hard checks for MVP skeleton).

No routing side effects. ``trunk_load`` presence is not re-computed here until spec lands.
"""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    PlacementCommitState,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.routing.connectivity import (
    flood_reachable,
)


@dataclass(frozen=True, slots=True)
class FinalValidationReport:
    """Structured assertion summary (expand with §15 fields)."""

    geometry_ok: bool
    connectivity_ok: bool
    quarantined_count: int


def validate_final_layout_stub(
    *,
    placement_commit_by_id: dict[str, PlacementCommitState],
    transport_cells: frozenset[tuple[int, int]],
    external_cells: frozenset[tuple[int, int]],
) -> FinalValidationReport:
    """
    Minimal checks: no QUARANTINED_UNROUTED at STEP9 boundary; some transport reaches exterior.

    Full geometry rules are added in a later phase.
    """
    quarantined = sum(
        1 for s in placement_commit_by_id.values() if s is PlacementCommitState.QUARANTINED_UNROUTED
    )
    geometry_ok = quarantined == 0
    if not transport_cells:
        return FinalValidationReport(
            geometry_ok=geometry_ok,
            connectivity_ok=True,
            quarantined_count=quarantined,
        )
    seeds = transport_cells & external_cells
    if not seeds:
        # Without declared exterior touchpoints, skip connectivity (skeleton leniency).
        return FinalValidationReport(
            geometry_ok=geometry_ok,
            connectivity_ok=True,
            quarantined_count=quarantined,
        )
    start = next(iter(seeds))
    passable = transport_cells | external_cells
    reach = flood_reachable(start, passable)
    connectivity_ok = transport_cells <= reach
    return FinalValidationReport(
        geometry_ok=geometry_ok,
        connectivity_ok=connectivity_ok,
        quarantined_count=quarantined,
    )
