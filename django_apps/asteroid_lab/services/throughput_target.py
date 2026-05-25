"""Throughput target percent and budget evaluation (PR-2c; never replay input)."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import ROUND_CEILING, Decimal
from typing import Any

from django_apps.asteroid_lab.services.reconstruction_capacity_summary import decimal_str
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_THROUGHPUT_TARGET_PERCENT_KEY,
)

MIN_THROUGHPUT_TARGET_PERCENT = 10
MAX_THROUGHPUT_TARGET_PERCENT = 80
DEFAULT_THROUGHPUT_TARGET_PERCENT = 80
THROUGHPUT_TARGET_SHORTFALL_ISSUE_CODE = "throughput_target_shortfall"


@dataclass(frozen=True, slots=True)
class ThroughputBudgetEvaluation:
    satisfied: bool
    shortfall: Decimal


def parse_throughput_target_percent(config: Mapping[str, Any]) -> int:
    raw = config.get(
        SOLVER_RUN_CONFIG_THROUGHPUT_TARGET_PERCENT_KEY,
        DEFAULT_THROUGHPUT_TARGET_PERCENT,
    )
    if isinstance(raw, bool) or not isinstance(raw, int):
        msg = "throughput_target_percent must be an integer"
        raise ValueError(msg)
    if raw < MIN_THROUGHPUT_TARGET_PERCENT or raw > MAX_THROUGHPUT_TARGET_PERCENT:
        msg = (
            f"throughput_target_percent must be between "
            f"{MIN_THROUGHPUT_TARGET_PERCENT} and {MAX_THROUGHPUT_TARGET_PERCENT}"
        )
        raise ValueError(msg)
    return int(raw)


def primary_reconstruction_max_per_min(envelope: Mapping[str, Any]) -> Decimal:
    primary = str(envelope.get("primary_resource_kind", "shape"))
    by = dict(envelope.get("by_resource") or {})
    row = dict(by.get(primary) or {})
    raw = row.get("max_throughput_per_min", "0")
    return Decimal(str(raw))


def compute_target_throughput_per_min(*, reconstruction_max: Decimal, percent: int) -> Decimal:
    product = reconstruction_max * Decimal(percent) / Decimal(100)
    return product.to_integral_value(rounding=ROUND_CEILING)


def evaluate_throughput_budget(*, actual: Decimal, target: Decimal) -> ThroughputBudgetEvaluation:
    if actual >= target:
        return ThroughputBudgetEvaluation(satisfied=True, shortfall=Decimal(0))
    return ThroughputBudgetEvaluation(satisfied=False, shortfall=target - actual)


def throughput_utilization_ratios(
    *,
    actual: Decimal,
    reconstruction_max: Decimal,
    percent: int,
) -> tuple[Decimal, Decimal]:
    target_u = (Decimal(percent) / Decimal(100)).quantize(Decimal("0.0001"))
    if reconstruction_max <= 0:
        actual_u = Decimal(0)
    else:
        actual_u = (actual / reconstruction_max).quantize(Decimal("0.0001"))
    return target_u, actual_u


def build_throughput_budget_summary(
    *,
    reconstruction_capacity: Mapping[str, Any],
    throughput_target_percent: int,
    actual_committed_output_per_min: str,
) -> dict[str, Any]:
    recon_max = primary_reconstruction_max_per_min(reconstruction_capacity)
    actual = Decimal(actual_committed_output_per_min)
    target = compute_target_throughput_per_min(
        reconstruction_max=recon_max,
        percent=throughput_target_percent,
    )
    ev = evaluate_throughput_budget(actual=actual, target=target)
    target_u, actual_u = throughput_utilization_ratios(
        actual=actual,
        reconstruction_max=recon_max,
        percent=throughput_target_percent,
    )
    return {
        "reconstruction_max_throughput_per_min": decimal_str(recon_max),
        "throughput_target_percent": throughput_target_percent,
        "target_throughput_per_min": decimal_str(target),
        "actual_committed_output_per_min": actual_committed_output_per_min,
        "throughput_budget_satisfied": ev.satisfied,
        "throughput_shortfall_per_min": decimal_str(ev.shortfall),
        "target_utilization_ratio": decimal_str(target_u),
        "actual_utilization_ratio": decimal_str(actual_u),
        "throughput_target_status": "satisfied" if ev.satisfied else "shortfall",
    }


__all__ = [
    "DEFAULT_THROUGHPUT_TARGET_PERCENT",
    "MAX_THROUGHPUT_TARGET_PERCENT",
    "MIN_THROUGHPUT_TARGET_PERCENT",
    "THROUGHPUT_TARGET_SHORTFALL_ISSUE_CODE",
    "ThroughputBudgetEvaluation",
    "build_throughput_budget_summary",
    "compute_target_throughput_per_min",
    "evaluate_throughput_budget",
    "parse_throughput_target_percent",
    "primary_reconstruction_max_per_min",
    "throughput_utilization_ratios",
]
