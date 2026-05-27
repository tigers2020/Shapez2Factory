"""LNS ELCP context propagation (Run #238 wiring regression)."""

from __future__ import annotations

from decimal import Decimal
from types import SimpleNamespace

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import (
    ExteriorLaneCapacityPlan,
    ExteriorTransportLane,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import RouteProbeStartPolicy
from django_apps.asteroid_lab.optimization.commit import local_lns
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    CommitConflict,
    CommitConflictReason,
    CommitResult,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    RouteGoal,
    RouteGoalKind,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome


def _goal(coord: tuple[int, int]) -> RouteGoal:
    return RouteGoal(
        coord=coord,
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=20,
        existing_trunk=False,
    )


def _plan() -> ExteriorLaneCapacityPlan:
    lane = ExteriorTransportLane(
        lane_id="exterior_lane:shape_belt:0",
        transport_kind=TransportKind.SHAPE_BELT,
        connector_goal=_goal((5, 5)),
        capacity_per_min=Decimal("2880"),
        target_load_per_min=Decimal("2880"),
        anchor_coord=(5, 5),
    )
    return ExteriorLaneCapacityPlan(
        transport_kind=TransportKind.SHAPE_BELT,
        max_asteroid_throughput_per_min=Decimal("2880"),
        lane_capacity_per_min=Decimal("2880"),
        required_lane_count=1,
        lanes=(lane,),
    )


def _candidate(candidate_id: str, *, anchor: tuple[int, int]) -> SimpleNamespace:
    return SimpleNamespace(
        candidate_id=candidate_id,
        anchor_coord=anchor,
        pattern=object(),
        occupied_cells=frozenset({anchor}),
        output_stub=(anchor[0], anchor[1] + 1),
        output_dir="N",
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=1,
        route_probe_cost=1,
        reachable=True,
    )


def test_local_lns_forwards_elcp_kwargs_to_incremental_commit(monkeypatch) -> None:
    plan = _plan()
    keep = _candidate("keep", anchor=(10, 10))
    conflicted = _candidate("conflict", anchor=(0, 0))
    candidates_by_id = {keep.candidate_id: keep, conflicted.candidate_id: conflicted}
    primary = CommitResult(
        committed_ids=(keep.candidate_id,),
        reserved_route_cells=frozenset(),
        domain_version=1,
        conflicts=(
            CommitConflict(
                candidate_id=conflicted.candidate_id,
                reason=CommitConflictReason.REPROBE_FAILED,
            ),
        ),
        exterior_lane_assignments=(
            {"candidate_id": keep.candidate_id, "exterior_lane_id": plan.lanes[0].lane_id},
        ),
    )
    captured: list[dict[str, object]] = []

    def _fake_incremental_commit(*_args, **kwargs):
        captured.append(dict(kwargs))
        return CommitResult(
            committed_ids=(keep.candidate_id,),
            reserved_route_cells=frozenset(),
            domain_version=1,
            conflicts=(),
            exterior_lane_assignments=(
                {"candidate_id": keep.candidate_id, "exterior_lane_id": plan.lanes[0].lane_id},
            ),
        )

    monkeypatch.setattr(
        local_lns,
        "generate_candidates",
        lambda *_a, **_k: SimpleNamespace(normal_candidates=()),
    )
    monkeypatch.setattr(
        local_lns,
        "select_genome",
        lambda pool, *_a, **_k: PlacementGenome(commit_order=tuple(c.candidate_id for c in pool)),
    )
    monkeypatch.setattr(local_lns, "initial_commit_domain", lambda *_a, **_k: object())
    monkeypatch.setattr(local_lns, "incremental_commit", _fake_incremental_commit)

    policy = RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED
    resource_kind = "shape"

    local_lns.run_local_lns(
        SimpleNamespace(),
        SimpleNamespace(),
        PlacementGenome(commit_order=(keep.candidate_id, conflicted.candidate_id)),
        candidates_by_id,
        primary,
        exterior_lane_plan=plan,
        route_probe_start_policy=policy,
        resource_kind=resource_kind,
    )

    assert captured, "incremental_commit should be invoked during LNS retry"
    for call_kwargs in captured:
        assert call_kwargs.get("exterior_lane_plan") is plan
        assert call_kwargs.get("route_probe_start_policy") is policy
        assert call_kwargs.get("resource_kind") == resource_kind


def test_local_lns_rejects_elcp_incomplete_conflict_free_early_exit(monkeypatch) -> None:
    """Run #238 regression: higher commit count without assignments must not win."""
    plan = _plan()
    keep = _candidate("keep", anchor=(10, 10))
    conflicted = _candidate("conflict", anchor=(0, 0))
    candidates_by_id = {keep.candidate_id: keep, conflicted.candidate_id: conflicted}
    primary = CommitResult(
        committed_ids=(keep.candidate_id,),
        reserved_route_cells=frozenset(),
        domain_version=1,
        conflicts=(
            CommitConflict(
                candidate_id=conflicted.candidate_id,
                reason=CommitConflictReason.REPROBE_FAILED,
            ),
        ),
        exterior_lane_assignments=(
            {"candidate_id": keep.candidate_id, "exterior_lane_id": plan.lanes[0].lane_id},
        ),
    )

    monkeypatch.setattr(
        local_lns,
        "generate_candidates",
        lambda *_a, **_k: SimpleNamespace(normal_candidates=()),
    )
    monkeypatch.setattr(
        local_lns,
        "select_genome",
        lambda pool, *_a, **_k: PlacementGenome(commit_order=tuple(c.candidate_id for c in pool)),
    )
    monkeypatch.setattr(local_lns, "initial_commit_domain", lambda *_a, **_k: object())
    monkeypatch.setattr(
        local_lns,
        "incremental_commit",
        lambda *_a, **_k: CommitResult(
            committed_ids=(keep.candidate_id, "extra1", "extra2"),
            reserved_route_cells=frozenset(),
            domain_version=3,
            conflicts=(),
            exterior_lane_assignments=(),
        ),
    )

    genome, final = local_lns.run_local_lns(
        SimpleNamespace(),
        SimpleNamespace(),
        PlacementGenome(commit_order=(keep.candidate_id, conflicted.candidate_id)),
        candidates_by_id,
        primary,
        exterior_lane_plan=plan,
        route_probe_start_policy=RouteProbeStartPolicy.OUTPUT_STUB_ONLY,
        resource_kind="shape",
    )

    assert final.committed_ids == primary.committed_ids
    assert final.exterior_lane_assignments == primary.exterior_lane_assignments
    assert genome.commit_order == (keep.candidate_id, conflicted.candidate_id)
