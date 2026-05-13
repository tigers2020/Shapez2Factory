"""Typed wire shapes for STEP4 routing-failure telemetry."""

from __future__ import annotations

from typing import Any, TypedDict

from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.existing_layout_types import (
    CoordWire,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.recovery_semantics import (
    RecoveryTrigger,
)


class Step4FailureClassificationWire(TypedDict, total=False):
    """Nested classification object on routing-failure detail."""

    category: str
    confidence: str
    evidence: dict[str, Any]


class Step4RoutingFailureDetailWire(TypedDict, total=False):
    """Stable-key STEP4 routing failure detail wire object."""

    extractor_id: str | None
    placement_id: str | None
    transport_kind: str | None
    stub_cell: CoordWire
    placement_commit_state: str | None
    blocked_reason: str | None
    blocked_reason_near_stub: str | None
    nearest_blocked_cell: CoordWire | None
    nearest_blocked_zone: str | None
    existing_trunk_present: bool
    trunk_seed_candidate_count: int
    route_goal_set_size: int
    external_goal_count: int
    active_goal_cells_count: int
    margin_goals_in_active_goal_cells_count: int
    reachable_goal_count: int
    reachable_existing_trunk_count: int
    reachable_exterior_margin_count: int
    candidate_expanded_nodes: int | None
    search_mode: str | None
    goal_ordering_mode: str
    fallback_reason: str | None
    search_budget_exhausted: bool
    replacement_search_exhausted: bool | None
    quarantined: bool
    rolled_back: bool
    step4_failure_category: str
    step4_failure_classification: Step4FailureClassificationWire | dict[str, Any]
    goal_set_size: int
    dijkstra_reachable_goal_count: int
    dijkstra_reachable_trunk_goal_count: int
    dijkstra_reachable_margin_goal_count: int
    placement_commit_state_at_route_attempt: str | None


class Step4SearchStatsWire(TypedDict, total=False):
    """Known search-stat keys copied into STEP4 diagnostics."""

    search_mode: str
    expanded_nodes: int
    candidate_expanded_nodes: int
    nearest_goal_distance_estimate: int | None
    first_goal_candidate: CoordWire | None
    goal_count_by_distance_bucket: dict[str, int]


class Step4RoutingFailureRowWire(TypedDict, total=False):
    """One public ``Step4RoutingResult.routing_failures`` row."""

    placement_id: str
    placement_pass: str
    extractor_cell: CoordWire
    extension_cells: list[CoordWire]
    stub_cell: CoordWire
    transport_kind: str
    state: str
    route_id: str | None
    rollback_reason: str | None
    reason: str
    extractor_id: str
    attempt_count: int
    final_state: str
    last_error: str
    recovery_trigger: RecoveryTrigger | str


def step4_routing_failure_row_to_public_dict(
    row: Step4RoutingFailureRowWire,
) -> dict[str, Any]:
    """Boundary adapter preserving the legacy public ``dict`` contract."""

    return dict(row)


__all__ = [
    "Step4FailureClassificationWire",
    "Step4RoutingFailureDetailWire",
    "Step4RoutingFailureRowWire",
    "Step4SearchStatsWire",
    "step4_routing_failure_row_to_public_dict",
]
