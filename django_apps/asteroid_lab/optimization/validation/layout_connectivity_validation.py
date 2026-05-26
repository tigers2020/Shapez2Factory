"""Read-only layout connectivity validation (RTTP A6).

Asserts only — no repair. Product placement shortfall (committed < placement goal) is
**not** a validation failure; see throughput diagnostics and ``placement_goal_shortfall``.
"""

from __future__ import annotations

from django_apps.asteroid_lab.contracts.rttp_layout_issue_codes import (
    ISSUE_CODE_INSUFFICIENT_EXTERIOR_CONNECTORS,
    ISSUE_CODE_MISSING_EXTERIOR_ROUTE,
    ISSUE_CODE_MISSING_OUTPUT_TRANSPORT,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.placement_cells import (
    fixed_output_transport_cell,
)
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import OptimizationInput
from django_apps.asteroid_lab.services.rttp_route_connectivity import (
    count_exterior_connected_route_cells,
)


def _output_transport_reserved(
    *,
    committed_ids: tuple[str, ...],
    reserved_route_cells: frozenset[Coord],
    candidates_by_id: dict[str, BundleCandidate],
) -> bool:
    """True when each committed bundle's output face is represented in route reservation."""

    if not committed_ids:
        return True
    for candidate_id in committed_ids:
        candidate = candidates_by_id.get(candidate_id)
        if candidate is None:
            return False
        fot = fixed_output_transport_cell(candidate)
        stub = candidate.output_stub
        if fot in reserved_route_cells or stub in reserved_route_cells:
            continue
        return False
    return True


def _distinct_exterior_connectors_touched(
    *,
    reserved_route_cells: frozenset[Coord],
    inp: OptimizationInput,
) -> int:
    connector_coords = frozenset(
        goal.coord
        for goal in inp.route_goals
        if goal.transport_kind is None or goal.transport_kind is inp.transport_kind
    )
    if not connector_coords:
        return 0
    return sum(1 for coord in connector_coords if coord in reserved_route_cells)


def validate_layout_connectivity_issues(
    *,
    committed_ids: tuple[str, ...],
    reserved_route_cells: frozenset[Coord],
    candidates_by_id: dict[str, BundleCandidate],
    trunk_mask_cells: frozenset[Coord],
    inp: OptimizationInput | None = None,
) -> tuple[str, ...]:
    """Return stable issue codes when committed extractors lack transport invariants."""

    if not committed_ids:
        return ()

    issues: list[str] = []
    if not _output_transport_reserved(
        committed_ids=committed_ids,
        reserved_route_cells=reserved_route_cells,
        candidates_by_id=candidates_by_id,
    ):
        issues.append(ISSUE_CODE_MISSING_OUTPUT_TRANSPORT)

    exterior_count = count_exterior_connected_route_cells(
        reserved_route_cells,
        trunk_mask_cells,
    )
    if exterior_count <= 0:
        touched_connectors = 0
        if inp is not None:
            touched_connectors = _distinct_exterior_connectors_touched(
                reserved_route_cells=reserved_route_cells,
                inp=inp,
            )
        if touched_connectors <= 0:
            issues.append(ISSUE_CODE_MISSING_EXTERIOR_ROUTE)

    if inp is not None and inp.required_external_connector_count is not None:
        required = inp.required_external_connector_count
        touched = _distinct_exterior_connectors_touched(
            reserved_route_cells=reserved_route_cells,
            inp=inp,
        )
        if touched < required and len(committed_ids) >= required:
            issues.append(ISSUE_CODE_INSUFFICIENT_EXTERIOR_CONNECTORS)

    return tuple(issues)


__all__ = [
    "validate_layout_connectivity_issues",
]
