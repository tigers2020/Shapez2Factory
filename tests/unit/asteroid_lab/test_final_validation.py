"""Phase L final validation tests (PR7)."""

from __future__ import annotations

from dataclasses import replace

from django_apps.asteroid_lab.optimization.candidate_selector import SelectedCandidatePlan
from django_apps.asteroid_lab.optimization.commit_best_candidates import (
    ConfirmedGenePlacement,
    IncrementalCommitResult,
    commit_selected_candidates,
)
from django_apps.asteroid_lab.optimization.enums import (
    PlacementCommitState,
    ReservationState,
    RouteGoalKind,
    TransportKind,
    ValidationIssueCode,
    ValidationSeverity,
)
from django_apps.asteroid_lab.optimization.final_validation import validate_final_layout
from django_apps.asteroid_lab.optimization.input_contracts import RouteGoal, RouteReservation
from django_apps.asteroid_lab.optimization.materialization_dtos import (
    MaterializedLayoutCells,
    MaterializedTransportCell,
)
from django_apps.asteroid_lab.optimization.route_network_materializer import (
    materialize_route_network,
)
from tests.unit.asteroid_lab.test_incremental_commit import (
    _open_void_inp,
    _shape_candidate,
)


def test_validation_read_only() -> None:
    inp = _open_void_inp()
    candidate = _shape_candidate(candidate_id="a:1")
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:1",))
    commit = commit_selected_candidates(plan, {candidate.candidate_id: candidate}, inp=inp)
    mat = materialize_route_network(commit, {candidate.candidate_id: candidate})
    inp_before = replace(inp)
    commit_before = replace(
        commit,
        confirmed=tuple(replace(p, reservation=replace(p.reservation)) for p in commit.confirmed),
    )

    r1 = validate_final_layout(
        commit,
        mat.layout,
        inp=inp,
        candidates_by_id={candidate.candidate_id: candidate},
    )
    r2 = validate_final_layout(
        commit,
        mat.layout,
        inp=inp,
        candidates_by_id={candidate.candidate_id: candidate},
    )

    assert r1 == r2
    assert inp == inp_before
    assert commit.confirmed == commit_before.confirmed


def test_validation_issue_codes_explicit() -> None:
    inp = _open_void_inp()
    bad_res = RouteReservation(
        reservation_id="x:route:0",
        candidate_id="missing",
        transport_kind=TransportKind.SHAPE_BELT,
        path=((1, 0), (2, 0)),
        reserved_cells=frozenset({(9, 9)}),
        cost=1,
        reached_goal=RouteGoal(
            coord=(6, 0),
            goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
            transport_kind=TransportKind.SHAPE_BELT,
            priority=10,
            existing_trunk=False,
        ),
        goal_priority=10,
        reservation_state=ReservationState.PROVISIONAL,
        domain_cell_transitions=(),
    )
    commit = IncrementalCommitResult(
        confirmed=(
            ConfirmedGenePlacement(
                candidate_id="missing",
                reservation=bad_res,
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        ),
        skipped_candidate_ids=(),
        goal_assigned_platforms={},
    )
    result = validate_final_layout(commit, None, inp=inp, candidates_by_id={})
    assert not result.passed
    for issue in result.issues:
        assert isinstance(issue.issue_code, ValidationIssueCode)
        assert issue.issue_code.value == issue.issue_code


def test_validation_passes_connected_layout() -> None:
    inp = _open_void_inp()
    candidate = _shape_candidate(candidate_id="a:1")
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:1",))
    commit = commit_selected_candidates(plan, {candidate.candidate_id: candidate}, inp=inp)
    mat = materialize_route_network(commit, {candidate.candidate_id: candidate})
    assert mat.layout is not None

    result = validate_final_layout(
        commit,
        mat.layout,
        inp=inp,
        candidates_by_id={candidate.candidate_id: candidate},
    )
    assert result.passed
    assert result.issues == ()


def test_validation_fails_reserved_cells_path_mismatch() -> None:
    inp = _open_void_inp()
    candidate = _shape_candidate(candidate_id="a:1")
    goal = RouteGoal(
        coord=(6, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    res = RouteReservation(
        reservation_id="a:1:route:0",
        candidate_id="a:1",
        transport_kind=TransportKind.SHAPE_BELT,
        path=((0, 0), (6, 0)),
        reserved_cells=frozenset({(0, 0)}),
        cost=1,
        reached_goal=goal,
        goal_priority=10,
        reservation_state=ReservationState.CONFIRMED,
        domain_cell_transitions=(),
    )
    commit = IncrementalCommitResult(
        confirmed=(
            ConfirmedGenePlacement(
                candidate_id="a:1",
                reservation=res,
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        ),
        skipped_candidate_ids=(),
        goal_assigned_platforms={},
    )
    layout = MaterializedLayoutCells(
        cells=(
            MaterializedTransportCell(
                coord=(0, 0),
                tile_type="SpaceBelt_Left",
                transport_kind=TransportKind.SHAPE_BELT,
            ),
        )
    )
    result = validate_final_layout(
        commit,
        layout,
        inp=inp,
        candidates_by_id={candidate.candidate_id: candidate},
    )
    assert not result.passed
    codes = {i.issue_code for i in result.issues}
    assert ValidationIssueCode.RESERVED_PATH_MISMATCH in codes


def test_extractor_not_connected_issue_has_detail_fields() -> None:
    inp = _open_void_inp()
    candidate = _shape_candidate(candidate_id="a:1", extractor=(0, 0))
    goal = RouteGoal(
        coord=(6, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    res = RouteReservation(
        reservation_id="a:1:route:0",
        candidate_id="a:1",
        transport_kind=TransportKind.SHAPE_BELT,
        path=((1, 0), (2, 0), (6, 0)),
        reserved_cells=frozenset({(1, 0), (2, 0), (6, 0)}),
        cost=1,
        reached_goal=goal,
        goal_priority=10,
        reservation_state=ReservationState.CONFIRMED,
        domain_cell_transitions=(),
    )
    commit = IncrementalCommitResult(
        confirmed=(
            ConfirmedGenePlacement(
                candidate_id="a:1",
                reservation=res,
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        ),
        skipped_candidate_ids=(),
        goal_assigned_platforms={},
    )
    result = validate_final_layout(
        commit,
        None,
        inp=inp,
        candidates_by_id={candidate.candidate_id: candidate},
    )
    assert not result.passed
    issues = [i for i in result.issues if i.issue_code is ValidationIssueCode.EXTRACTOR_NOT_CONNECTED]
    assert len(issues) == 1
    issue = issues[0]
    assert issue.coord == (0, 0)
    assert issue.candidate_id == "a:1"
    assert issue.route_reservation_id == "a:1:route:0"
    assert issue.message == "extractor not on reservation path"


def test_validation_fails_candidate_without_confirmed_reservation() -> None:
    inp = _open_void_inp()
    candidate = _shape_candidate(candidate_id="a:1")
    goal = RouteGoal(
        coord=(6, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    res = RouteReservation(
        reservation_id="a:1:route:0",
        candidate_id="a:1",
        transport_kind=TransportKind.SHAPE_BELT,
        path=((0, 0), (6, 0)),
        reserved_cells=frozenset({(0, 0), (6, 0)}),
        cost=1,
        reached_goal=goal,
        goal_priority=10,
        reservation_state=ReservationState.PROVISIONAL,
        domain_cell_transitions=(),
    )
    commit = IncrementalCommitResult(
        confirmed=(
            ConfirmedGenePlacement(
                candidate_id="a:1",
                reservation=res,
                commit_state=PlacementCommitState.CONFIRMED,
            ),
        ),
        skipped_candidate_ids=(),
        goal_assigned_platforms={},
    )
    result = validate_final_layout(
        commit,
        None,
        inp=inp,
        candidates_by_id={candidate.candidate_id: candidate},
    )
    assert not result.passed
    codes = {i.issue_code for i in result.issues}
    assert ValidationIssueCode.CANDIDATE_RESERVATION_MISMATCH in codes
    assert any(i.severity is ValidationSeverity.ERROR for i in result.issues)
