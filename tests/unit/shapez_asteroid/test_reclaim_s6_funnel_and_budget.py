"""§12.6 S6 reclaim funnel, mineable_cur exclusions, budget floor, stub-inclusive route cost."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.boundary import (
    cells_touching_void,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    MIN_INTERNAL_TRANSPORT_SPEND_WHEN_NO_PASS3_SAVINGS,
    P4_REJECT_GAIN_RATIO,
    P4_REJECT_INTERNAL_TRANSPORT_BUDGET,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_greedy_core import (
    mining_priority_route_cell_cost,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_map_ops import (
    _allowed_internal_transport_budget,
    _mineable_cur_for_reclaim,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_p4_bundle import (
    _p4_bundle_eval,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_route_metrics import (  # noqa: E501
    _path_additional_route_cost_detail,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow_scan import (  # noqa: E501
    _p4_reclaim_candidate_funnel_trace,
)


def test_mineable_cur_excludes_final_route_hard_soft_committed() -> None:
    base = frozenset({(1, 1), (2, 1), (3, 1), (4, 1)})
    final_route = frozenset({(1, 1)})
    hard = frozenset({(2, 1)})
    soft = frozenset({(3, 1)})
    committed = frozenset({(4, 1)})
    cur = _mineable_cur_for_reclaim(
        base,
        final_route_cells=final_route,
        hard_protected_corridors=hard,
        soft_protected_corridors=soft,
        committed_building_cells=committed,
    )
    assert cur == frozenset()


def test_soft_corridor_cell_reenters_mineable_when_not_in_active_soft_pool() -> None:
    """``soft_protected_corridors`` passed to reclaim is active-on-map only (caller contract)."""

    base = frozenset({(1, 1), (2, 1)})
    cur = _mineable_cur_for_reclaim(
        base,
        final_route_cells=frozenset(),
        hard_protected_corridors=frozenset(),
        soft_protected_corridors=frozenset({(1, 1)}),
        committed_building_cells=frozenset(),
    )
    assert cur == frozenset({(2, 1)})
    cur_after_release = _mineable_cur_for_reclaim(
        base,
        final_route_cells=frozenset(),
        hard_protected_corridors=frozenset(),
        soft_protected_corridors=frozenset(),
        committed_building_cells=frozenset(),
    )
    assert cur_after_release == base


def test_allowed_internal_transport_budget_uses_floor_when_pass3_saved_zero() -> None:
    assert (
        _allowed_internal_transport_budget(0) == MIN_INTERNAL_TRANSPORT_SPEND_WHEN_NO_PASS3_SAVINGS
    )
    assert (
        _allowed_internal_transport_budget(-3) == MIN_INTERNAL_TRANSPORT_SPEND_WHEN_NO_PASS3_SAVINGS
    )


def test_path_additional_route_cost_includes_output_stub_cell() -> None:
    path = [(0, 0), (1, 0), (2, 0)]
    ast = {(0, 0), (1, 0), (2, 0)}
    mine = {(0, 0), (1, 0), (2, 0)}
    b: dict = {}
    tc = {(0, 0): "belt"}
    fixed = frozenset({(0, 0)})
    outlet = (0, 0)
    tot, first, rest = _path_additional_route_cost_detail(
        path,
        asteroid_cells=ast,
        mineable_cells=mine,
        buildings=b,
        transport_cells=tc,
        fixed_stubs=fixed,
        outlet_stub=outlet,
    )
    assert first + rest == tot
    route_tree = {c for c in tc if c != outlet}
    boundary = cells_touching_void(set(ast))
    stub_ec = mining_priority_route_cell_cost(
        outlet,
        asteroid_cells=ast,
        mineable_cells=mine,
        boundary_cells=boundary,
        buildings=b,
        fixed_stubs=frozenset(),
        route_tree=route_tree,
        opportunity_score={},
        route_zone_map=None,
    )
    ec1 = mining_priority_route_cell_cost(
        (1, 0),
        asteroid_cells=ast,
        mineable_cells=mine,
        boundary_cells=boundary,
        buildings=b,
        fixed_stubs=fixed,
        route_tree=route_tree,
        opportunity_score={},
        route_zone_map=None,
    )
    ec2 = mining_priority_route_cell_cost(
        (2, 0),
        asteroid_cells=ast,
        mineable_cells=mine,
        boundary_cells=boundary,
        buildings=b,
        fixed_stubs=fixed,
        route_tree=route_tree,
        opportunity_score={},
        route_zone_map=None,
    )
    assert tot == stub_ec + ec1 + ec2
    assert first == stub_ec + ec1


def test_reclaim_shadow_scan_trace_includes_funnel_and_pass3_budget_key() -> None:
    import copy

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_shadow_scan import (  # noqa: E501
        reclaim_shadow_scan_core_after_pass3,
    )
    from tests.unit.shapez_asteroid.test_reclaim_shadow import (
        _base_final_mining_map,
        _external_east,
        _minimal_routed_shape_map,
    )

    m0 = copy.deepcopy(_minimal_routed_shape_map(include_orphan_belt_at_8_4=False))
    fm = list(_base_final_mining_map())
    r = reclaim_shadow_scan_core_after_pass3(
        copy.deepcopy(m0),
        copy.deepcopy(m0),
        final_mining_map=fm,
        is_external=_external_east,
        pass3_trace={"pass3_internal_transport_saved": 50},
    )
    tr = r.trace
    if tr.get("p4_reclaim_shadow_enabled") and not tr.get("p4_reclaim_shadow_skip_reason"):
        assert "mineable_cur_before_protection" in tr
        assert "mineable_cur_after_protection" in tr
        assert "candidate_scan_count" in tr
        assert "candidate_reject_by_reason" in tr
        assert "pass3_internal_transport_saved_for_reclaim_budget" in tr
        assert int(tr["pass3_internal_transport_saved_for_reclaim_budget"]) >= 0


def test_p4_reclaim_candidate_funnel_trace_histogram() -> None:
    a = _p4_bundle_eval(
        gain=1.0,
        additional_route_cost=1.0,
        gain_ratio=1.0,
        incremental_internal_transport_added=0,
        rejected_reason=P4_REJECT_GAIN_RATIO,
        accepted_shadow=False,
        anchor=(1, 1),
        extension=(2, 1),
        rotation=0,
    )
    b = _p4_bundle_eval(
        gain=1.0,
        additional_route_cost=1.0,
        gain_ratio=9.0,
        incremental_internal_transport_added=2,
        rejected_reason=P4_REJECT_INTERNAL_TRANSPORT_BUDGET,
        accepted_shadow=False,
        anchor=(3, 1),
        extension=(4, 1),
        rotation=0,
    )
    d = _p4_reclaim_candidate_funnel_trace(
        [a, b],
        mineable_cur_before_protection=10,
        mineable_cur_after_protection=4,
        final_route_cells_excluded_count=1,
        hard_protected_excluded_count=2,
        soft_protected_excluded_count=3,
        internal_budget=5,
        spent_prior=1,
    )
    assert d["candidate_scan_count"] == 2
    assert d["gain_ratio_reject_count"] == 1
    assert d["internal_budget_reject_count"] == 1
    assert d["candidate_reject_by_reason"][P4_REJECT_GAIN_RATIO] == 1
    assert d["candidate_reject_by_reason"][P4_REJECT_INTERNAL_TRANSPORT_BUDGET] == 1
    assert d["allowed_internal_spend"] == 5
    assert d["reclaim_internal_transport_spent_prior"] == 1
