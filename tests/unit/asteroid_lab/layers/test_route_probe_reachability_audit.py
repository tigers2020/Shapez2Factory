"""PR-C: route probe reachability audit — split exterior goal failures."""

from __future__ import annotations

import inspect

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    CandidateRejectReason,
    RouteProbeStatus,
    make_bundle_candidate_for_test,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.exterior_connector_role import (
    ExteriorConnectorRole,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.route_goal import (
    RouteGoal,
    RouteGoalKind,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.transport_kind import (
    TransportKind,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.weighted_transport_route_domain import (  # noqa: E501
    WeightedTransportRouteDomain,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement import (
    commit_reprobe,
)
from shapez2_factory.application.asteroid_lab.layers.shared import route_probe
from shapez2_factory.application.asteroid_lab.layers.shared.route_probe import (
    immediate_route_probe,
    weighted_route_probe,
)


def _shape_goal(*, goal_id: str, coord: tuple[int, int]) -> RouteGoal:
    return RouteGoal(
        goal_id=goal_id,
        kind=RouteGoalKind.EXTERIOR_CONNECTOR_VOID,
        coord=coord,
        transport_kind=TransportKind.SPACE_BELT,
        priority=0,
        connector_role=ExteriorConnectorRole.REQUIRED,
    )


def _void_line(*, length: int, y: int = 0) -> frozenset[tuple[int, int]]:
    return frozenset((x, y) for x in range(length))


def _line_candidate(
    *,
    anchor: tuple[int, int],
    stub: tuple[int, int],
) -> object:
    return make_bundle_candidate_for_test(
        anchor_coord=anchor,
        route_probe_start_coord=stub,
        transport_stub_cells=frozenset({stub}),
        mining_occupied_cells=frozenset({anchor}),
    )


def test_unreachable_splits_probe_limit_hit(monkeypatch) -> None:
    monkeypatch.setattr(route_probe, "LAYER03_ROUTE_PROBE_MAX_PATH_CELLS", 8)
    void = _void_line(length=20)
    start = (1, 0)
    goal_coord = (19, 0)
    candidate = _line_candidate(anchor=(0, 0), stub=start)
    domain = WeightedTransportRouteDomain(
        search_bbox=(0, 0, 19, 0),
        blocked_cells=frozenset(),
        walkable_cells=void,
        field_cost_cells=frozenset(),
    )
    result = weighted_route_probe(
        candidate=candidate,
        route_goals=(_shape_goal(goal_id="g_far", coord=goal_coord),),
        domain=domain,
        field_cells=frozenset(),
        external_void_cells=void,
    )
    assert result.route_probe_status is RouteProbeStatus.FAILED
    assert result.reject_reason is CandidateRejectReason.EXTERIOR_GOAL_UNREACHABLE_PROBE_LIMIT_HIT
    assert result.route_probe_diagnostic is not None
    assert result.route_probe_diagnostic.probe_limit_hit is True
    assert (
        result.route_probe_diagnostic.detailed_unreachable_reason
        == CandidateRejectReason.EXTERIOR_GOAL_UNREACHABLE_PROBE_LIMIT_HIT.value
    )


def test_unreachable_splits_no_same_component_goal() -> None:
    west_void = frozenset({(0, 0), (1, 0)})
    east_void = frozenset({(8, 0), (9, 0)})
    external_void = west_void | east_void
    walkable = west_void
    candidate = _line_candidate(anchor=(0, 0), stub=(1, 0))
    domain = WeightedTransportRouteDomain(
        search_bbox=(0, 0, 9, 0),
        blocked_cells=frozenset(),
        walkable_cells=walkable,
        field_cost_cells=frozenset(),
    )
    result = weighted_route_probe(
        candidate=candidate,
        route_goals=(_shape_goal(goal_id="g_east", coord=(9, 0)),),
        domain=domain,
        field_cells=frozenset(),
        external_void_cells=external_void,
    )
    assert result.reject_reason is (
        CandidateRejectReason.EXTERIOR_GOAL_UNREACHABLE_NO_SAME_VOID_COMPONENT
    )
    diag = result.route_probe_diagnostic
    assert diag is not None
    assert diag.same_void_component_goal_count == 0
    assert diag.stub_component_id != diag.goal_component_ids[0]


def test_empty_map_reachable_when_goal_same_component() -> None:
    void = frozenset({(0, 0), (1, 0), (2, 0), (3, 0)})
    start = (1, 0)
    goal = (3, 0)
    candidate = _line_candidate(anchor=(0, 0), stub=start)
    domain = WeightedTransportRouteDomain(
        search_bbox=(0, 0, 3, 0),
        blocked_cells=frozenset(),
        walkable_cells=void,
        field_cost_cells=frozenset(),
    )
    result = weighted_route_probe(
        candidate=candidate,
        route_goals=(_shape_goal(goal_id="g_near", coord=goal),),
        domain=domain,
        field_cells=frozenset(),
        external_void_cells=void,
    )
    assert result.route_probe_status is RouteProbeStatus.SUCCEEDED
    assert result.route_probe_diagnostic is None


def test_corridor_share_not_hard_block() -> None:
    source = inspect.getsource(commit_reprobe.try_commit_reprobe)
    blockers_line = next(
        line for line in source.splitlines() if line.strip().startswith("blockers =")
    )
    assert blockers_line.strip() == "blockers = frozenset(state.occupied | set(own_equipment))"
    assert "state.corridor" not in blockers_line


def test_goal_count_not_miner_cap() -> None:
    void = frozenset(
        {
            (0, 0),
            (1, 0),
            (2, 0),
            (3, 0),
            (4, 0),
            (0, 1),
            (1, 1),
            (2, 1),
            (3, 1),
            (4, 1),
        }
    )
    goal = (4, 0)
    goals = (_shape_goal(goal_id="shared_trunk", coord=goal),)
    domain = WeightedTransportRouteDomain(
        search_bbox=(0, 0, 4, 0),
        blocked_cells=frozenset(),
        walkable_cells=void,
        field_cost_cells=frozenset(),
    )
    first = _line_candidate(anchor=(0, 0), stub=(1, 0))
    second = _line_candidate(anchor=(0, 1), stub=(1, 1))
    r1 = weighted_route_probe(
        candidate=first,
        route_goals=goals,
        domain=domain,
        field_cells=frozenset(),
        external_void_cells=void,
    )
    r2 = weighted_route_probe(
        candidate=second,
        route_goals=goals,
        domain=domain,
        field_cells=frozenset(),
        external_void_cells=void,
    )
    assert r1.route_probe_status is RouteProbeStatus.SUCCEEDED
    assert r2.route_probe_status is RouteProbeStatus.SUCCEEDED
    assert r1.route_probe_result is not None
    assert r2.route_probe_result is not None
    assert r1.route_probe_result.goal_coord == goal
    assert r2.route_probe_result.goal_coord == goal


def test_no_matching_goals_emits_no_goals_reason() -> None:
    void = _void_line(length=5)
    candidate = _line_candidate(anchor=(0, 0), stub=(1, 0))
    domain = WeightedTransportRouteDomain(
        search_bbox=(0, 0, 4, 0),
        blocked_cells=frozenset(),
        walkable_cells=void,
        field_cost_cells=frozenset(),
    )
    fluid_goal = RouteGoal(
        goal_id="fluid_only",
        kind=RouteGoalKind.EXTERIOR_CONNECTOR_VOID,
        coord=(4, 0),
        transport_kind=TransportKind.SPACE_PIPE,
        priority=0,
        connector_role=ExteriorConnectorRole.REQUIRED,
    )
    result = weighted_route_probe(
        candidate=candidate,
        route_goals=(fluid_goal,),
        domain=domain,
        field_cells=frozenset(),
        external_void_cells=void,
    )
    assert result.reject_reason is CandidateRejectReason.EXTERIOR_GOAL_UNREACHABLE_NO_GOALS
    assert result.route_probe_diagnostic is not None
    assert (
        result.route_probe_diagnostic.detailed_unreachable_reason
        == CandidateRejectReason.EXTERIOR_GOAL_UNREACHABLE_NO_GOALS.value
    )


def test_route_probe_module_never_emits_legacy_connector_unreachable() -> None:
    source = inspect.getsource(route_probe)
    assert "EXTERIOR_CONNECTOR_UNREACHABLE" not in source


def test_immediate_route_probe_emits_diagnostic_on_frontier_exhausted() -> None:
    walkable = frozenset({(0, 0), (1, 0), (2, 0)})
    external_void = frozenset({(0, 0), (1, 0), (2, 0), (4, 0)})
    candidate = _line_candidate(anchor=(0, 0), stub=(1, 0))
    result = immediate_route_probe(
        candidate=candidate,
        route_goals=(_shape_goal(goal_id="blocked_goal", coord=(4, 0)),),
        placeable_cells=walkable,
        external_void_cells=external_void,
    )
    assert result.reject_reason in {
        CandidateRejectReason.EXTERIOR_GOAL_UNREACHABLE_NO_SAME_VOID_COMPONENT,
        CandidateRejectReason.EXTERIOR_GOAL_UNREACHABLE_FRONTIER_EXHAUSTED,
    }
    assert result.route_probe_diagnostic is not None
