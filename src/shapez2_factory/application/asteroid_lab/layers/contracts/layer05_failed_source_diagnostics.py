"""Layer 05 per-failed-source diagnostics (instrumentation only)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
    Layer05FailureReason,
    Layer05RoutePlan,
)
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord


class Layer05FailureBucket(StrEnum):
    WRONG_OR_MISSING_OUTPUT_STUB = "wrong_or_missing_output_stub"
    NO_REACHABLE_ROOT = "no_reachable_root"
    BLOCKED_BY_EQUIPMENT_OR_INTERIOR = "blocked_by_equipment_or_interior"
    ROUTE_BUDGET_EXHAUSTED = "route_budget_exhausted"
    CONFLICT_WITH_COMMITTED_ROUTE = "conflict_with_committed_route"
    TRANSPORT_KIND_OR_CONNECTOR_MISMATCH = "transport_kind_or_connector_mismatch"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class Layer05FailedSourceDiagnostic:
    source_id: str
    source_coord: Coord
    output_dir: str | None
    transport_kind: str
    source_load_m: int
    candidate_root_count: int
    nearest_root_distance: int | None
    failure_reason: Layer05FailureReason
    failure_bucket: Layer05FailureBucket
    blocked_cell_count: int
    conflict_cell_count: int
    attempted_probe_count: int
    shortest_probe_length: int | None
    detail: str = ""


def failure_reason_to_bucket(
    reason: Layer05FailureReason,
    *,
    detail: str = "",
) -> Layer05FailureBucket:
    if reason == Layer05FailureReason.CAPACITY_OVERFLOW:
        return Layer05FailureBucket.ROUTE_BUDGET_EXHAUSTED
    if reason == Layer05FailureReason.COMMIT_OVERLAP_BLOCKED:
        return Layer05FailureBucket.CONFLICT_WITH_COMMITTED_ROUTE
    if reason == Layer05FailureReason.INTERIOR_OCCUPIED_BLOCKED:
        return Layer05FailureBucket.BLOCKED_BY_EQUIPMENT_OR_INTERIOR
    if reason in {
        Layer05FailureReason.NO_CONNECTOR_WITH_CAPACITY,
        Layer05FailureReason.MIX_UNSUPPORTED,
        Layer05FailureReason.RESOURCE_KIND_MISMATCH,
    }:
        return Layer05FailureBucket.TRANSPORT_KIND_OR_CONNECTOR_MISMATCH
    if reason == Layer05FailureReason.ROUTE_NOT_FOUND:
        if "blocked_by_l4_interior_count=" in detail or "blocked_by_equipment_count=" in detail:
            return Layer05FailureBucket.BLOCKED_BY_EQUIPMENT_OR_INTERIOR
        return Layer05FailureBucket.NO_REACHABLE_ROOT
    if reason in {
        Layer05FailureReason.EMPTY_L3_PACKAGE,
        Layer05FailureReason.MISSING_L2_EXTERIOR_PLAN,
        Layer05FailureReason.UNSUPPORTED_IO_SIGNATURE,
        Layer05FailureReason.CATALOG_MISSING_TILE,
    }:
        return Layer05FailureBucket.OTHER
    return Layer05FailureBucket.OTHER


def aggregate_failure_histogram(
    diagnostics: tuple[Layer05FailedSourceDiagnostic, ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in diagnostics:
        key = entry.failure_bucket.value
        counts[key] = counts.get(key, 0) + 1
    return counts


def aggregate_reason_histogram(
    diagnostics: tuple[Layer05FailedSourceDiagnostic, ...],
) -> dict[str, int]:
    counts: dict[str, int] = {}
    for entry in diagnostics:
        key = entry.failure_reason.value
        counts[key] = counts.get(key, 0) + 1
    return counts


def format_l5_failure_eval_diagnostics(
    route_plan: Layer05RoutePlan | None,
    *,
    example_limit: int = 5,
) -> tuple[str, ...]:
    if route_plan is None:
        return ()
    entries = route_plan.failed_source_diagnostics
    if not entries:
        return ()

    lines: list[str] = []
    for bucket, count in sorted(aggregate_failure_histogram(entries).items()):
        lines.append(f"l5_failure_bucket:{bucket}={count}")
    for reason, count in sorted(aggregate_reason_histogram(entries).items()):
        lines.append(f"l5_failure_reason:{reason}={count}")

    for entry in sorted(entries, key=lambda e: e.source_id)[:example_limit]:
        x, y = entry.source_coord
        lines.append(
            "l5_failed_example:"
            f"{entry.source_id}@{x},{y}:"
            f"{entry.failure_bucket.value}:"
            f"{entry.failure_reason.value}",
        )
    return tuple(lines)


__all__ = [
    "Layer05FailedSourceDiagnostic",
    "Layer05FailureBucket",
    "aggregate_failure_histogram",
    "aggregate_reason_histogram",
    "failure_reason_to_bucket",
    "format_l5_failure_eval_diagnostics",
]
