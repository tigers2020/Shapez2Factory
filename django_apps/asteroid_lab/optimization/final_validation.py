"""Phase L — read-only final layout validation (PR7)."""

from __future__ import annotations

from collections.abc import Mapping

from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.commit_best_candidates import IncrementalCommitResult
from django_apps.asteroid_lab.optimization.enums import (
    ReservationState,
    ValidationIssueCode,
    ValidationSeverity,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RouteReservation,
    ValidationIssue,
    ValidationResult,
)
from django_apps.asteroid_lab.optimization.materialization_dtos import MaterializedLayoutCells


def _coord_sort_key(coord: object) -> tuple[int, int]:
    if not isinstance(coord, (tuple, list)) or len(coord) != 2:
        return (0, 0)
    try:
        return (int(coord[0]), int(coord[1]))
    except (TypeError, ValueError):
        return (0, 0)


def _coord_contract_ok(coord: object) -> bool:
    if not isinstance(coord, (tuple, list)) or len(coord) != 2:
        return False
    try:
        int(coord[0])
        int(coord[1])
    except (TypeError, ValueError):
        return False
    return True


def _issue(
    *,
    issue_code: ValidationIssueCode,
    severity: ValidationSeverity = ValidationSeverity.ERROR,
    coord: tuple[int, int] | None = None,
    candidate_id: str | None = None,
    route_reservation_id: str | None = None,
    path_index: int | None = None,
    message: str,
    issue_extra: dict[str, object] | None = None,
) -> ValidationIssue:
    return ValidationIssue(
        issue_code=issue_code,
        severity=severity,
        coord=coord,
        candidate_id=candidate_id,
        route_reservation_id=route_reservation_id,
        path_index=path_index,
        route_goal_kind=None,
        transport_kind=None,
        message=message,
        issue_extra=issue_extra,
    )


def _extractor_not_connected_extra(
    candidate: GeneCandidate,
    res: RouteReservation,
) -> dict[str, object]:
    path_set = frozenset(res.path)
    return {
        "extractor_coord": candidate.extractor,
        "output_stub": candidate.fixed_output_transport,
        "reservation_path_head": res.path[0] if res.path else None,
        "reservation_path_tail": res.path[-1] if res.path else None,
        "reservation_path_len": len(res.path),
        "reservation_path_contains_output_stub": (
            candidate.fixed_output_transport in res.reserved_cells
        ),
        "reservation_path_contains_extractor": candidate.extractor in path_set,
        "transport_kind": res.transport_kind,
    }


def validate_final_layout(
    commit: IncrementalCommitResult,
    layout: MaterializedLayoutCells | None,
    *,
    inp: OptimizationInput,
    candidates_by_id: Mapping[str, GeneCandidate],
) -> ValidationResult:
    """Assert final layout and reservations satisfy solver contracts (read-only)."""

    issues: list[ValidationIssue] = []

    if layout is None:
        issues.append(
            _issue(
                issue_code=ValidationIssueCode.MATERIALIZATION_FAILED,
                message="materialized layout is missing",
            )
        )

    reservations_by_candidate: dict[str, list[RouteReservation]] = {}
    for placement in commit.confirmed:
        cid = placement.candidate_id
        reservations_by_candidate.setdefault(cid, []).append(placement.reservation)

        if cid not in candidates_by_id:
            issues.append(
                _issue(
                    issue_code=ValidationIssueCode.CANDIDATE_POOL_MISSING,
                    candidate_id=cid,
                    message=f"candidate {cid!r} not in pool",
                )
            )

        res = placement.reservation
        if res.reservation_state is not ReservationState.CONFIRMED:
            issues.append(
                _issue(
                    issue_code=ValidationIssueCode.CANDIDATE_RESERVATION_MISMATCH,
                    candidate_id=cid,
                    route_reservation_id=res.reservation_id,
                    message="reservation is not CONFIRMED",
                )
            )

        if res.reserved_cells != frozenset(res.path):
            issues.append(
                _issue(
                    issue_code=ValidationIssueCode.RESERVED_PATH_MISMATCH,
                    candidate_id=cid,
                    route_reservation_id=res.reservation_id,
                    message="reserved_cells does not match path set",
                )
            )

        candidate = candidates_by_id.get(cid)
        if candidate is not None:
            if candidate.fixed_output_transport not in res.reserved_cells and res.path:
                issues.append(
                    _issue(
                        issue_code=ValidationIssueCode.EXTRACTOR_NOT_CONNECTED,
                        coord=candidate.extractor,
                        candidate_id=cid,
                        route_reservation_id=res.reservation_id,
                        message="output stub not on reservation path",
                        issue_extra=_extractor_not_connected_extra(candidate, res),
                    )
                )
            elif not res.path and candidate.fixed_output_transport != res.reached_goal.coord:
                issues.append(
                    _issue(
                        issue_code=ValidationIssueCode.EXTRACTOR_NOT_CONNECTED,
                        coord=candidate.extractor,
                        candidate_id=cid,
                        route_reservation_id=res.reservation_id,
                        message="empty path does not connect output stub to goal",
                        issue_extra=_extractor_not_connected_extra(candidate, res),
                    )
                )

    for cid, res_list in reservations_by_candidate.items():
        confirmed = [r for r in res_list if r.reservation_state is ReservationState.CONFIRMED]
        if len(confirmed) != 1:
            issues.append(
                _issue(
                    issue_code=ValidationIssueCode.CANDIDATE_RESERVATION_MISMATCH,
                    candidate_id=cid,
                    message=f"expected exactly one CONFIRMED reservation, got {len(confirmed)}",
                )
            )

    reserved_all: set[tuple[int, int]] = set()
    for placement in commit.confirmed:
        reserved_all.update(placement.reservation.path)

    if layout is not None:
        for cell in layout.cells:
            if not _coord_contract_ok(cell.coord):
                issues.append(
                    _issue(
                        issue_code=ValidationIssueCode.INVALID_COORD_CONTRACT,
                        coord=cell.coord if _coord_contract_ok(cell.coord) else None,
                        message="materialized cell violates server coord contract",
                    )
                )
            if cell.coord not in reserved_all:
                issues.append(
                    _issue(
                        issue_code=ValidationIssueCode.ORPHAN_TRANSPORT,
                        coord=cell.coord,
                        message="materialized transport not on any reservation path",
                    )
                )

        equipment_coords = {c.coord: c.cell_kind for c in layout.equipment_cells}
        for placement in commit.confirmed:
            candidate = candidates_by_id.get(placement.candidate_id)
            if candidate is None:
                continue
            if candidate.extractor not in equipment_coords:
                issues.append(
                    _issue(
                        issue_code=ValidationIssueCode.PLACEMENT_NOT_MATERIALIZED,
                        coord=candidate.extractor,
                        candidate_id=placement.candidate_id,
                        message="extractor not present in materialized equipment",
                    )
                )
            for ext in candidate.extensions:
                if ext not in equipment_coords:
                    issues.append(
                        _issue(
                            issue_code=ValidationIssueCode.PLACEMENT_NOT_MATERIALIZED,
                            coord=ext,
                            candidate_id=placement.candidate_id,
                            message="extension not present in materialized equipment",
                        )
                    )

    for coord in sorted(reserved_all, key=_coord_sort_key):
        if not _coord_contract_ok(coord):
            issues.append(
                _issue(
                    issue_code=ValidationIssueCode.INVALID_COORD_CONTRACT,
                    coord=(int(coord[0]), int(coord[1])) if len(coord) == 2 else None,
                    message="reservation path coord violates server contract",
                )
            )

    passed = not any(i.severity is ValidationSeverity.ERROR for i in issues)
    return ValidationResult(passed=passed, issues=tuple(issues))
