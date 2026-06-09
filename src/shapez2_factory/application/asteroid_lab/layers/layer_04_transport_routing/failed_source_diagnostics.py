"""Build per-source L5 failure diagnostics at route commit failure sites."""

from __future__ import annotations

import re

from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_failed_source_diagnostics import (  # noqa: E501
    Layer05FailedSourceDiagnostic,
    failure_reason_to_bucket,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer05_route import (
    Layer05FailureReason,
    Layer05SourceView,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    CommittedRimSeedPlacement,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.route_goal import RouteGoal
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord

_INTERIOR_RE = re.compile(r"blocked_by_l4_interior_count=(\d+)")
_EQUIPMENT_RE = re.compile(r"blocked_by_equipment_count=(\d+)")


def _nearest_goal_distance(stub: Coord, goals: tuple[RouteGoal, ...]) -> int | None:
    if not goals:
        return None
    return min(abs(stub[0] - goal.coord[0]) + abs(stub[1] - goal.coord[1]) for goal in goals)


def _blocked_counts_from_detail(detail: str) -> tuple[int, int]:
    interior_match = _INTERIOR_RE.search(detail)
    equipment_match = _EQUIPMENT_RE.search(detail)
    interior = int(interior_match.group(1)) if interior_match else 0
    equipment = int(equipment_match.group(1)) if equipment_match else 0
    return interior, equipment


def build_failed_source_diagnostic(
    *,
    source: Layer05SourceView,
    placement: CommittedRimSeedPlacement | None,
    transport_kind: str,
    reason: Layer05FailureReason,
    detail: str,
    goals: tuple[RouteGoal, ...],
) -> Layer05FailedSourceDiagnostic:
    interior_blocked, equipment_blocked = _blocked_counts_from_detail(detail)
    blocked_cell_count = interior_blocked + equipment_blocked
    conflict_cell_count = 1 if reason == Layer05FailureReason.COMMIT_OVERLAP_BLOCKED else 0
    probe_path = placement.route_probe_path if placement is not None else source.route_probe_path
    shortest_probe_length = len(probe_path) if probe_path else None
    output_dir = placement.output_dir if placement is not None else None

    return Layer05FailedSourceDiagnostic(
        source_id=source.placement_id,
        source_coord=source.m_output_stub,
        output_dir=output_dir,
        transport_kind=transport_kind,
        source_load_m=source.source_load_m,
        candidate_root_count=len(goals),
        nearest_root_distance=_nearest_goal_distance(source.m_output_stub, goals),
        failure_reason=reason,
        failure_bucket=failure_reason_to_bucket(reason, detail=detail),
        blocked_cell_count=blocked_cell_count,
        conflict_cell_count=conflict_cell_count,
        attempted_probe_count=1,
        shortest_probe_length=shortest_probe_length,
        detail=detail,
    )


__all__ = ["build_failed_source_diagnostic"]
