"""Placement coverage goal policy (PR-2d + Task 4 recovery).

``throughput_target_percent`` run-config key is a **legacy alias** for
``placement_target_percent`` (placement coverage %, not throughput /min alone).

``legacy_configured_max_placement_goal`` records the resolved run-config max
(field cells × ``placement_target_percent`` floor when unset). It must never
clamp ``placement_goal_count``.
"""

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
    best_bundle_output_per_min_from_factors,
)
from django_apps.asteroid_lab.services.reconstruction_capacity_summary import decimal_str
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_MAX_PLACEMENT_GOAL_COUNT_KEY,
)

MIN_MAX_PLACEMENT_GOAL_COUNT = 1


class ThroughputShortfallReason(StrEnum):
    SATISFIED = "satisfied"
    ROUTE_FEASIBLE_SHORTFALL = "route_feasible_shortfall"
    ANCHOR_CAPACITY_SHORTFALL = "anchor_capacity_shortfall"
    COMMIT_SHORTFALL = "commit_shortfall"
    PLACEMENT_GOAL_SHORTFALL = "placement_goal_shortfall"
    CANDIDATE_GENERATION_SHORTFALL = "candidate_generation_shortfall"
    BEST_BUNDLE_ZERO = "best_bundle_zero"
    NO_ACTUAL_OUTPUT = "no_actual_output"


@dataclass(frozen=True, slots=True)
class PlacementGoalPlan:
    placement_goal_count: int
    asteroid_field_cell_count: int
    placement_target_percent: int
    bundles_needed_for_target: int
    best_bundle_throughput_per_min: Decimal
    route_feasible_candidate_cap: int
    non_overlapping_anchor_cap: int
    legacy_configured_max_placement_goal: int
    skeleton_capacity_goals: int

    @property
    def mineable_platform_cell_count(self) -> int:
        """Backward-compatible alias for ``asteroid_field_cell_count``."""

        return self.asteroid_field_cell_count

    @property
    def configured_max_placement_goal(self) -> int:
        """Resolved run-config max (>= placement coverage floor; not a hard 32 cap)."""

        return self.legacy_configured_max_placement_goal

    def to_summary_dict(self) -> dict[str, Any]:
        return {
            "placement_goal_count": self.placement_goal_count,
            "asteroid_field_cell_count": self.asteroid_field_cell_count,
            "mineable_platform_cell_count": self.asteroid_field_cell_count,
            "placement_target_percent": self.placement_target_percent,
            "bundles_needed_for_target": self.bundles_needed_for_target,
            "best_bundle_throughput_per_min": decimal_str(self.best_bundle_throughput_per_min),
            "route_feasible_candidate_cap": self.route_feasible_candidate_cap,
            "non_overlapping_anchor_cap": self.non_overlapping_anchor_cap,
            "legacy_configured_max_placement_goal": self.legacy_configured_max_placement_goal,
            "configured_max_placement_goal": self.legacy_configured_max_placement_goal,
            "skeleton_capacity_goals": self.skeleton_capacity_goals,
        }


def compute_placement_goal_count(
    *,
    asteroid_field_cell_count: int,
    placement_target_percent: int,
) -> int:
    """Product placement target from reconstruction-complete asteroid field coverage."""

    if asteroid_field_cell_count <= 0 or placement_target_percent <= 0:
        return 0
    product = Decimal(asteroid_field_cell_count) * Decimal(placement_target_percent) / Decimal(100)
    return int(product.to_integral_value(rounding=ROUND_CEILING))


def parse_max_placement_goal_count(config: Mapping[str, Any]) -> int:
    """Parse explicit run-config override when the key is present.

    No default of 32. Full floor vs field cells is enforced by
    ``resolve_max_placement_goal_count`` at solver runtime.
    """
    key = SOLVER_RUN_CONFIG_MAX_PLACEMENT_GOAL_COUNT_KEY
    if key not in config:
        msg = "max_placement_goal_count is required when validating an explicit override"
        raise ValueError(msg)
    raw = config[key]
    if isinstance(raw, bool) or not isinstance(raw, int):
        msg = "max_placement_goal_count must be an integer"
        raise ValueError(msg)
    if raw < MIN_MAX_PLACEMENT_GOAL_COUNT:
        msg = f"max_placement_goal_count must be at least {MIN_MAX_PLACEMENT_GOAL_COUNT}"
        raise ValueError(msg)
    return int(raw)


def resolve_max_placement_goal_count(
    config: Mapping[str, Any],
    *,
    asteroid_field_cell_count: int,
    placement_target_percent: int,
) -> int:
    """Product max placement goal: default = ``placement_target_percent`` of field cells.

    No arbitrary 32 default. Explicit override must be >= that floor and <= field cells.
    """
    floor = compute_placement_goal_count(
        asteroid_field_cell_count=asteroid_field_cell_count,
        placement_target_percent=placement_target_percent,
    )
    key = SOLVER_RUN_CONFIG_MAX_PLACEMENT_GOAL_COUNT_KEY
    if key not in config:
        return floor
    raw = config[key]
    if isinstance(raw, bool) or not isinstance(raw, int):
        msg = "max_placement_goal_count must be an integer"
        raise ValueError(msg)
    if raw < floor:
        msg = (
            f"max_placement_goal_count must be at least {floor} "
            f"({placement_target_percent}% of {asteroid_field_cell_count} field cells)"
        )
        raise ValueError(msg)
    if asteroid_field_cell_count > 0 and raw > asteroid_field_cell_count:
        msg = (
            f"max_placement_goal_count must not exceed asteroid field cell count "
            f"({asteroid_field_cell_count})"
        )
        raise ValueError(msg)
    if raw < MIN_MAX_PLACEMENT_GOAL_COUNT:
        msg = f"max_placement_goal_count must be at least {MIN_MAX_PLACEMENT_GOAL_COUNT}"
        raise ValueError(msg)
    return int(raw)


def _best_bundle_throughput(
    *,
    normal_candidates: Sequence[BundleCandidate],
    transport_kind: TransportKind,
) -> Decimal:
    factors = tuple(
        int(candidate.throughput_factor) for candidate in normal_candidates if candidate.reachable
    )
    return best_bundle_output_per_min_from_factors(
        throughput_factors=factors,
        transport_kind=transport_kind,
    )


def _bundles_needed_for_target(*, target: Decimal, best_bundle: Decimal) -> int:
    if best_bundle <= 0:
        return 0
    return int((target / best_bundle).to_integral_value(rounding=ROUND_CEILING))


def build_placement_goal_plan(
    *,
    normal_candidates: Sequence[BundleCandidate],
    transport_kind: TransportKind,
    asteroid_field_cell_count: int,
    placement_target_percent: int,
    target_throughput_per_min: Decimal,
    skeleton_capacity_goals: int,
    legacy_configured_max_placement_goal: int,
) -> PlacementGoalPlan:
    """Build product placement goal + diagnostic caps (caps do not lower goal)."""

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
    placement_goal_count = compute_placement_goal_count(
        asteroid_field_cell_count=asteroid_field_cell_count,
        placement_target_percent=placement_target_percent,
    )
    return PlacementGoalPlan(
        placement_goal_count=placement_goal_count,
        asteroid_field_cell_count=asteroid_field_cell_count,
        placement_target_percent=placement_target_percent,
        bundles_needed_for_target=bundles_needed,
        best_bundle_throughput_per_min=best,
        route_feasible_candidate_cap=route_cap,
        non_overlapping_anchor_cap=anchor_cap,
        legacy_configured_max_placement_goal=legacy_configured_max_placement_goal,
        skeleton_capacity_goals=skeleton_capacity_goals,
    )


def _placement_coverage_shortfall_reason(
    plan: PlacementGoalPlan,
    *,
    selected_count: int,
    normal_count: int,
) -> ThroughputShortfallReason:
    if selected_count < plan.placement_goal_count:
        if (
            plan.route_feasible_candidate_cap < plan.placement_goal_count
            and selected_count <= plan.route_feasible_candidate_cap
        ):
            return ThroughputShortfallReason.ROUTE_FEASIBLE_SHORTFALL
        if (
            plan.non_overlapping_anchor_cap < plan.placement_goal_count
            and selected_count <= plan.non_overlapping_anchor_cap
        ):
            return ThroughputShortfallReason.ANCHOR_CAPACITY_SHORTFALL
        if normal_count < plan.placement_goal_count:
            return ThroughputShortfallReason.CANDIDATE_GENERATION_SHORTFALL
        return ThroughputShortfallReason.CANDIDATE_GENERATION_SHORTFALL
    return ThroughputShortfallReason.PLACEMENT_GOAL_SHORTFALL


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
    if normal_count == 0:
        return ThroughputShortfallReason.CANDIDATE_GENERATION_SHORTFALL

    if selected_count < plan.placement_goal_count:
        return _placement_coverage_shortfall_reason(
            plan,
            selected_count=selected_count,
            normal_count=normal_count,
        )

    if selected_count < plan.bundles_needed_for_target:
        if plan.bundles_needed_for_target > plan.placement_goal_count:
            return ThroughputShortfallReason.PLACEMENT_GOAL_SHORTFALL

    if selected_count >= plan.placement_goal_count and (
        committed_count < selected_count or conflict_count > 0
    ):
        return ThroughputShortfallReason.COMMIT_SHORTFALL

    return ThroughputShortfallReason.PLACEMENT_GOAL_SHORTFALL


__all__ = [
    "MIN_MAX_PLACEMENT_GOAL_COUNT",
    "PlacementGoalPlan",
    "ThroughputShortfallReason",
    "attribute_throughput_shortfall",
    "build_placement_goal_plan",
    "compute_placement_goal_count",
    "parse_max_placement_goal_count",
    "resolve_max_placement_goal_count",
]
