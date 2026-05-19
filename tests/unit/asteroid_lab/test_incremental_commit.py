"""Incremental commit tests (Solver Runtime PR5)."""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import patch

from django_apps.asteroid_lab.optimization.candidate_dtos import GeneCandidate
from django_apps.asteroid_lab.optimization.candidate_score import GoalLoadKey
from django_apps.asteroid_lab.optimization.candidate_selector import SelectedCandidatePlan
from django_apps.asteroid_lab.optimization.commit_best_candidates import commit_selected_candidates
from django_apps.asteroid_lab.optimization.enums import (
    Direction,
    PlacementCommitState,
    ReservationState,
    RouteGoalKind,
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
from django_apps.asteroid_lab.optimization.route_probe import RouteProbeResult


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
        fixed_output_transport=(extractor[0] + 1, extractor[1]),
        output_dir=Direction.E,
        transport_kind=transport_kind,
        base_throughput=base_throughput,
        base_score=float(base_throughput),
        route_probe_result=probe,
    )


def test_incremental_commit_reprobes_latest_domain() -> None:
    inp = _open_void_inp()
    c1 = _shape_candidate(candidate_id="a:1", extractor=(0, 0), route_probe_start=(0, 0))
    c2 = _shape_candidate(candidate_id="b:2", extractor=(2, 0), route_probe_start=(2, 0))
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:1", "b:2"))
    snapshot_ids: list[int] = []
    original = RouteDomainSnapshotBuilder.build_snapshot

    def tracking_build(*args, **kwargs) -> dict[tuple[int, int], RouteCellDomain]:
        domain = original(*args, **kwargs)
        snapshot_ids.append(id(domain))
        return domain

    with patch.object(RouteDomainSnapshotBuilder, "build_snapshot", side_effect=tracking_build):
        commit_selected_candidates(
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

    result = commit_selected_candidates(
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
    assert placement.reservation.path[0] == (0, 0)
    assert placement.reservation.path[-1] == (6, 0)


def test_incremental_commit_rolls_back_unreachable_candidate() -> None:
    inp = _open_void_inp()
    ok = _shape_candidate(candidate_id="a:ok", extractor=(0, 0), route_probe_start=(0, 0))
    blocked = _shape_candidate(candidate_id="b:blocked", extractor=(0, 0), route_probe_start=(1, 0))
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:ok", "b:blocked"))

    result = commit_selected_candidates(
        plan,
        {ok.candidate_id: ok, blocked.candidate_id: blocked},
        inp=inp,
    )

    assert [c.candidate_id for c in result.confirmed] == ["a:ok"]
    assert result.skipped_candidate_ids == ("b:blocked",)
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
        extractor=(2, 0),
        route_probe_start=(2, 0),
        reached_goal=goal,
        base_throughput=4,
    )
    plan = SelectedCandidatePlan(ordered_candidate_ids=("a:1", "b:2"))

    result = commit_selected_candidates(
        plan,
        {c1.candidate_id: c1, c2.candidate_id: c2},
        inp=inp,
    )

    key: GoalLoadKey = (goal.coord, TransportKind.SHAPE_BELT)
    assert result.goal_assigned_platforms[key] == 16


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

    result = commit_selected_candidates(
        plan,
        {shape.candidate_id: shape, fluid.candidate_id: fluid},
        inp=inp,
    )

    assert len(result.confirmed) == 1
    assert result.confirmed[0].candidate_id == "shape:1"
    assert result.skipped_candidate_ids == ("fluid:1",)

    overlap_cell = result.confirmed[0].reservation.path[2]
    domain = RouteDomainSnapshotBuilder.build_snapshot(
        inp,
        confirmed_reservations=(result.confirmed[0].reservation,),
    )
    cell = domain[overlap_cell]
    assert bool(cell.transport_mask & TransportMask.SHAPE_BELT)
    assert not bool(cell.transport_mask & TransportMask.FLUID_PIPE)
