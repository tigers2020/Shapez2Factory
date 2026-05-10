"""Cost constants for repair / demolition routing (separate from Pass3 mining-priority costs)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    INF_COST,
    MINEABLE_ROUTE_COST,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord


@dataclass(frozen=True)
class RepairCellCost:
    """단일 셀 demolition/repair cost DTO.

        RouteZone 비용과 분리된 repair 탐색 비용이다 (§3.5 route/cost grid).

    상세: documents/Algorithm/mining_solver_cursor_sessions/01_project_overview.md"""

    cost: int


def repair_cell_cost(
    cell: Coord,
    *,
    asteroid_cells: set[Coord],
    buildings: dict[Coord, str],
    transport_cells: frozenset[Coord],
    allow_mineable_route: bool = False,
    mineable_route_step_cost: int | None = None,
) -> RepairCellCost:
    """Single-step demolition/repair cost onto ``cell``."""

    _ = buildings
    _ = transport_cells
    if cell in asteroid_cells:
        if allow_mineable_route:
            step = MINEABLE_ROUTE_COST
            if mineable_route_step_cost is not None:
                step = mineable_route_step_cost
            return RepairCellCost(step)
        return RepairCellCost(INF_COST)
    return RepairCellCost(1)
