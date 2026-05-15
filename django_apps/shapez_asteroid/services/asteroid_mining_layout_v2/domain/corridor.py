"""Corridor probe / egress opening DTOs (STEP 2 post-gate, STEP 4 recovery)."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BlueprintCell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    RejectedReason,
    RollbackReason,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.routing import (
    RoutePath,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.trace_events import (
    TraceEvent,
)


@dataclass(frozen=True, slots=True)
class CorridorProbeResult:
    connected: bool
    gateway_count: int
    reachable_internal_count: int
    blocked_frontier_cells: frozenset[BlueprintCell]
    cheapest_path: RoutePath | None
    reason: str | None


@dataclass(frozen=True, slots=True)
class CorridorOpeningPlan:
    path: RoutePath
    cells_to_clear: frozenset[BlueprintCell]
    placement_ids_to_rollback: frozenset[str]
    estimated_lost_slots: int
    estimated_cost: tuple[int, ...]
    target_anchor: BlueprintCell
    exterior_goal: BlueprintCell


@dataclass(frozen=True, slots=True)
class CorridorOpeningResult:
    committed: bool
    plan: CorridorOpeningPlan | None
    rollback_reason: RollbackReason | None
    rejected_reason: RejectedReason | None
    trace_rows: tuple[TraceEvent, ...]


__all__ = [
    "CorridorOpeningPlan",
    "CorridorOpeningResult",
    "CorridorProbeResult",
]
