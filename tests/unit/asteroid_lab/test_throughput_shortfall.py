"""PR-2d throughput shortfall attribution tests."""

from __future__ import annotations

from decimal import Decimal

from django_apps.asteroid_lab.services.placement_goal import (
    PlacementGoalPlan,
    ThroughputShortfallReason,
    attribute_throughput_shortfall,
)


def _plan(
    *,
    placement_goal_count: int = 13,
    bundles_needed_for_target: int = 13,
    route_feasible_candidate_cap: int = 127,
    non_overlapping_anchor_cap: int = 42,
) -> PlacementGoalPlan:
    return PlacementGoalPlan(
        placement_goal_count=placement_goal_count,
        bundles_needed_for_target=bundles_needed_for_target,
        best_bundle_throughput_per_min=Decimal("120"),
        route_feasible_candidate_cap=route_feasible_candidate_cap,
        non_overlapping_anchor_cap=non_overlapping_anchor_cap,
        configured_max_placement_goal=32,
        skeleton_capacity_goals=1,
    )


def test_satisfied_when_budget_ok() -> None:
    reason = attribute_throughput_shortfall(
        plan=_plan(),
        selected_count=13,
        committed_count=13,
        conflict_count=0,
        budget_satisfied=True,
        actual=Decimal("1560"),
        target=Decimal("1536"),
        normal_count=127,
    )
    assert reason == ThroughputShortfallReason.SATISFIED


def test_cap_reason_before_conflict() -> None:
    reason = attribute_throughput_shortfall(
        plan=_plan(placement_goal_count=3, bundles_needed_for_target=13),
        selected_count=3,
        committed_count=3,
        conflict_count=0,
        budget_satisfied=False,
        actual=Decimal("360"),
        target=Decimal("1536"),
        normal_count=127,
    )
    assert reason == ThroughputShortfallReason.SELECTION_GOAL_CAP


def test_route_feasible_cap_when_binding() -> None:
    reason = attribute_throughput_shortfall(
        plan=_plan(
            placement_goal_count=5,
            bundles_needed_for_target=13,
            route_feasible_candidate_cap=5,
            non_overlapping_anchor_cap=40,
        ),
        selected_count=5,
        committed_count=5,
        conflict_count=0,
        budget_satisfied=False,
        actual=Decimal("600"),
        target=Decimal("1536"),
        normal_count=5,
    )
    assert reason == ThroughputShortfallReason.ROUTE_FEASIBLE_CANDIDATE_CAP


def test_conflict_only_when_selection_reached_goal() -> None:
    reason = attribute_throughput_shortfall(
        plan=_plan(),
        selected_count=13,
        committed_count=8,
        conflict_count=5,
        budget_satisfied=False,
        actual=Decimal("960"),
        target=Decimal("1536"),
        normal_count=127,
    )
    assert reason == ThroughputShortfallReason.COMMIT_CONFLICT_CAP
