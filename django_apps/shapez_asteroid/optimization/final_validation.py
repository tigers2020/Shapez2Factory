"""Sequence 7 — read-only final validation gate for ``IncrementalCommitResult``."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.dto import (
    BundleCandidate,
    IncrementalCommitResult,
    OptimizationInput,
    RouteGoal,
    ValidationIssue,
    ValidationResult,
)
from django_apps.shapez_asteroid.optimization.enums import (
    ReservationState,
    RouteGoalKind,
    TransportKind,
    TransportMask,
    ValidationIssueCode,
    ValidationSeverity,
)

_SEVERITY_ORDER: dict[ValidationSeverity, int] = {
    ValidationSeverity.ERROR: 0,
    ValidationSeverity.WARNING: 1,
    ValidationSeverity.INFO: 2,
}

_PATH_INDEX_NONE_SORT = 10**9


def _candidate_pool_by_id(pool: Sequence[BundleCandidate]) -> dict[str, BundleCandidate]:
    out: dict[str, BundleCandidate] = {}
    for c in sorted(pool, key=lambda z: z.candidate_id):
        if c.candidate_id in out:
            raise ValueError(f"duplicate candidate_id in pool: {c.candidate_id!r}")
        out[c.candidate_id] = c
    return out


def _mask_allows(mask: TransportMask, kind: TransportKind) -> bool:
    if kind is TransportKind.SHAPE_BELT:
        return bool(mask & TransportMask.SHAPE_BELT)
    if kind is TransportKind.FLUID_PIPE:
        return bool(mask & TransportMask.FLUID_PIPE)
    return False


def _is_int_coord_component(v: object) -> bool:
    return type(v) is int


def _is_valid_coord(obj: object) -> bool:
    return (
        isinstance(obj, Coord) and _is_int_coord_component(obj.x) and _is_int_coord_component(obj.y)
    )


def _issue_sort_key(issue: ValidationIssue) -> tuple[object, ...]:
    coord_key: tuple[object, ...]
    if issue.coord is None:
        coord_key = (1, 0, 0)
    else:
        coord_key = (0, issue.coord.x, issue.coord.y)
    path_key = _PATH_INDEX_NONE_SORT if issue.path_index is None else issue.path_index
    return (
        _SEVERITY_ORDER.get(issue.severity, 99),
        issue.issue_code.value,
        issue.candidate_id or "",
        issue.route_reservation_id or "",
        coord_key,
        path_key,
        issue.message,
    )


def _sort_issues(issues: Sequence[ValidationIssue]) -> tuple[ValidationIssue, ...]:
    return tuple(sorted(issues, key=_issue_sort_key))


def _passed_from_issues(issues: Sequence[ValidationIssue]) -> bool:
    return not any(i.severity is ValidationSeverity.ERROR for i in issues)


def _goal_matches_input(reached: RouteGoal, goals: frozenset[RouteGoal]) -> bool:
    if reached in goals:
        return True
    for g in goals:
        if (
            g.coord == reached.coord
            and g.goal_kind == reached.goal_kind
            and g.transport_kind == reached.transport_kind
            and g.priority == reached.priority
        ):
            return True
    return False


def _emit(
    issues: list[ValidationIssue],
    *,
    issue_code: ValidationIssueCode,
    severity: ValidationSeverity,
    message: str,
    coord: Coord | None = None,
    candidate_id: str | None = None,
    route_reservation_id: str | None = None,
    path_index: int | None = None,
    route_goal_kind: RouteGoalKind | None = None,
    transport_kind: TransportKind | None = None,
) -> None:
    issues.append(
        ValidationIssue(
            issue_code=issue_code,
            severity=severity,
            coord=coord,
            candidate_id=candidate_id,
            route_reservation_id=route_reservation_id,
            path_index=path_index,
            route_goal_kind=route_goal_kind,
            transport_kind=transport_kind,
            message=message,
        )
    )


def _validate_coord_contract(
    optimization_input: OptimizationInput,
    candidate_pool: Sequence[BundleCandidate],
    commit_result: IncrementalCommitResult,
    issues: list[ValidationIssue],
) -> None:
    def check_coord(c: object, *, ctx: str) -> None:
        if not _is_valid_coord(c):
            _emit(
                issues,
                issue_code=ValidationIssueCode.INVALID_COORD_CONTRACT,
                severity=ValidationSeverity.ERROR,
                coord=c if isinstance(c, Coord) else None,
                message=f"invalid Coord contract: {ctx}",
            )

    for c in sorted(optimization_input.asteroid_cells, key=lambda z: (z.x, z.y)):
        check_coord(c, ctx="optimization_input.asteroid_cells")
    for c in sorted(optimization_input.mineable_cells, key=lambda z: (z.x, z.y)):
        check_coord(c, ctx="optimization_input.mineable_cells")
    for c in sorted(optimization_input.rim_cells, key=lambda z: (z.x, z.y)):
        check_coord(c, ctx="optimization_input.rim_cells")
    for c in sorted(optimization_input.interior_cells, key=lambda z: (z.x, z.y)):
        check_coord(c, ctx="optimization_input.interior_cells")
    for c in sorted(optimization_input.external_void_cells, key=lambda z: (z.x, z.y)):
        check_coord(c, ctx="optimization_input.external_void_cells")
    for g in sorted(
        optimization_input.route_goals,
        key=lambda z: (z.coord.x, z.coord.y, z.priority),
    ):
        check_coord(g.coord, ctx="optimization_input.route_goals.coord")
    for etc in sorted(
        optimization_input.existing_transport_cells,
        key=lambda z: (z.coord.x, z.coord.y),
    ):
        check_coord(etc.coord, ctx="optimization_input.existing_transport_cells.coord")
    for c in sorted(optimization_input.existing_trunk_cells, key=lambda z: (z.x, z.y)):
        check_coord(c, ctx="optimization_input.existing_trunk_cells")
    for c in sorted(optimization_input.protected_corridor_cells, key=lambda z: (z.x, z.y)):
        check_coord(c, ctx="optimization_input.protected_corridor_cells")
    for c in sorted(optimization_input.blocked_cells, key=lambda z: (z.x, z.y)):
        check_coord(c, ctx="optimization_input.blocked_cells")
    for n in sorted(optimization_input.topology_graph.nodes, key=lambda z: (z.coord.x, z.coord.y)):
        check_coord(n.coord, ctx="topology_graph.node.coord")
    for edge in sorted(
        optimization_input.topology_graph.edges,
        key=lambda z: (z.a.x, z.a.y, z.b.x, z.b.y),
    ):
        check_coord(edge.a, ctx="topology_graph.edge.a")
        check_coord(edge.b, ctx="topology_graph.edge.b")

    for cand in sorted(candidate_pool, key=lambda z: z.candidate_id):
        check_coord(cand.extractor, ctx=f"candidate {cand.candidate_id!r} extractor")
        for i, ext in enumerate(cand.extensions):
            check_coord(ext, ctx=f"candidate {cand.candidate_id!r} extensions[{i}]")
        for c in sorted(cand.occupied_cells, key=lambda z: (z.x, z.y)):
            check_coord(c, ctx=f"candidate {cand.candidate_id!r} occupied_cells")
        check_coord(cand.output_stub, ctx=f"candidate {cand.candidate_id!r} output_stub")
        for i, path_coord in enumerate(cand.route_probe_result.path):
            check_coord(
                path_coord,
                ctx=f"candidate {cand.candidate_id!r} route_probe_result.path[{i}]",
            )
        rg = cand.route_probe_result.reached_goal
        if rg is not None:
            check_coord(rg.coord, ctx=f"candidate {cand.candidate_id!r} reached_goal.coord")

    for pl in commit_result.committed_placements:
        for c in sorted(pl.occupied_cells, key=lambda z: (z.x, z.y)):
            check_coord(c, ctx=f"placement {pl.candidate_id!r} occupied_cells")

    for res in commit_result.route_reservations:
        for i, c in enumerate(res.path):
            check_coord(c, ctx=f"reservation {res.reservation_id!r} path[{i}]")
        for c in sorted(res.reserved_cells, key=lambda z: (z.x, z.y)):
            check_coord(c, ctx=f"reservation {res.reservation_id!r} reserved_cells")
        check_coord(
            res.reached_goal.coord,
            ctx=f"reservation {res.reservation_id!r} reached_goal.coord",
        )

    for c, dom in sorted(commit_result.final_route_domain.items(), key=lambda z: (z[0].x, z[0].y)):
        check_coord(c, ctx="final_route_domain key")
        check_coord(dom.coord, ctx="final_route_domain RouteCellDomain.coord")


def _validate_confirmed_candidate_has_one_reservation(
    commit_result: IncrementalCommitResult,
    issues: list[ValidationIssue],
) -> None:
    reservations = commit_result.route_reservations
    for pl in commit_result.committed_placements:
        matches = [
            r
            for r in reservations
            if r.candidate_id == pl.candidate_id
            and r.reservation_state is ReservationState.CONFIRMED
            and r.reservation_id == pl.route_reservation_id
        ]
        if len(matches) != 1:
            _emit(
                issues,
                issue_code=ValidationIssueCode.CONFIRMED_RESERVATION_MISSING,
                severity=ValidationSeverity.ERROR,
                candidate_id=pl.candidate_id,
                route_reservation_id=pl.route_reservation_id,
                message=(
                    "expected exactly one CONFIRMED RouteReservation matching "
                    "placement.candidate_id and placement.route_reservation_id"
                ),
            )


def _validate_reserved_cells_match_path(
    commit_result: IncrementalCommitResult,
    issues: list[ValidationIssue],
) -> None:
    for res in commit_result.route_reservations:
        if res.reservation_state is not ReservationState.CONFIRMED:
            continue
        if res.reserved_cells != frozenset(res.path):
            _emit(
                issues,
                issue_code=ValidationIssueCode.RESERVED_PATH_MISMATCH,
                severity=ValidationSeverity.ERROR,
                route_reservation_id=res.reservation_id,
                candidate_id=res.candidate_id,
                message="reserved_cells must equal frozenset(path) for confirmed reservation",
            )


def _validate_route_goal_contract(
    optimization_input: OptimizationInput,
    commit_result: IncrementalCommitResult,
    issues: list[ValidationIssue],
) -> None:
    goals = optimization_input.route_goals
    for res in commit_result.route_reservations:
        if res.reservation_state is not ReservationState.CONFIRMED:
            continue
        rg = res.reached_goal
        if not res.path:
            _emit(
                issues,
                issue_code=ValidationIssueCode.ROUTE_GOAL_MISMATCH,
                severity=ValidationSeverity.ERROR,
                route_reservation_id=res.reservation_id,
                candidate_id=res.candidate_id,
                message="empty path for confirmed reservation",
            )
            continue
        last = res.path[-1]
        if rg.coord != last:
            _emit(
                issues,
                issue_code=ValidationIssueCode.ROUTE_GOAL_MISMATCH,
                severity=ValidationSeverity.ERROR,
                coord=last,
                route_reservation_id=res.reservation_id,
                candidate_id=res.candidate_id,
                path_index=len(res.path) - 1,
                route_goal_kind=rg.goal_kind,
                transport_kind=res.transport_kind,
                message="reached_goal.coord must equal path[-1]",
            )
        if not _goal_matches_input(rg, goals):
            _emit(
                issues,
                issue_code=ValidationIssueCode.ROUTE_GOAL_MISMATCH,
                severity=ValidationSeverity.ERROR,
                coord=rg.coord,
                route_reservation_id=res.reservation_id,
                candidate_id=res.candidate_id,
                route_goal_kind=rg.goal_kind,
                transport_kind=rg.transport_kind,
                message="reached_goal not listed in optimization_input.route_goals contract",
            )
        if rg.transport_kind is not None and rg.transport_kind is not res.transport_kind:
            _emit(
                issues,
                issue_code=ValidationIssueCode.ROUTE_GOAL_MISMATCH,
                severity=ValidationSeverity.ERROR,
                route_reservation_id=res.reservation_id,
                candidate_id=res.candidate_id,
                route_goal_kind=rg.goal_kind,
                transport_kind=res.transport_kind,
                message=(
                    "reached_goal.transport_kind must be None or "
                    "match reservation.transport_kind"
                ),
            )


def _validate_transport_kind_consistency(
    candidate_by_id: Mapping[str, BundleCandidate],
    commit_result: IncrementalCommitResult,
    issues: list[ValidationIssue],
) -> None:
    res_by_id = {r.reservation_id: r for r in commit_result.route_reservations}
    for pl in commit_result.committed_placements:
        res = res_by_id.get(pl.route_reservation_id)
        if res is None or res.reservation_state is not ReservationState.CONFIRMED:
            continue
        if pl.transport_kind is not res.transport_kind:
            _emit(
                issues,
                issue_code=ValidationIssueCode.TRANSPORT_KIND_MISMATCH,
                severity=ValidationSeverity.ERROR,
                candidate_id=pl.candidate_id,
                route_reservation_id=res.reservation_id,
                transport_kind=res.transport_kind,
                message="placement.transport_kind must match reservation.transport_kind",
            )
        cand = candidate_by_id.get(pl.candidate_id)
        if cand is not None and cand.transport_kind is not res.transport_kind:
            _emit(
                issues,
                issue_code=ValidationIssueCode.TRANSPORT_KIND_MISMATCH,
                severity=ValidationSeverity.ERROR,
                candidate_id=pl.candidate_id,
                route_reservation_id=res.reservation_id,
                transport_kind=res.transport_kind,
                message="candidate.transport_kind must match reservation.transport_kind",
            )


def _validate_no_invalid_overlap(
    commit_result: IncrementalCommitResult,
    issues: list[ValidationIssue],
) -> None:
    placements = commit_result.committed_placements
    cell_to_candidates: dict[Coord, list[str]] = {}
    for pl in placements:
        for c in pl.occupied_cells:
            cell_to_candidates.setdefault(c, []).append(pl.candidate_id)
    for coord, ids in sorted(cell_to_candidates.items(), key=lambda z: (z[0].x, z[0].y)):
        uniq = sorted(frozenset(ids))
        if len(uniq) > 1:
            _emit(
                issues,
                issue_code=ValidationIssueCode.INVALID_OVERLAP,
                severity=ValidationSeverity.ERROR,
                coord=coord,
                message=f"occupied cell shared by placements: {uniq!r}",
            )

    all_occupied = (
        frozenset().union(*(p.occupied_cells for p in placements)) if placements else frozenset()
    )

    for res in commit_result.route_reservations:
        if res.reservation_state is not ReservationState.CONFIRMED:
            continue
        own_occ: frozenset[Coord] = frozenset()
        for pl in placements:
            if (
                pl.candidate_id == res.candidate_id
                and pl.route_reservation_id == res.reservation_id
            ):
                own_occ = pl.occupied_cells
                break
        for i, c in enumerate(res.path):
            if c in own_occ:
                _emit(
                    issues,
                    issue_code=ValidationIssueCode.INVALID_OVERLAP,
                    severity=ValidationSeverity.ERROR,
                    coord=c,
                    candidate_id=res.candidate_id,
                    route_reservation_id=res.reservation_id,
                    path_index=i,
                    message="reservation path intersects its own placement occupied_cells",
                )
            elif c in all_occupied:
                _emit(
                    issues,
                    issue_code=ValidationIssueCode.INVALID_OVERLAP,
                    severity=ValidationSeverity.ERROR,
                    coord=c,
                    candidate_id=res.candidate_id,
                    route_reservation_id=res.reservation_id,
                    path_index=i,
                    message="reservation path intersects a committed placement occupied_cells",
                )


def _validate_route_domain_vs_reserved_paths(
    commit_result: IncrementalCommitResult,
    issues: list[ValidationIssue],
) -> None:
    domain = commit_result.final_route_domain
    all_occupied = (
        frozenset().union(
            *(p.occupied_cells for p in commit_result.committed_placements),
        )
        if commit_result.committed_placements
        else frozenset()
    )

    for res in commit_result.route_reservations:
        if res.reservation_state is not ReservationState.CONFIRMED:
            continue
        for i, c in enumerate(res.path):
            dom = domain.get(c)
            if dom is None:
                _emit(
                    issues,
                    issue_code=ValidationIssueCode.ROUTE_GOAL_MISMATCH,
                    severity=ValidationSeverity.ERROR,
                    coord=c,
                    candidate_id=res.candidate_id,
                    route_reservation_id=res.reservation_id,
                    path_index=i,
                    message="path coord missing from final_route_domain",
                )
                continue
            if dom.hard_blocked and c not in all_occupied:
                _emit(
                    issues,
                    issue_code=ValidationIssueCode.ROUTE_GOAL_MISMATCH,
                    severity=ValidationSeverity.ERROR,
                    coord=c,
                    candidate_id=res.candidate_id,
                    route_reservation_id=res.reservation_id,
                    path_index=i,
                    message="path coord hard_blocked in final_route_domain (not a placement cell)",
                )
            if not _mask_allows(dom.transport_mask, res.transport_kind):
                _emit(
                    issues,
                    issue_code=ValidationIssueCode.TRANSPORT_KIND_MISMATCH,
                    severity=ValidationSeverity.ERROR,
                    coord=c,
                    candidate_id=res.candidate_id,
                    route_reservation_id=res.reservation_id,
                    path_index=i,
                    transport_kind=res.transport_kind,
                    message="final_route_domain transport_mask forbids reservation.transport_kind",
                )


def _validate_no_orphan_transport(
    optimization_input: OptimizationInput,
    commit_result: IncrementalCommitResult,
    issues: list[ValidationIssue],
) -> None:
    placement_ids = {p.candidate_id for p in commit_result.committed_placements}
    goals = optimization_input.route_goals
    for res in commit_result.route_reservations:
        if not res.path:
            _emit(
                issues,
                issue_code=ValidationIssueCode.ORPHAN_TRANSPORT,
                severity=ValidationSeverity.ERROR,
                candidate_id=res.candidate_id,
                route_reservation_id=res.reservation_id,
                message="reservation path is empty",
            )
        if res.candidate_id not in placement_ids:
            _emit(
                issues,
                issue_code=ValidationIssueCode.ORPHAN_TRANSPORT,
                severity=ValidationSeverity.ERROR,
                candidate_id=res.candidate_id,
                route_reservation_id=res.reservation_id,
                message="reservation.candidate_id has no committed placement",
            )
        rg = res.reached_goal
        if not _goal_matches_input(rg, goals):
            _emit(
                issues,
                issue_code=ValidationIssueCode.ORPHAN_TRANSPORT,
                severity=ValidationSeverity.ERROR,
                coord=rg.coord,
                candidate_id=res.candidate_id,
                route_reservation_id=res.reservation_id,
                route_goal_kind=rg.goal_kind,
                transport_kind=rg.transport_kind,
                message="reached_goal is not a valid RouteGoal for optimization_input",
            )


def _validate_extractor_output_connected(
    candidate_by_id: Mapping[str, BundleCandidate],
    commit_result: IncrementalCommitResult,
    issues: list[ValidationIssue],
) -> None:
    res_by_rid = {r.reservation_id: r for r in commit_result.route_reservations}
    for pl in commit_result.committed_placements:
        cand = candidate_by_id.get(pl.candidate_id)
        if cand is None:
            continue
        res = res_by_rid.get(pl.route_reservation_id)
        if res is None or res.reservation_state is not ReservationState.CONFIRMED:
            _emit(
                issues,
                issue_code=ValidationIssueCode.EXTRACTOR_OUTPUT_DISCONNECTED,
                severity=ValidationSeverity.ERROR,
                candidate_id=pl.candidate_id,
                route_reservation_id=pl.route_reservation_id,
                message="matching CONFIRMED reservation missing for committed placement",
            )
            continue
        if not res.path or cand.output_stub != res.path[0]:
            _emit(
                issues,
                issue_code=ValidationIssueCode.EXTRACTOR_OUTPUT_DISCONNECTED,
                severity=ValidationSeverity.ERROR,
                candidate_id=pl.candidate_id,
                route_reservation_id=res.reservation_id,
                coord=cand.output_stub,
                message=(
                    "candidate.output_stub must equal first coord of " "confirmed reservation.path"
                ),
            )


def _validate_extension_constraints_v0(
    candidate_by_id: Mapping[str, BundleCandidate],
    commit_result: IncrementalCommitResult,
    issues: list[ValidationIssue],
) -> None:
    committed_ids = {p.candidate_id for p in commit_result.committed_placements}
    for cid in sorted(committed_ids):
        cand = candidate_by_id.get(cid)
        if cand is None:
            continue
        exts = cand.extensions
        if len(exts) > 3:
            _emit(
                issues,
                issue_code=ValidationIssueCode.EXTENSION_COUNT_EXCEEDED,
                severity=ValidationSeverity.ERROR,
                candidate_id=cid,
                message="more than 3 extensions",
            )
        if len(set(exts)) != len(exts):
            _emit(
                issues,
                issue_code=ValidationIssueCode.EXTENSION_ATTACHMENT_INVALID,
                severity=ValidationSeverity.ERROR,
                candidate_id=cid,
                message="extensions must be unique",
            )
        occ = cand.occupied_cells
        if cand.extractor not in occ:
            _emit(
                issues,
                issue_code=ValidationIssueCode.EXTENSION_ATTACHMENT_INVALID,
                severity=ValidationSeverity.ERROR,
                candidate_id=cid,
                coord=cand.extractor,
                message="extractor must be in candidate.occupied_cells",
            )
        for i, e in enumerate(exts):
            if e not in occ:
                _emit(
                    issues,
                    issue_code=ValidationIssueCode.EXTENSION_ATTACHMENT_INVALID,
                    severity=ValidationSeverity.ERROR,
                    candidate_id=cid,
                    coord=e,
                    message=f"extension[{i}] must be in candidate.occupied_cells",
                )


def validate_incremental_commit_result(
    optimization_input: OptimizationInput,
    candidate_pool: Sequence[BundleCandidate],
    commit_result: IncrementalCommitResult,
) -> ValidationResult:
    """Assert-gate validation: read-only checks on ``commit_result`` (no routing or mutation)."""

    candidate_by_id = _candidate_pool_by_id(candidate_pool)

    issues: list[ValidationIssue] = []
    _validate_coord_contract(optimization_input, candidate_pool, commit_result, issues)
    _validate_confirmed_candidate_has_one_reservation(commit_result, issues)
    _validate_reserved_cells_match_path(commit_result, issues)
    _validate_route_goal_contract(optimization_input, commit_result, issues)
    _validate_transport_kind_consistency(candidate_by_id, commit_result, issues)
    _validate_no_invalid_overlap(commit_result, issues)
    _validate_route_domain_vs_reserved_paths(commit_result, issues)
    _validate_no_orphan_transport(optimization_input, commit_result, issues)
    _validate_extractor_output_connected(candidate_by_id, commit_result, issues)
    _validate_extension_constraints_v0(candidate_by_id, commit_result, issues)

    sorted_issues = _sort_issues(issues)
    return ValidationResult(passed=_passed_from_issues(sorted_issues), issues=sorted_issues)


def validation_passed_from_issues(issues: Sequence[ValidationIssue]) -> bool:
    """Whether issues contain no ERROR severity (WARNING/INFO do not fail)."""

    return _passed_from_issues(issues)
