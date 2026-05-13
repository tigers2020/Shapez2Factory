"""Typed wire shapes for Pass12 route-probe diagnostics."""

from __future__ import annotations

from typing import Any, Literal, TypedDict


class Pass2GoalTraceWire(TypedDict, total=False):
    """Trace from ``build_pass2_step4_aligned_routing_goals``."""

    goal_set_kind: Literal["first_route", "subsequent_route"]
    exterior_margin_cell_count: int
    trunk_seed_candidate_count: int
    same_kind_trunk_seed_count: int
    existing_trunk_goal_count: int
    raw_goal_count: int
    trunk_reaching_probe_count: int
    final_goal_count: int
    transport_cells_before_count: int
    external_reachable_transport_before_count: int
    external_margin_bbox_source: str
    universe_cell_count: int
    mineable_cell_count: int
    asteroid_cell_count: int
    mineable_asteroid_bbox: dict[str, int] | None
    rejected_reason: str | None
    pass2_prior_transport_all_orphan: bool
    pass2_empty_goal_nonempty_universe: bool


class Pass2RouteProbeStatsWire(TypedDict, total=False):
    """Counters merged into Pass12 stats for the Pass2 route-probe gate."""

    pass2_probe_goal_set_kind_counts: dict[str, int]
    pass2_probe_goal_set_kind: str
    pass2_probe_goal_count: int
    pass2_probe_goal_count_max: int
    pass2_probe_goal_count_sum: int
    pass2_probe_last_final_goal_count: int | None
    pass2_probe_last_goal_trace: Pass2GoalTraceWire | dict[str, Any] | None
    pass2_probe_empty_goal_set_count: int
    pass2_probe_goal_eval_count: int
    pass2_route_uncertain_count: int
    pass2_provisional_unrouted_count: int
    pass2_hard_geometry_reject_count: int
    pass2_reject_step4_stub_isolated_count: int
    pass2_reject_step4_unreachable_stub_count: int
    pass2_reject_step4_unreachable_fluid_stub_count: int
    pass2_reject_step4_unreachable_component_count: int
    reachable_component_sample_by_size: dict[str, int]


__all__ = [
    "Pass2GoalTraceWire",
    "Pass2RouteProbeStatsWire",
]
