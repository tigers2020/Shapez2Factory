"""Throughput-aware placement goal policy (PR-2d; never replay input)."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal
from enum import StrEnum
from typing import Any

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.optimization.selection.equivalence import dedupe_candidates
from django_apps.asteroid_lab.services.committed_throughput_summary import (
    resource_kind_for_transport,
)
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import decimal_str
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_MAX_PLACEMENT_GOAL_COUNT_KEY,
)

MIN_MAX_PLACEMENT_GOAL_COUNT = 1
MAX_MAX_PLACEMENT_GOAL_COUNT = 128
DEFAULT_MAX_PLACEMENT_GOAL_COUNT = 32


class ThroughputShortfallReason(StrEnum):
    SATISFIED = "satisfied"
    ROUTE_FEASIBLE_CANDIDATE_CAP = "route_feasible_candidate_cap"
    NON_OVERLAPPING_ANCHOR_CAP = "non_overlapping_anchor_cap"
    COMMIT_CONFLICT_CAP = "commit_conflict_cap"
    SELECTION_GOAL_CAP = "selection_goal_cap"
    CANDIDATE_POOL_EXHAUSTED = "candidate_pool_exhausted"
    BEST_BUNDLE_ZERO = "best_bundle_zero"
    NO_ACTUAL_OUTPUT = "no_actual_output"


@dataclass(frozen=True, slots=True)
class PlacementGoalPlan:
    placement_goal_count: int
    bundles_needed_for_target: int
    best_bundle_throughput_per_min: Decimal
    route_feasible_candidate_cap: int
    non_overlapping_anchor_cap: int
    configured_max_placement_goal: int
    skeleton_capacity_goals: int

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "placement_goal_count": self.placement_goal_count,
            "bundles_needed_for_target": self.bundles_needed_for_target,
            "best_bundle_throughput_per_min": decimal_str(self.best_bundle_throughput_per_min),
            "route_feasible_candidate_cap": self.route_feasible_candidate_cap,
            "non_overlapping_anchor_cap": self.non_overlapping_anchor_cap,
            "configured_max_placement_goal": self.configured_max_placement_goal,
            "skeleton_capacity_goals": self.skeleton_capacity_goals,
        }


def parse_max_placement_goal_count(config: Mapping[str, Any]) -> int:
    raw = config.get(
        SOLVER_RUN_CONFIG_MAX_PLACEMENT_GOAL_COUNT_KEY,
        DEFAULT_MAX_PLACEMENT_GOAL_COUNT,
    )
    if isinstance(raw, bool) or not isinstance(raw, int):
        msg = "max_placement_goal_count must be an integer"
        raise ValueError(msg)
    if raw < MIN_MAX_PLACEMENT_GOAL_COUNT or raw > MAX_MAX_PLACEMENT_GOAL_COUNT:
        msg = (
            f"max_placement_goal_count must be between "
            f"{MIN_MAX_PLACEMENT_GOAL_COUNT} and {MAX_MAX_PLACEMENT_GOAL_COUNT}"
        )
        raise ValueError(msg)
    return int(raw)


def _best_bundle_throughput(
    *,
    normal_candidates: Sequence[BundleCandidate],
    transport_kind: TransportKind,
) -> Decimal:
    from django_apps.game_data.services.mining_extraction_rules import (
        get_active_rule,
        output_per_min,
    )

    reachable = [candidate for candidate in normal_candidates if candidate.reachable]
    if not reachable:
        return Decimal(0)
    rule = get_active_rule(resource_kind_for_transport(transport_kind))
    return max(output_per_min(rule, candidate.throughput_factor) for candidate in reachable)


def _bundles_needed_for_target(*, target: Decimal, best_bundle: Decimal) -> int:
    if best_bundle <= 0:
        return 0
    return int((target / best_bundle).to_integral_value(rounding=ROUND_CEILING))


def build_placement_goal_plan(
    *,
    normal_candidates: Sequence[BundleCandidate],
    transport_kind: TransportKind,
    target_throughput_per_min: Decimal,
    skeleton_capacity_goals: int,
    configured_max_placement_goal: int,
) -> PlacementGoalPlan:
    reachable = [candidate for candidate in normal_candidates if candidate.reachable]
    route_cap = len(reachable)
    deduped = dedupe_candidates(tuple(reachable))
    anchor_cap = len({candidate.anchor_coord for candidate in deduped})
    best = _best_bundle_throughput(
        normal_candidates=normal_candidates,
        transport_kind=transport_kind,
    )
    bundles_needed = _bundles_needed_for_target(
        target=target_throughput_per_min,
        best_bundle=best,
    )
    floor = max(0, skeleton_capacity_goals)
    raw_goal = max(floor, bundles_needed)
    placement_goal_count = min(
        route_cap,
        anchor_cap,
        configured_max_placement_goal,
        raw_goal,
    )
    return PlacementGoalPlan(
        placement_goal_count=placement_goal_count,
        bundles_needed_for_target=bundles_needed,
        best_bundle_throughput_per_min=best,
        route_feasible_candidate_cap=route_cap,
        non_overlapping_anchor_cap=anchor_cap,
        configured_max_placement_goal=configured_max_placement_goal,
        skeleton_capacity_goals=skeleton_capacity_goals,
    )


def _selection_cap_reason(plan: PlacementGoalPlan) -> ThroughputShortfallReason:
    if plan.placement_goal_count == plan.route_feasible_candidate_cap:
        return ThroughputShortfallReason.ROUTE_FEASIBLE_CANDIDATE_CAP
    if plan.placement_goal_count == plan.non_overlapping_anchor_cap:
        return ThroughputShortfallReason.NON_OVERLAPPING_ANCHOR_CAP
    if plan.placement_goal_count == plan.configured_max_placement_goal:
        return ThroughputShortfallReason.SELECTION_GOAL_CAP
    return ThroughputShortfallReason.SELECTION_GOAL_CAP


def attribute_throughput_shortfall(
    *,
    plan: PlacementGoalPlan,
    selected_count: int,
    committed_count: int,
    conflict_count: int,
    budget_satisfied: bool,
    actual: Decimal,
    target: Decimal,
    normal_count: int,
) -> ThroughputShortfallReason:
    """Post-run read-only attribution when throughput budget is unsatisfied."""

    if budget_satisfied:
        return ThroughputShortfallReason.SATISFIED
    if actual <= 0 and target > 0:
        return ThroughputShortfallReason.NO_ACTUAL_OUTPUT
    if plan.best_bundle_throughput_per_min <= 0:
        return ThroughputShortfallReason.BEST_BUNDLE_ZERO
    if normal_count == 0 or plan.route_feasible_candidate_cap == 0:
        return ThroughputShortfallReason.CANDIDATE_POOL_EXHAUSTED

    if selected_count < plan.bundles_needed_for_target:
        if plan.placement_goal_count < plan.bundles_needed_for_target:
            return _selection_cap_reason(plan)
        if selected_count < plan.placement_goal_count:
            return ThroughputShortfallReason.CANDIDATE_POOL_EXHAUSTED

    if selected_count >= plan.placement_goal_count and (
        committed_count < selected_count or conflict_count > 0
    ):
        return ThroughputShortfallReason.COMMIT_CONFLICT_CAP

    return ThroughputShortfallReason.SELECTION_GOAL_CAP


__all__ = [
    "DEFAULT_MAX_PLACEMENT_GOAL_COUNT",
    "MAX_MAX_PLACEMENT_GOAL_COUNT",
    "MIN_MAX_PLACEMENT_GOAL_COUNT",
    "PlacementGoalPlan",
    "ThroughputShortfallReason",
    "attribute_throughput_shortfall",
    "build_placement_goal_plan",
    "parse_max_placement_goal_count",
]
