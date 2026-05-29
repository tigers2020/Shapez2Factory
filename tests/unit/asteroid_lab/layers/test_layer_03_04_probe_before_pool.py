"""Layer 03/04 candidate pool and transport kind contract tests (PR-3a)."""

from __future__ import annotations

from dataclasses import replace

import pytest

from django_apps.asteroid_lab.layers.contracts.candidates import (
    BundleCandidate,
    CandidateRejectReason,
    Layer03ExpansionMetrics,
    Layer03SkipReason,
    RouteProbedBundleCandidate,
    RouteProbeResult,
    RouteProbeStatus,
    build_rim_bundle_candidate_set,
    make_bundle_candidate_for_test,
)
from django_apps.asteroid_lab.layers.contracts.transport_kind import (
    ResourceKind,
    TransportKind,
    map_resource_kind_to_transport_kind,
    resource_kind_from_plan_string,
)


def test_map_resource_kind_to_transport_kind() -> None:
    assert map_resource_kind_to_transport_kind(ResourceKind.SHAPE) == TransportKind.SHAPE_BELT
    assert map_resource_kind_to_transport_kind(ResourceKind.FLUID) == TransportKind.FLUID_PIPE


def test_resource_kind_from_plan_string_shape_and_fluid() -> None:
    assert resource_kind_from_plan_string("shape") == ResourceKind.SHAPE
    assert resource_kind_from_plan_string("  FLUID ") == ResourceKind.FLUID


def test_resource_kind_from_plan_string_invalid_raises() -> None:
    with pytest.raises(ValueError, match="unknown plan transport_kind"):
        resource_kind_from_plan_string("water")


def _succeeded_probe(
    candidate: BundleCandidate,
    *,
    goal_coord: tuple[int, int] = (6, 4),
) -> RouteProbedBundleCandidate:
    start = candidate.route_probe_start_coord
    path = (start, (5, 4), goal_coord)
    return RouteProbedBundleCandidate(
        candidate=candidate,
        route_probe_status=RouteProbeStatus.SUCCEEDED,
        route_probe_result=RouteProbeResult(
            reached_goal=True,
            goal_coord=goal_coord,
            path_coords=path,
            steps_expanded=len(path),
            transport_kind=TransportKind.SHAPE_BELT,
        ),
        route_goal_id="ext_conn_00",
        reject_reason=None,
    )


def test_normal_candidates_type_requires_succeeded_status() -> None:
    candidate = make_bundle_candidate_for_test()
    with pytest.raises(ValueError, match="normal_candidates"):
        build_rim_bundle_candidate_set(
            normal_candidates=(
                RouteProbedBundleCandidate(
                    candidate=candidate,
                    route_probe_status=RouteProbeStatus.FAILED,
                    route_probe_result=None,
                    route_goal_id=None,
                    reject_reason=CandidateRejectReason.ROUTE_PROBE_FAILED,
                ),
            ),
            diagnostic_rejected_candidates=(),
            metrics=Layer03ExpansionMetrics.empty(),
        )


def test_unprobed_never_in_normal_pool() -> None:
    candidate = make_bundle_candidate_for_test()
    with pytest.raises(ValueError, match="SKIPPED_GEOMETRY"):
        build_rim_bundle_candidate_set(
            normal_candidates=(
                RouteProbedBundleCandidate(
                    candidate=candidate,
                    route_probe_status=RouteProbeStatus.SKIPPED_GEOMETRY,
                    route_probe_result=None,
                    route_goal_id=None,
                    reject_reason=CandidateRejectReason.LOCAL_GEOMETRY_INVALID,
                ),
            ),
            diagnostic_rejected_candidates=(),
            metrics=Layer03ExpansionMetrics.empty(),
        )


def test_route_probe_failed_goes_to_diagnostic_rejected_only() -> None:
    candidate = make_bundle_candidate_for_test()
    failed = RouteProbedBundleCandidate(
        candidate=candidate,
        route_probe_status=RouteProbeStatus.FAILED,
        route_probe_result=None,
        route_goal_id=None,
        reject_reason=CandidateRejectReason.ROUTE_PROBE_FAILED,
    )
    result = build_rim_bundle_candidate_set(
        normal_candidates=(),
        diagnostic_rejected_candidates=(failed,),
        metrics=replace(
            Layer03ExpansionMetrics.empty(),
            diagnostic_rejected_count=1,
            route_probe_failed_count=1,
        ),
    )
    assert len(result.normal_candidates) == 0
    assert len(result.diagnostic_rejected_candidates) == 1


def test_succeeded_requires_route_probe_result_and_goal_id() -> None:
    candidate = make_bundle_candidate_for_test()
    with pytest.raises(ValueError, match="route_probe_result"):
        RouteProbedBundleCandidate(
            candidate=candidate,
            route_probe_status=RouteProbeStatus.SUCCEEDED,
            route_probe_result=None,
            route_goal_id="ext_conn_00",
            reject_reason=None,
        )
    with pytest.raises(ValueError, match="route_goal_id"):
        RouteProbedBundleCandidate(
            candidate=candidate,
            route_probe_status=RouteProbeStatus.SUCCEEDED,
            route_probe_result=RouteProbeResult(
                reached_goal=True,
                goal_coord=(6, 4),
                path_coords=((5, 4), (6, 4)),
                steps_expanded=2,
                transport_kind=TransportKind.SHAPE_BELT,
            ),
            route_goal_id=None,
            reject_reason=None,
        )


def test_succeeded_validates_path_endpoints() -> None:
    candidate = make_bundle_candidate_for_test(route_probe_start_coord=(5, 4))
    with pytest.raises(ValueError, match="path_coords\\[0\\]"):
        RouteProbedBundleCandidate(
            candidate=candidate,
            route_probe_status=RouteProbeStatus.SUCCEEDED,
            route_probe_result=RouteProbeResult(
                reached_goal=True,
                goal_coord=(6, 4),
                path_coords=((9, 9), (6, 4)),
                steps_expanded=2,
                transport_kind=TransportKind.SHAPE_BELT,
            ),
            route_goal_id="ext_conn_00",
            reject_reason=None,
        )
    with pytest.raises(ValueError, match="path_coords\\[-1\\]"):
        RouteProbedBundleCandidate(
            candidate=candidate,
            route_probe_status=RouteProbeStatus.SUCCEEDED,
            route_probe_result=RouteProbeResult(
                reached_goal=True,
                goal_coord=(6, 4),
                path_coords=((5, 4), (9, 9)),
                steps_expanded=2,
                transport_kind=TransportKind.SHAPE_BELT,
            ),
            route_goal_id="ext_conn_00",
            reject_reason=None,
        )


def test_build_rim_bundle_candidate_set_accepts_valid_succeeded() -> None:
    candidate = make_bundle_candidate_for_test()
    probed = _succeeded_probe(candidate)
    metrics = replace(
        Layer03ExpansionMetrics.empty(),
        normal_candidate_count=1,
        route_probe_attempt_count=1,
        route_probe_succeeded_count=1,
    )
    result = build_rim_bundle_candidate_set(
        normal_candidates=(probed,),
        diagnostic_rejected_candidates=(),
        metrics=metrics,
    )
    assert len(result.normal_candidates) == 1
    assert result.metrics.normal_candidate_count == 1


def test_succeeded_must_not_appear_in_diagnostic_pool() -> None:
    candidate = make_bundle_candidate_for_test()
    probed = _succeeded_probe(candidate)
    with pytest.raises(ValueError, match="diagnostic_rejected_candidates"):
        build_rim_bundle_candidate_set(
            normal_candidates=(),
            diagnostic_rejected_candidates=(probed,),
            metrics=Layer03ExpansionMetrics.empty(),
        )


def test_layer03_expansion_metrics_empty_factory() -> None:
    metrics = Layer03ExpansionMetrics.empty()
    assert metrics.layer_skip_reason == Layer03SkipReason.NONE
    assert metrics.rim_anchor_count == 0
    assert metrics.normal_candidate_count == 0


def test_equivalence_key_ignores_gene_key_on_candidates() -> None:
    from django_apps.asteroid_lab.genetic_sample.enums import Direction
    from django_apps.asteroid_lab.layers.shared.equivalence_key import (
        build_equivalence_key_from_candidate,
    )

    shared = dict(
        equivalence_key="placeholder",
        throughput_factor=16,
        route_probe_start_coord=(5, 4),
        mining_occupied_cells=frozenset({(3, 4), (4, 4)}),
        transport_stub_cells=frozenset({(5, 4)}),
        topology_signature="topo_a",
        output_dir=Direction.E,
    )
    cand_a = make_bundle_candidate_for_test(gene_key="miner_seed_m3e_01", **shared)
    cand_b = make_bundle_candidate_for_test(gene_key="miner_seed_m1e_01", **shared)
    assert cand_a.candidate_id != cand_b.candidate_id
    assert build_equivalence_key_from_candidate(cand_a) == build_equivalence_key_from_candidate(
        cand_b
    )


def test_immediate_route_probe_reaches_nearest_priority_goal() -> None:
    from django_apps.asteroid_lab.layers.contracts.exterior_connector_role import (
        ExteriorConnectorRole,
    )
    from django_apps.asteroid_lab.layers.contracts.route_goal import RouteGoal, RouteGoalKind
    from django_apps.asteroid_lab.layers.shared.route_probe import immediate_route_probe

    void_cells = frozenset({(5, 4), (6, 4), (7, 4), (8, 4)})
    candidate = make_bundle_candidate_for_test(route_probe_start_coord=(5, 4))
    goals = (
        RouteGoal(
            goal_id="ext_conn_far",
            kind=RouteGoalKind.EXTERIOR_CONNECTOR_VOID,
            coord=(8, 4),
            transport_kind=TransportKind.SHAPE_BELT,
            priority=10,
            connector_role=ExteriorConnectorRole.SPARE,
        ),
        RouteGoal(
            goal_id="ext_conn_near",
            kind=RouteGoalKind.EXTERIOR_CONNECTOR_VOID,
            coord=(6, 4),
            transport_kind=TransportKind.SHAPE_BELT,
            priority=0,
            connector_role=ExteriorConnectorRole.REQUIRED,
        ),
    )
    probed = immediate_route_probe(
        candidate=candidate,
        route_goals=goals,
        placeable_cells=void_cells,
    )
    assert probed.route_probe_status == RouteProbeStatus.SUCCEEDED
    assert probed.route_probe_result is not None
    assert probed.route_goal_id == "ext_conn_near"
    assert probed.route_probe_result.path_coords[0] == candidate.route_probe_start_coord
    assert probed.route_probe_result.path_coords[-1] == probed.route_probe_result.goal_coord


def test_immediate_route_probe_failed_when_unreachable() -> None:
    from django_apps.asteroid_lab.layers.contracts.exterior_connector_role import (
        ExteriorConnectorRole,
    )
    from django_apps.asteroid_lab.layers.contracts.route_goal import RouteGoal, RouteGoalKind
    from django_apps.asteroid_lab.layers.shared.route_probe import immediate_route_probe

    candidate = make_bundle_candidate_for_test(route_probe_start_coord=(5, 4))
    goals = (
        RouteGoal(
            goal_id="ext_conn_isolated",
            kind=RouteGoalKind.EXTERIOR_CONNECTOR_VOID,
            coord=(99, 99),
            transport_kind=TransportKind.SHAPE_BELT,
            priority=0,
            connector_role=ExteriorConnectorRole.REQUIRED,
        ),
    )
    probed = immediate_route_probe(
        candidate=candidate,
        route_goals=goals,
        placeable_cells=frozenset({(5, 4)}),
    )
    assert probed.route_probe_status == RouteProbeStatus.FAILED
    assert probed.route_probe_result is None
    assert probed.reject_reason == CandidateRejectReason.EXTERIOR_CONNECTOR_UNREACHABLE


def test_probe_start_not_in_traversable_returns_exterior_entry_not_reachable() -> None:
    from django_apps.asteroid_lab.layers.contracts.exterior_connector_role import (
        ExteriorConnectorRole,
    )
    from django_apps.asteroid_lab.layers.contracts.route_goal import RouteGoal, RouteGoalKind
    from django_apps.asteroid_lab.layers.shared.route_probe import immediate_route_probe

    candidate = make_bundle_candidate_for_test(route_probe_start_coord=(5, 4))
    goals = (
        RouteGoal(
            goal_id="ext_conn_far",
            kind=RouteGoalKind.EXTERIOR_CONNECTOR_VOID,
            coord=(99, 99),
            transport_kind=TransportKind.SHAPE_BELT,
            priority=0,
            connector_role=ExteriorConnectorRole.REQUIRED,
        ),
    )
    probed = immediate_route_probe(
        candidate=candidate,
        route_goals=goals,
        placeable_cells=frozenset(),
    )
    assert probed.route_probe_status == RouteProbeStatus.FAILED
    assert probed.reject_reason == CandidateRejectReason.EXTERIOR_ENTRY_NOT_REACHABLE


def test_route_probe_result_proposed_transport_cells_unions_stub_and_path() -> None:
    stubs = frozenset({(5, 5), (6, 5)})
    result = RouteProbeResult(
        reached_goal=True,
        goal_coord=(8, 5),
        path_coords=((5, 5), (6, 5), (7, 5), (8, 5)),
        steps_expanded=3,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    proposed = result.proposed_transport_cells(stub_cells=stubs)
    assert proposed == frozenset({(5, 5), (6, 5), (7, 5), (8, 5)})
