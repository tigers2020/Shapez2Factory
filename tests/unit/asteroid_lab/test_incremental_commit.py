"""Incremental commit tests (Solver Runtime PR5)."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.candidate_score import GoalLoadKey
from django_apps.asteroid_lab.optimization.candidate_selector import SelectedCandidatePlan
from django_apps.asteroid_lab.optimization.commit_best_candidates import (
    ConfirmedGenePlacement,
    commit_selected_candidates,
)
from django_apps.asteroid_lab.optimization.enums import (
    CommitConflictReason,
    Direction,
    PlacementCommitState,
    ReservationState,
    RouteGoalKind,
    RouteProbeFailureReason,
    TransportKind,
    TransportMask,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    BBox,
    RouteGoal,
    greenfield_optimization_input,
)
from django_apps.asteroid_lab.optimization.route_domain import (
    RouteCellDomain,
    RouteDomainSnapshotBuilder,
)
from django_apps.asteroid_lab.optimization.route_probe import RouteProbeResult, run_route_probe


def _open_void_inp(*, bb: BBox | None = None, goals: frozenset[RouteGoal] | None = None):
    bb = bb or BBox(0, 8, 0, 0)
    void = frozenset(
        (sx, sy) for sx in range(bb.min_sx, bb.max_sx + 1) for sy in range(bb.min_sy, bb.max_sy + 1)
    )
    default_goal = RouteGoal(
        coord=(6, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    return replace(
        greenfield_optimization_input(bbox=bb),
        external_void_cells=void,
        route_goals=goals if goals is not None else frozenset({default_goal}),
    )


def _shape_candidate(
    *,
    candidate_id: str,
    extractor: tuple[int, int] = (0, 0),
    route_probe_start: tuple[int, int] = (0, 0),
    fixed_output_transport: tuple[int, int] | None = None,
    reached_goal: RouteGoal | None = None,
    transport_kind: TransportKind = TransportKind.SHAPE_BELT,
    base_throughput: int = 8,
) -> GeneCandidate:
    goal = reached_goal or RouteGoal(
        coord=(6, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=transport_kind,
        priority=10,
        existing_trunk=False,
    )
    probe = RouteProbeResult(
        reachable=True,
        path=(),
        cost=0,
        expanded_nodes=0,
        reached_goal=goal,
        goal_priority=goal.priority,
        failure_reason=None,
    )
    return GeneCandidate(
        candidate_id=candidate_id,
        gene_id="test_gene",
        topology_signature="sig",
        extractor=extractor,
        extensions=(),
        occupied_cells=frozenset({extractor}),
        route_probe_start=route_probe_start,
        fixed_output_transport=fixed_output_transport
        if fixed_output_transport is not None
        else (extractor[0] + 1, extractor[1]),
        output_dir=Direction.E,
        transport_kind=transport_kind,
        base_throughput=base_throughput,
        base_score=float(base_throughput),
        route_probe_result=probe,
    )


def _shape_candidate_with_offset_probe(
    *,
    candidate_id: str,
    extractor: tuple[int, int] = (0, 0),
    reached_goal: RouteGoal | None = None,
    transport_kind: TransportKind = TransportKind.SHAPE_BELT,
    base_throughput: int = 8,
) -> GeneCandidate:
    """Probe starts after output stub (real game layout: rps=2, fot=1)."""

    return _shape_candidate(
        candidate_id=candidate_id,
        extractor=extractor,
        route_probe_start=(extractor[0] + 2, extractor[1]),
        reached_goal=reached_goal,
        transport_kind=transport_kind,
        base_throughput=base_throughput,
    )


def _commit_offset_probe_candidate() -> tuple[GeneCandidate, ConfirmedGenePlacement]:
    inp = _open_void_inp()
    candidate = _shape_candidate_with_offset_probe(candidate_id="offset:1")
    plan = SelectedCandidatePlan(ordered_candidate_ids=(candidate.candidate_id,))
    result, _commit_timing, _diag = commit_selected_candidates(
        plan,
        {candidate.candidate_id: candidate},
        inp=inp,
    )
    assert len(result.confirmed) == 1
    return candidate, result.confirmed[0]


def test_incremental_commit_reprobes_latest_domain() -> None:
    inp = _open_void_inp()
    c1 = _shape_candidate(candidate_id="a:1", extractor=(0, 0), route_probe_start=(0, 0))
    c2 = _shape_candidate(candidate_id="b:2", extractor=(8, 0), route_probe_start=(8, 0))
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:1", "b:2"))
    snapshot_ids: list[int] = []
    original = RouteDomainSnapshotBuilder.build_snapshot

    def tracking_build(*args, **kwargs) -> dict[tuple[int, int], RouteCellDomain]:
        domain = original(*args, **kwargs)
        snapshot_ids.append(id(domain))
        return domain

    with patch.object(RouteDomainSnapshotBuilder, "build_snapshot", side_effect=tracking_build):
        _, _commit_timing, _diag = commit_selected_candidates(
            plan,
            {"a:1": c1, "b:2": c2},
            inp=inp,
        )

    assert len(snapshot_ids) >= 4
    assert len(set(snapshot_ids)) == len(snapshot_ids)


def test_incremental_commit_confirms_connected_candidate() -> None:
    inp = _open_void_inp()
    candidate = _shape_candidate(candidate_id="a:1")
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:1",))

    result, _commit_timing, _diag = commit_selected_candidates(
        plan,
        {candidate.candidate_id: candidate},
        inp=inp,
    )

    assert len(result.confirmed) == 1
    placement = result.confirmed[0]
    assert placement.commit_state == PlacementCommitState.CONFIRMED
    assert placement.reservation.reservation_state == ReservationState.CONFIRMED
    assert placement.reservation.candidate_id == "a:1"
    assert placement.reservation.reservation_id == "a:1:route:0"
    assert placement.reservation.path[0] == candidate.fixed_output_transport
    assert placement.reservation.path[-1] == (6, 0)


def test_incremental_commit_rolls_back_unreachable_candidate() -> None:
    inp = _open_void_inp()
    ok = _shape_candidate(candidate_id="a:ok", extractor=(0, 0), route_probe_start=(0, 0))
    blocked = _shape_candidate(candidate_id="b:blocked", extractor=(2, 0), route_probe_start=(1, 0))
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:ok", "b:blocked"))
    unreachable = RouteProbeResult(
        reachable=False,
        path=(),
        cost=0,
        expanded_nodes=0,
        reached_goal=None,
        goal_priority=None,
        failure_reason=RouteProbeFailureReason.EXHAUSTED,
    )

    def _probe_side_effect(probe_inp):
        if probe_inp.start == blocked.route_probe_start:
            return unreachable
        return run_route_probe(probe_inp)

    with patch(
        "django_apps.asteroid_lab.optimization.commit_best_candidates.run_route_probe",
        side_effect=_probe_side_effect,
    ):
        result, _commit_timing, _diag = commit_selected_candidates(
            plan,
            {ok.candidate_id: ok, blocked.candidate_id: blocked},
            inp=inp,
        )

    assert [c.candidate_id for c in result.confirmed] == ["a:ok"]
    assert result.skipped_candidate_ids == ("b:blocked",)
    assert len(result.skipped_candidate_ids) == 1
    skip = result.skipped_candidates[0]
    assert skip.reason is CommitConflictReason.ROUTE_PROBE_FAILED
    assert skip.reason.value == "route_probe_failed"
    assert skip.route_probe_failure_reason is RouteProbeFailureReason.EXHAUSTED
    assert len(result.confirmed[0].reservation.reserved_cells) > 0


def test_incremental_commit_updates_goal_load() -> None:
    goal = RouteGoal(
        coord=(6, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    inp = _open_void_inp(goals=frozenset({goal}))
    c1 = _shape_candidate(
        candidate_id="a:1",
        extractor=(0, 0),
        route_probe_start=(0, 0),
        reached_goal=goal,
        base_throughput=12,
    )
    c2 = _shape_candidate(
        candidate_id="b:2",
        extractor=(8, 0),
        route_probe_start=(8, 0),
        reached_goal=goal,
        base_throughput=4,
    )
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:1", "b:2"))

    result, _commit_timing, _diag = commit_selected_candidates(
        plan,
        {c1.candidate_id: c1, c2.candidate_id: c2},
        inp=inp,
    )

    key: GoalLoadKey = (goal.coord, TransportKind.SHAPE_BELT)
    assert result.goal_assigned_platforms[key] == 2


def test_incremental_commit_separates_shape_and_fluid_domains() -> None:
    shape_goal = RouteGoal(
        coord=(6, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    fluid_goal = RouteGoal(
        coord=(6, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.FLUID_PIPE,
        priority=10,
        existing_trunk=False,
    )
    inp = _open_void_inp(goals=frozenset({shape_goal, fluid_goal}))
    shape = _shape_candidate(
        candidate_id="shape:1",
        extractor=(0, 0),
        route_probe_start=(0, 0),
        reached_goal=shape_goal,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    fluid = _shape_candidate(
        candidate_id="fluid:1",
        extractor=(1, 0),
        route_probe_start=(0, 0),
        reached_goal=fluid_goal,
        transport_kind=TransportKind.FLUID_PIPE,
    )
    plan = SelectedCandidatePlan(ordered_candidate_ids=("shape:1", "fluid:1"))

    result, _commit_timing, _diag = commit_selected_candidates(
        plan,
        {shape.candidate_id: shape, fluid.candidate_id: fluid},
        inp=inp,
    )

    assert len(result.confirmed) == 1
    assert result.confirmed[0].candidate_id == "shape:1"
    assert result.skipped_candidate_ids == ("fluid:1",)
    skip = result.skipped_candidates[0]
    assert skip.reason is CommitConflictReason.ROUTE_PROBE_FAILED
    assert skip.route_probe_failure_reason is RouteProbeFailureReason.START_BLOCKED

    overlap_cell = result.confirmed[0].reservation.path[2]
    domain = RouteDomainSnapshotBuilder.build_snapshot(
        inp,
        confirmed_reservations=(result.confirmed[0].reservation,),
    )
    cell = domain[overlap_cell]
    assert bool(cell.transport_mask & TransportMask.SHAPE_BELT)
    assert not bool(cell.transport_mask & TransportMask.FLUID_PIPE)


def test_incremental_commit_reserved_cells_include_output_stub() -> None:
    candidate, placement = _commit_offset_probe_candidate()
    fot = candidate.fixed_output_transport
    assert fot in placement.reservation.reserved_cells
    assert placement.reservation.reserved_cells == frozenset(placement.reservation.path)


def test_incremental_commit_reservation_path_starts_at_output_stub() -> None:
    candidate, placement = _commit_offset_probe_candidate()
    fot = candidate.fixed_output_transport
    assert placement.reservation.path
    assert placement.reservation.path[0] == fot


def test_incremental_commit_reservation_excludes_extractor_body() -> None:
    candidate, placement = _commit_offset_probe_candidate()
    assert candidate.extractor not in placement.reservation.reserved_cells


def test_incremental_commit_skipped_record_transport_kind_conflict() -> None:
    shape_goal = RouteGoal(
        coord=(6, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    fluid_goal = RouteGoal(
        coord=(6, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.FLUID_PIPE,
        priority=10,
        existing_trunk=False,
    )
    inp = _open_void_inp(goals=frozenset({shape_goal, fluid_goal}))
    shape = _shape_candidate(
        candidate_id="shape:1",
        extractor=(0, 0),
        route_probe_start=(0, 0),
        reached_goal=shape_goal,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    fluid = _shape_candidate(
        candidate_id="fluid:1",
        extractor=(3, 0),
        route_probe_start=(3, 0),
        reached_goal=fluid_goal,
        transport_kind=TransportKind.FLUID_PIPE,
    )
    overlap_path = ((1, 0), (2, 0), (3, 0), (4, 0), (5, 0), (6, 0))
    fluid_probe = RouteProbeResult(
        reachable=True,
        path=overlap_path,
        cost=len(overlap_path),
        expanded_nodes=1,
        reached_goal=fluid_goal,
        goal_priority=fluid_goal.priority,
        failure_reason=None,
    )
    plan = SelectedCandidatePlan(ordered_candidate_ids=("shape:1", "fluid:1"))

    def _probe_side_effect(probe_inp):
        if probe_inp.start == fluid.route_probe_start:
            return fluid_probe
        return run_route_probe(probe_inp)

    with patch(
        "django_apps.asteroid_lab.optimization.commit_best_candidates.run_route_probe",
        side_effect=_probe_side_effect,
    ):
        result, _commit_timing, _diag = commit_selected_candidates(
            plan,
            {shape.candidate_id: shape, fluid.candidate_id: fluid},
            inp=inp,
        )

    assert len(result.confirmed) == 1
    assert result.skipped_candidate_ids == ("fluid:1",)
    assert result.skipped_candidates[0].reason is CommitConflictReason.TRANSPORT_KIND_CONFLICT


def test_commit_rejects_fixed_output_transport_on_committed_route_cell() -> None:
    goal = RouteGoal(
        coord=(6, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    inp = _open_void_inp(goals=frozenset({goal}))
    first = _shape_candidate(
        candidate_id="a:1",
        extractor=(0, 0),
        route_probe_start=(0, 0),
        reached_goal=goal,
    )
    shared_trunk = (3, 0)
    second = _shape_candidate(
        candidate_id="b:2",
        extractor=(10, 0),
        route_probe_start=(10, 0),
        fixed_output_transport=shared_trunk,
        reached_goal=goal,
    )
    second_probe = RouteProbeResult(
        reachable=True,
        path=(shared_trunk, (4, 0), (5, 0), (6, 0)),
        cost=4,
        expanded_nodes=1,
        reached_goal=goal,
        goal_priority=goal.priority,
        failure_reason=None,
    )
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:1", "b:2"))

    def _probe_side_effect(probe_inp):
        if probe_inp.start == second.route_probe_start:
            return second_probe
        return run_route_probe(probe_inp)

    with patch(
        "django_apps.asteroid_lab.optimization.commit_best_candidates.run_route_probe",
        side_effect=_probe_side_effect,
    ):
        result, _commit_timing, _diag = commit_selected_candidates(
            plan,
            {first.candidate_id: first, second.candidate_id: second},
            inp=inp,
        )

    assert len(result.confirmed) == 1
    assert result.skipped_candidate_ids == ("b:2",)
    assert (
        result.skipped_candidates[0].reason is CommitConflictReason.INLET_ON_SHARED_TRANSPORT
    )


def test_commit_allows_same_kind_route_path_sharing_after_stub() -> None:
    goal = RouteGoal(
        coord=(6, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    inp = _open_void_inp(goals=frozenset({goal}))
    first = _shape_candidate(
        candidate_id="a:1",
        extractor=(0, 0),
        route_probe_start=(0, 0),
        reached_goal=goal,
    )
    shared_trunk = (3, 0)
    second = _shape_candidate(
        candidate_id="b:2",
        extractor=(10, 0),
        route_probe_start=(10, 0),
        reached_goal=goal,
    )
    second_probe = RouteProbeResult(
        reachable=True,
        path=(
            second.fixed_output_transport,
            shared_trunk,
            (4, 0),
            (5, 0),
            (6, 0),
        ),
        cost=5,
        expanded_nodes=1,
        reached_goal=goal,
        goal_priority=goal.priority,
        failure_reason=None,
    )
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:1", "b:2"))

    def _probe_side_effect(probe_inp):
        if probe_inp.start == second.route_probe_start:
            return second_probe
        return run_route_probe(probe_inp)

    with patch(
        "django_apps.asteroid_lab.optimization.commit_best_candidates.run_route_probe",
        side_effect=_probe_side_effect,
    ):
        result, _commit_timing, _diag = commit_selected_candidates(
            plan,
            {first.candidate_id: first, second.candidate_id: second},
            inp=inp,
        )

    assert len(result.confirmed) == 2
    assert result.skipped_candidate_ids == ()
    assert shared_trunk in result.confirmed[0].reservation.path
    second_path = result.confirmed[1].reservation.path
    assert second_path[0] == second.fixed_output_transport
    assert shared_trunk in second_path[1:]


def test_commit_allows_extension_on_committed_transport_trunk() -> None:
    goal = RouteGoal(
        coord=(6, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    inp = _open_void_inp(goals=frozenset({goal}))
    shared_trunk = (3, 0)
    first = _shape_candidate(
        candidate_id="a:1",
        extractor=(0, 0),
        route_probe_start=(0, 0),
        reached_goal=goal,
    )
    second = GeneCandidate(
        candidate_id="b:2",
        gene_id="test_gene",
        topology_signature="sig",
        extractor=(10, 0),
        extensions=(shared_trunk,),
        occupied_cells=frozenset({(10, 0), shared_trunk}),
        route_probe_start=(10, 0),
        fixed_output_transport=(11, 0),
        output_dir=Direction.E,
        transport_kind=TransportKind.SHAPE_BELT,
        base_throughput=16,
        base_score=16.0,
        route_probe_result=RouteProbeResult(
            reachable=True,
            path=((11, 0), (4, 0), (5, 0), (6, 0)),
            cost=4,
            expanded_nodes=1,
            reached_goal=goal,
            goal_priority=goal.priority,
            failure_reason=None,
        ),
    )
    first_probe = RouteProbeResult(
        reachable=True,
        path=(first.fixed_output_transport, shared_trunk, (4, 0), (5, 0), (6, 0)),
        cost=5,
        expanded_nodes=1,
        reached_goal=goal,
        goal_priority=goal.priority,
        failure_reason=None,
    )
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:1", "b:2"))

    def _probe_side_effect(probe_inp):
        if probe_inp.start == first.route_probe_start:
            return first_probe
        if probe_inp.start == second.route_probe_start:
            return second.route_probe_result
        return run_route_probe(probe_inp)

    with patch(
        "django_apps.asteroid_lab.optimization.commit_best_candidates.run_route_probe",
        side_effect=_probe_side_effect,
    ):
        result, _, _diag = commit_selected_candidates(
            plan,
            {first.candidate_id: first, second.candidate_id: second},
            inp=inp,
        )

    assert len(result.confirmed) == 2
    assert result.skipped_candidate_ids == ()
    assert shared_trunk in result.confirmed[0].reservation.path


def test_commit_skips_equipment_transport_overlap() -> None:
    goal = RouteGoal(
        coord=(6, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    inp = _open_void_inp(goals=frozenset({goal}))
    first = _shape_candidate(
        candidate_id="a:1",
        extractor=(0, 0),
        route_probe_start=(0, 0),
        reached_goal=goal,
    )
    second = _shape_candidate(
        candidate_id="b:2",
        extractor=(10, 0),
        route_probe_start=(10, 0),
        reached_goal=goal,
    )
    overlap_path = (
        (0, 0),
        first.fixed_output_transport,
        (2, 0),
        (3, 0),
        (4, 0),
        (5, 0),
        (6, 0),
    )
    second_probe = RouteProbeResult(
        reachable=True,
        path=overlap_path,
        cost=len(overlap_path),
        expanded_nodes=1,
        reached_goal=goal,
        goal_priority=goal.priority,
        failure_reason=None,
    )
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:1", "b:2"))

    def _probe_side_effect(probe_inp):
        if probe_inp.start == second.route_probe_start:
            return second_probe
        return run_route_probe(probe_inp)

    with patch(
        "django_apps.asteroid_lab.optimization.commit_best_candidates.run_route_probe",
        side_effect=_probe_side_effect,
    ):
        result, _commit_timing, _diag = commit_selected_candidates(
            plan,
            {first.candidate_id: first, second.candidate_id: second},
            inp=inp,
        )

    assert len(result.confirmed) == 1
    assert result.skipped_candidate_ids == ("b:2",)
    assert result.skipped_candidates[0].reason is CommitConflictReason.EQUIPMENT_TRANSPORT_OVERLAP


def test_incremental_commit_skipped_record_occupied_cell_conflict() -> None:
    inp = _open_void_inp()
    first = _shape_candidate(candidate_id="a:1", extractor=(0, 0), route_probe_start=(0, 0))
    second = _shape_candidate(candidate_id="b:2", extractor=(0, 0), route_probe_start=(0, 0))
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:1", "b:2"))

    result, _commit_timing, _diag = commit_selected_candidates(
        plan,
        {first.candidate_id: first, second.candidate_id: second},
        inp=inp,
    )

    assert len(result.confirmed) == 1
    assert result.skipped_candidate_ids == ("b:2",)
    skip = result.skipped_candidates[0]
    assert skip.reason is CommitConflictReason.OCCUPIED_CELL_CONFLICT
    assert skip.anchor_coord == (0, 0)
    assert skip.route_probe_failure_reason is None


def test_incremental_commit_conflict_reason_enum_only() -> None:
    inp = _open_void_inp()
    ok = _shape_candidate(candidate_id="a:ok", extractor=(0, 0), route_probe_start=(0, 0))
    blocked = _shape_candidate(candidate_id="b:blocked", extractor=(2, 0), route_probe_start=(1, 0))
    duplicate = _shape_candidate(candidate_id="c:dup", extractor=(0, 0), route_probe_start=(0, 0))
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:ok", "b:blocked", "c:dup"))

    result, _commit_timing, _diag = commit_selected_candidates(
        plan,
        {ok.candidate_id: ok, blocked.candidate_id: blocked, duplicate.candidate_id: duplicate},
        inp=inp,
    )

    for record in result.skipped_candidates:
        assert isinstance(record.reason, CommitConflictReason)
        assert record.reason.value in {m.value for m in CommitConflictReason}
        if record.route_probe_failure_reason is not None:
            assert isinstance(record.route_probe_failure_reason, RouteProbeFailureReason)


def test_deferred_retry_rounds_zero_matches_single_pass_outcome() -> None:
    """deferred_retry_rounds=0 must match legacy immediate skip for probe failures."""

    inp = _open_void_inp()
    ok = _shape_candidate(candidate_id="a:ok", extractor=(0, 0), route_probe_start=(0, 0))
    blocked = _shape_candidate(candidate_id="b:blocked", extractor=(2, 0), route_probe_start=(1, 0))
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:ok", "b:blocked"))
    unreachable = RouteProbeResult(
        reachable=False,
        path=(),
        cost=0,
        expanded_nodes=0,
        reached_goal=None,
        goal_priority=None,
        failure_reason=RouteProbeFailureReason.EXHAUSTED,
    )

    def _probe_side_effect(probe_inp):
        if probe_inp.start == blocked.route_probe_start:
            return unreachable
        return run_route_probe(probe_inp)

    by_id = {ok.candidate_id: ok, blocked.candidate_id: blocked}
    with patch(
        "django_apps.asteroid_lab.optimization.commit_best_candidates.run_route_probe",
        side_effect=_probe_side_effect,
    ):
        legacy, _, diag_disabled = commit_selected_candidates(
            plan, by_id, inp=inp, deferred_retry_rounds=0
        )
        with_retry, _, diag_enabled = commit_selected_candidates(
            plan, by_id, inp=inp, deferred_retry_rounds=1
        )

    assert {c.candidate_id for c in legacy.confirmed} == {
        c.candidate_id for c in with_retry.confirmed
    }
    assert legacy.skipped_candidates == with_retry.skipped_candidates
    assert diag_disabled.deferred_retry_eligible_count == 0
    assert diag_disabled.deferred_retry_rounds == 0
    assert diag_disabled.primary_route_probe_failed_count == 1
    assert diag_enabled.deferred_retry_eligible_count == 1
    assert diag_enabled.deferred_retry_recovered_count == 0
    assert diag_enabled.deferred_retry_still_failed_count == 1


def test_deferred_retry_recovers_order_dependent_probe_failure() -> None:
    inp = _open_void_inp()
    goal = RouteGoal(
        coord=(6, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    first = _shape_candidate(
        candidate_id="a:1",
        extractor=(0, 0),
        route_probe_start=(0, 0),
        reached_goal=goal,
    )
    second = _shape_candidate(
        candidate_id="b:2",
        extractor=(8, 0),
        route_probe_start=(8, 0),
        reached_goal=goal,
    )
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:1", "b:2"))
    unreachable = RouteProbeResult(
        reachable=False,
        path=(),
        cost=0,
        expanded_nodes=0,
        reached_goal=None,
        goal_priority=None,
        failure_reason=RouteProbeFailureReason.EXHAUSTED,
    )
    probe_calls: list[tuple[int, int]] = []

    def _probe_side_effect(probe_inp):
        probe_calls.append(probe_inp.start)
        if probe_inp.start == first.route_probe_start and len(probe_calls) == 1:
            return unreachable
        return run_route_probe(probe_inp)

    with patch(
        "django_apps.asteroid_lab.optimization.commit_best_candidates.run_route_probe",
        side_effect=_probe_side_effect,
    ):
        result, _, diag = commit_selected_candidates(
            plan,
            {first.candidate_id: first, second.candidate_id: second},
            inp=inp,
            deferred_retry_rounds=1,
        )

    assert len(result.confirmed) == 2
    assert {c.candidate_id for c in result.confirmed} == {"a:1", "b:2"}
    assert result.skipped_candidates == ()
    assert diag.deferred_retry_eligible_count == 1
    assert diag.deferred_retry_recovered_count == 1
    assert diag.deferred_retry_still_failed_count == 0
    assert diag.primary_route_probe_failed_count == 1


def test_deferred_retry_does_not_retry_inlet_or_occupied_skips() -> None:
    goal = RouteGoal(
        coord=(6, 0),
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=10,
        existing_trunk=False,
    )
    inp = _open_void_inp(goals=frozenset({goal}))
    first = _shape_candidate(
        candidate_id="a:1",
        extractor=(0, 0),
        route_probe_start=(0, 0),
        reached_goal=goal,
    )
    shared_trunk = (3, 0)
    second = _shape_candidate(
        candidate_id="b:2",
        extractor=(10, 0),
        route_probe_start=(10, 0),
        fixed_output_transport=shared_trunk,
        reached_goal=goal,
    )
    second_probe = RouteProbeResult(
        reachable=True,
        path=(shared_trunk, (4, 0), (5, 0), (6, 0)),
        cost=4,
        expanded_nodes=1,
        reached_goal=goal,
        goal_priority=goal.priority,
        failure_reason=None,
    )
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:1", "b:2"))

    def _probe_side_effect(probe_inp):
        if probe_inp.start == second.route_probe_start:
            return second_probe
        return run_route_probe(probe_inp)

    with patch(
        "django_apps.asteroid_lab.optimization.commit_best_candidates.run_route_probe",
        side_effect=_probe_side_effect,
    ):
        result, _, diag = commit_selected_candidates(
            plan,
            {first.candidate_id: first, second.candidate_id: second},
            inp=inp,
            deferred_retry_rounds=1,
        )

    assert result.skipped_candidate_ids == ("b:2",)
    assert result.skipped_candidates[0].reason is CommitConflictReason.INLET_ON_SHARED_TRANSPORT
    assert diag.deferred_retry_eligible_count == 0
    assert diag.deferred_retry_recovered_count == 0


def test_deferred_retry_does_not_queue_occupied_conflict() -> None:
    inp = _open_void_inp()
    first = _shape_candidate(candidate_id="a:1", extractor=(0, 0), route_probe_start=(0, 0))
    second = _shape_candidate(candidate_id="b:2", extractor=(0, 0), route_probe_start=(0, 0))
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:1", "b:2"))

    result, _, diag = commit_selected_candidates(
        plan,
        {first.candidate_id: first, second.candidate_id: second},
        inp=inp,
        deferred_retry_rounds=1,
    )

    assert result.skipped_candidates[0].reason is CommitConflictReason.OCCUPIED_CELL_CONFLICT
    assert diag.deferred_retry_eligible_count == 0
