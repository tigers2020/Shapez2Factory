"""Frozen master valid baseline contract for Golden Loop regression guards."""

from __future__ import annotations

from typing import Any

from shapez2_factory.application.asteroid_lab.experiments.golden_fixture_eval import (
    GoldenEvalResult,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
    Layer05RoutePlan,
)

# Canon: docs/superpowers/reports/2026-06-09-golden-loop-valid-baseline.md
CANONICAL_THROUGHPUT_TARGET_PERCENT = 80
CANONICAL_BUDGET_MS = 60_000
CANONICAL_SPEED_TIER = 1

MASTER_SOURCE_COUNT = 76
MASTER_ROUTED_SOURCE_COUNT = 76
MASTER_FAILED_SOURCE_COUNT = 0
MASTER_MIN_ROUTED_THROUGHPUT = 30960.0
MASTER_ROUTE_ISLAND_COUNT = 0
MASTER_ORPHAN_COUNT = 0


def assert_master_valid_route_plan(route_plan: Layer05RoutePlan | None) -> None:
    if route_plan is None:
        msg = "route_plan is required for master valid baseline"
        raise AssertionError(msg)
    metrics = route_plan.metrics
    if metrics.source_count != MASTER_SOURCE_COUNT:
        msg = f"source_count={metrics.source_count}, expected {MASTER_SOURCE_COUNT}"
        raise AssertionError(msg)
    if metrics.routed_source_count != MASTER_ROUTED_SOURCE_COUNT:
        msg = (
            f"routed_source_count={metrics.routed_source_count}, "
            f"expected {MASTER_ROUTED_SOURCE_COUNT}"
        )
        raise AssertionError(msg)
    if metrics.failed_source_count != MASTER_FAILED_SOURCE_COUNT:
        msg = (
            f"failed_source_count={metrics.failed_source_count}, "
            f"expected {MASTER_FAILED_SOURCE_COUNT}"
        )
        raise AssertionError(msg)


def assert_master_valid_eval_result(result: GoldenEvalResult) -> None:
    if not result.valid:
        msg = f"valid=false diagnostics={list(result.diagnostics)}"
        raise AssertionError(msg)
    if result.score <= 0:
        msg = f"score={result.score}, expected > 0 for valid baseline"
        raise AssertionError(msg)
    if result.miner_count != MASTER_SOURCE_COUNT:
        msg = f"miner_count={result.miner_count}, expected {MASTER_SOURCE_COUNT}"
        raise AssertionError(msg)
    if result.routed_throughput < MASTER_MIN_ROUTED_THROUGHPUT:
        msg = (
            f"routed_throughput={result.routed_throughput}, "
            f"expected >= {MASTER_MIN_ROUTED_THROUGHPUT}"
        )
        raise AssertionError(msg)
    if result.route_island_count != MASTER_ROUTE_ISLAND_COUNT:
        msg = (
            f"route_island_count={result.route_island_count}, "
            f"expected {MASTER_ROUTE_ISLAND_COUNT}"
        )
        raise AssertionError(msg)
    if result.orphan_count != MASTER_ORPHAN_COUNT:
        msg = f"orphan_count={result.orphan_count}, expected {MASTER_ORPHAN_COUNT}"
        raise AssertionError(msg)
    transport_mismatch = [d for d in result.diagnostics if d.startswith("transport_kind_mismatch")]
    if transport_mismatch:
        msg = f"unexpected transport_kind_mismatch diagnostics: {transport_mismatch}"
        raise AssertionError(msg)
    l5_failures = [d for d in result.diagnostics if d.startswith("l5_failed_sources:")]
    if l5_failures:
        msg = f"unexpected L5 failure diagnostics: {l5_failures}"
        raise AssertionError(msg)


def assert_master_valid_loop_summary(summary: dict[str, Any]) -> None:
    if not summary.get("best_valid"):
        msg = f"best_valid=false summary={summary}"
        raise AssertionError(msg)
    best_score = summary.get("best_score")
    if best_score is None or float(best_score) <= 0:
        msg = f"best_score={best_score}, expected > 0"
        raise AssertionError(msg)


def assert_master_valid_diagnostics_payload(payload: dict[str, Any]) -> None:
    if not payload.get("best_valid"):
        msg = f"best_valid=false payload={payload}"
        raise AssertionError(msg)
    failure_patterns = payload.get("failure_patterns") or {}
    if failure_patterns:
        msg = f"unexpected failure_patterns={failure_patterns}"
        raise AssertionError(msg)


__all__ = [
    "CANONICAL_BUDGET_MS",
    "CANONICAL_SPEED_TIER",
    "CANONICAL_THROUGHPUT_TARGET_PERCENT",
    "MASTER_FAILED_SOURCE_COUNT",
    "MASTER_MIN_ROUTED_THROUGHPUT",
    "MASTER_ORPHAN_COUNT",
    "MASTER_ROUTE_ISLAND_COUNT",
    "MASTER_ROUTED_SOURCE_COUNT",
    "MASTER_SOURCE_COUNT",
    "assert_master_valid_diagnostics_payload",
    "assert_master_valid_eval_result",
    "assert_master_valid_loop_summary",
    "assert_master_valid_route_plan",
]
