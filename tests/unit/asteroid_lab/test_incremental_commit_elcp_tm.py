"""ELCP-TM Task 4 — incremental_commit trunk-merge path (fill-first + partition)."""

from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from django_apps.asteroid_lab.contracts.exterior_lane_capacity import (
    ACTIVATION_REASON_CAPACITY_EXHAUSTED,
    ExteriorLaneCapacityPlan,
    ExteriorTransportLane,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import (
    BundleCandidate,
    ExtractorPlacementPolicy,
    FixedOutputTransportPolicy,
    RouteProbeStartPolicy,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_generator import (
    generate_candidates,
)
from django_apps.asteroid_lab.optimization.candidates.pattern_library import build_pattern_library
from django_apps.asteroid_lab.optimization.commit.incremental_commit import (
    _candidate_throughput_per_min,
    incremental_commit,
    initial_commit_domain,
)
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RouteGoal,
    RouteGoalKind,
    RttpSkeletonConfig,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.selection.greedy_regret import PlacementGenome
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder
from tests.support.catalog_test_fixtures import build_minimal_test_catalog_slice
from tests.support.rttp_narrow_corridor_fixture import (
    NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID,
    build_narrow_corridor_optimization_input,
    candidate_by_id,
)


def _goal(coord: tuple[int, int], *, priority: int = 20) -> RouteGoal:
    return RouteGoal(
        coord=coord,
        goal_kind=RouteGoalKind.EXTERNAL_MARGIN,
        transport_kind=TransportKind.SHAPE_BELT,
        priority=priority,
        existing_trunk=False,
    )


def _lane(
    lane_id: str,
    coord: tuple[int, int],
    *,
    capacity: Decimal = Decimal("2880"),
    priority: int = 20,
) -> ExteriorTransportLane:
    goal = _goal(coord, priority=priority)
    return ExteriorTransportLane(
        lane_id=lane_id,
        transport_kind=TransportKind.SHAPE_BELT,
        connector_goal=goal,
        capacity_per_min=capacity,
        target_load_per_min=capacity,
        anchor_coord=coord,
    )


def _plan(*lanes: ExteriorTransportLane) -> ExteriorLaneCapacityPlan:
    cap = lanes[0].capacity_per_min if lanes else Decimal("2880")
    return ExteriorLaneCapacityPlan(
        transport_kind=TransportKind.SHAPE_BELT,
        max_asteroid_throughput_per_min=cap * Decimal(len(lanes) or 1),
        lane_capacity_per_min=cap,
        required_lane_count=len(lanes),
        lanes=lanes,
    )


def _micro_skeleton() -> RttpSkeleton:
    return RttpSkeleton(
        ring_cells=frozenset(),
        ring_ports=(),
        lift_columns=(),
        trunk_mask_cells=frozenset({(0, 0)}),
        capacity_goals=1,
        inner_cells=frozenset(),
        skeleton_id="elcp-tm-micro",
    )


def _lin_e_pattern():
    for pattern in build_pattern_library():
        if pattern.pattern_id == "lin_e_len0":
            return pattern
    msg = "lin_e_len0 not found"
    raise AssertionError(msg)


def _synthetic_candidate(
    candidate_id: str,
    *,
    output_stub: tuple[int, int] = (2, 0),
    throughput_factor: int = 4,
) -> BundleCandidate:
    pattern = _lin_e_pattern()
    return BundleCandidate(
        candidate_id=candidate_id,
        anchor_coord=(0, 0),
        pattern=pattern,
        output_stub=output_stub,
        output_dir=pattern.output_dir,
        occupied_cells=frozenset({(0, 0)}),
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=throughput_factor,
        route_probe_cost=5,
        reachable=True,
    )


def _narrow_inp_with_catalog() -> OptimizationInput:
    return replace(
        build_narrow_corridor_optimization_input(),
        catalog_slice=build_minimal_test_catalog_slice(),
    )


def _narrow_skeleton_domain(
    inp: OptimizationInput,
) -> tuple[object, object]:
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    domain = initial_commit_domain(skeleton, inp)
    return skeleton, domain


@pytest.mark.django_db
def test_two_miners_same_lane_share_trunk_cells(
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    plan = _plan(_lane("exterior_lane:shape_belt:0", (2, 0)))
    inp = OptimizationInput(
        mineable_cells=frozenset(),
        rim_cells=frozenset(),
        inner_cells=frozenset(),
        external_void_cells=frozenset(
            {(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)}
        ),
        protected_corridor_cells=frozenset(),
        existing_trunk_cells=frozenset(),
        transport_kind=TransportKind.SHAPE_BELT,
        route_goals=(_goal((2, 0)),),
        existing_transport_cells=frozenset(),
        catalog_slice=None,
    )
    skeleton = _micro_skeleton()
    domain = initial_commit_domain(skeleton, inp)
    c1 = _synthetic_candidate("c_tm_share_a")
    c2 = replace(
        _synthetic_candidate("c_tm_share_b"),
        anchor_coord=(0, 1),
        occupied_cells=frozenset({(0, 1)}),
        output_stub=(2, 1),
    )
    result = incremental_commit(
        PlacementGenome(commit_order=("c_tm_share_a", "c_tm_share_b")),
        {"c_tm_share_a": c1, "c_tm_share_b": c2},
        inp,
        skeleton,
        domain=domain,
        exterior_lane_plan=plan,
        resource_kind="shape",
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    assert len(result.committed_ids) == 2
    trunk_union: set[tuple[int, int]] = set()
    for row in result.exterior_lane_trunk_states:
        if row.active:
            trunk_union.update(row.trunk_cells)
    assert (2, 0) in trunk_union
    assert not any(c.reason.value == "route_cell_conflict" for c in result.conflicts)


@pytest.mark.django_db
def test_second_miner_reuses_trunk_and_reserves_branch_only(
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    plan = _plan(_lane("exterior_lane:shape_belt:0", (2, 0)))
    inp = OptimizationInput(
        mineable_cells=frozenset(),
        rim_cells=frozenset(),
        inner_cells=frozenset(),
        external_void_cells=frozenset(
            {(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)}
        ),
        protected_corridor_cells=frozenset(),
        existing_trunk_cells=frozenset(),
        transport_kind=TransportKind.SHAPE_BELT,
        route_goals=(_goal((2, 0)),),
        existing_transport_cells=frozenset(),
        catalog_slice=None,
    )
    skeleton = _micro_skeleton()
    domain = initial_commit_domain(skeleton, inp)
    c1 = _synthetic_candidate("c_tm_branch_a")
    c2 = replace(
        _synthetic_candidate("c_tm_branch_b"),
        anchor_coord=(0, 1),
        occupied_cells=frozenset({(0, 1)}),
        output_stub=(2, 1),
    )
    result = incremental_commit(
        PlacementGenome(commit_order=("c_tm_branch_a", "c_tm_branch_b")),
        {"c_tm_branch_a": c1, "c_tm_branch_b": c2},
        inp,
        skeleton,
        domain=domain,
        exterior_lane_plan=plan,
        resource_kind="shape",
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    assert len(result.committed_ids) == 2
    assert len(result.exterior_lane_route_evidence) == 2
    ev0, ev1 = result.exterior_lane_route_evidence
    assert ev0.lane_id == ev1.lane_id
    assert ev1.new_trunk_cells == ()


@pytest.mark.django_db
def test_lane0_capacity_unreachable_does_not_activate_lane1_in_commit(
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    inp = OptimizationInput(
        mineable_cells=frozenset(),
        rim_cells=frozenset(),
        inner_cells=frozenset(),
        external_void_cells=frozenset({(0, 0), (1, 0), (2, 0), (0, 1)}),
        protected_corridor_cells=frozenset(),
        existing_trunk_cells=frozenset(),
        transport_kind=TransportKind.SHAPE_BELT,
        route_goals=(
            _goal((999, 999)),
            _goal((0, 1)),
        ),
        existing_transport_cells=frozenset(),
        catalog_slice=None,
    )
    skeleton = _micro_skeleton()
    plan = _plan(
        _lane("exterior_lane:shape_belt:0", (999, 999)),
        _lane("exterior_lane:shape_belt:1", (0, 1)),
    )
    c1 = _synthetic_candidate("c_tm_unreachable")
    domain = initial_commit_domain(skeleton, inp)
    result = incremental_commit(
        PlacementGenome(commit_order=("c_tm_unreachable",)),
        {"c_tm_unreachable": c1},
        inp,
        skeleton,
        domain=domain,
        exterior_lane_plan=plan,
        resource_kind="shape",
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    assert result.committed_ids == ()
    assert result.exterior_lane_activations == ()
    lane1 = next(
        s for s in result.exterior_lane_trunk_states if s.lane_id == "exterior_lane:shape_belt:1"
    )
    assert lane1.active is False


@pytest.mark.django_db
def test_lane0_saturated_activates_lane1_in_commit(
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    c1 = _synthetic_candidate("c_tm_sat_a", throughput_factor=4)
    c2 = replace(
        _synthetic_candidate("c_tm_sat_b", throughput_factor=4),
        anchor_coord=(0, 1),
        occupied_cells=frozenset({(0, 1)}),
        output_stub=(2, 1),
    )
    inp = OptimizationInput(
        mineable_cells=frozenset(),
        rim_cells=frozenset(),
        inner_cells=frozenset(),
        external_void_cells=frozenset({(0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (2, 1)}),
        protected_corridor_cells=frozenset(),
        existing_trunk_cells=frozenset(),
        transport_kind=TransportKind.SHAPE_BELT,
        route_goals=(_goal((2, 0)), _goal((1, 0))),
        existing_transport_cells=frozenset(),
        catalog_slice=None,
    )
    skeleton = _micro_skeleton()
    domain = initial_commit_domain(skeleton, inp)
    t1 = _candidate_throughput_per_min(c1, resource_kind="shape")
    t2 = _candidate_throughput_per_min(c2, resource_kind="shape")
    lane_cap = t1 + Decimal("10")
    if t2 <= Decimal("15"):
        pytest.skip("second candidate throughput too low to exhaust lane0 headroom")
    plan = _plan(
        _lane("exterior_lane:shape_belt:0", (2, 0), capacity=lane_cap),
        _lane("exterior_lane:shape_belt:1", (1, 0), capacity=lane_cap),
    )
    result = incremental_commit(
        PlacementGenome(commit_order=("c_tm_sat_a", "c_tm_sat_b")),
        {"c_tm_sat_a": c1, "c_tm_sat_b": c2},
        inp,
        skeleton,
        domain=domain,
        exterior_lane_plan=plan,
        resource_kind="shape",
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    assert "c_tm_sat_a" in result.committed_ids
    assert "c_tm_sat_b" in result.committed_ids
    assert result.exterior_lane_activations
    act0 = result.exterior_lane_activations[0]
    assert act0.activation_reason == ACTIVATION_REASON_CAPACITY_EXHAUSTED
    assert act0.activated_lane_id == "exterior_lane:shape_belt:1"


@pytest.mark.django_db
def test_exterior_lane_plan_none_preserves_legacy_commit_behavior(
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    inp = _narrow_inp_with_catalog()
    skeleton, domain = _narrow_skeleton_domain(inp)
    gen = generate_candidates(
        inp,
        skeleton,
        policy=ExtractorPlacementPolicy.INTERIOR_AND_RIM,
        fixed_output_transport_policy=FixedOutputTransportPolicy.OUTSIDE_MINEABLE,
    )
    first = candidate_by_id(gen, NARROW_CORRIDOR_PROBE_FIRST_CANDIDATE_ID)
    by_id = {first.candidate_id: first}
    result = incremental_commit(
        PlacementGenome(commit_order=(first.candidate_id,)),
        by_id,
        inp,
        skeleton,
        domain=domain,
        exterior_lane_plan=None,
    )
    assert result.exterior_lane_trunk_states == ()
    assert result.exterior_lane_route_evidence == ()
    assert result.exterior_lane_activations == ()
    assert result.exterior_lane_assignments == ()
    assert first.candidate_id in result.committed_ids or result.conflicts


@pytest.mark.django_db
def test_output_spine_stops_at_shareable_trunk_attachment(
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    void_cells = frozenset({(0, 0), (1, 0), (2, 0), (3, 0), (4, 0)})
    plan = _plan(_lane("exterior_lane:shape_belt:0", (3, 0)))
    c1 = _synthetic_candidate("c_tm_spine")
    inp = OptimizationInput(
        mineable_cells=frozenset(),
        rim_cells=frozenset(),
        inner_cells=frozenset(),
        external_void_cells=void_cells,
        protected_corridor_cells=frozenset(),
        existing_trunk_cells=frozenset(),
        transport_kind=TransportKind.SHAPE_BELT,
        route_goals=(_goal((3, 0)),),
        existing_transport_cells=frozenset(),
        catalog_slice=None,
    )
    skeleton = _micro_skeleton()
    domain = initial_commit_domain(skeleton, inp)
    result = incremental_commit(
        PlacementGenome(commit_order=("c_tm_spine",)),
        {"c_tm_spine": c1},
        inp,
        skeleton,
        domain=domain,
        exterior_lane_plan=plan,
        resource_kind="shape",
        route_probe_start_policy=RouteProbeStartPolicy.PLATFORM_FALLBACK_WHEN_STUB_BLOCKED,
    )
    assert "c_tm_spine" in result.committed_ids
    assert (4, 0) not in result.reserved_route_cells
