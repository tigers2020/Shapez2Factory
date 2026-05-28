"""Shared solver runtime entry DTOs (no service imports)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class SolverRuntimeEntryErrorCode(StrEnum):
    """Structured failure codes for solver runtime entry (no free-form strings)."""

    PROJECT_NOT_FOUND = "project_not_found"
    NO_MAP_INPUT = "no_map_input"
    DECODE_FAILED = "decode_failed"
    SOLVER_NOT_AVAILABLE = "SOLVER_NOT_AVAILABLE"
    PROVENANCE_INCOMPLETE = "provenance_incomplete"
    CATALOG_SLICE_REQUIRED = "catalog_slice_required"
    CATALOG_SLICE_HASH_MISMATCH = "catalog_slice_hash_mismatch"
    CATALOG_TRANSPORT_UNRESOLVED = "catalog_transport_unresolved"
    INVALID_THROUGHPUT_TARGET_PERCENT = "invalid_throughput_target_percent"
    INVALID_MAX_PLACEMENT_GOAL_COUNT = "invalid_max_placement_goal_count"
    RTTP_VALIDATION_FAILED = "rttp_validation_failed"


def empty_milestone_track_metrics() -> dict[str, Any]:
    return {
        "track_key": None,
        "frame_count": 0,
        "event_types": [],
        "replay_truncated": False,
        "truncation_reason": None,
        "dropped_frame_count": None,
        "diagnostic_reason": None,
        "source_solver_run_id": None,
    }


@dataclass(frozen=True, slots=True)
class SolverRuntimeEntryResult:
    ok: bool
    solver_run_id: int | None
    lab_replay_frames_json: list[dict[str, Any]]
    replay_track_metrics: dict[str, Any]
    solver_summary: dict[str, Any]
    validation_passed: bool
    gene_template_source: dict[str, Any] = field(default_factory=dict)
    error_code: SolverRuntimeEntryErrorCode | None = None
    message: str | None = None
    lab_optimization_milestone_frames_json: list[dict[str, Any]] = field(default_factory=list)
    lab_optimization_milestone_track_metrics: dict[str, Any] = field(
        default_factory=empty_milestone_track_metrics
    )


__all__ = [
    "SolverRuntimeEntryErrorCode",
    "SolverRuntimeEntryResult",
    "empty_milestone_track_metrics",
]
