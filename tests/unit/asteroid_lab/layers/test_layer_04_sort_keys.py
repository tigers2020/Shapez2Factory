"""Layer 04 mining-first sort key helpers."""

from __future__ import annotations

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.candidates import (
    RouteProbedBundleCandidate,
    RouteProbeResult,
    RouteProbeStatus,
    make_bundle_candidate_for_test,
)
from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.sort_keys import (
    candidate_sort_key,
    connector_goal_distance,
    effective_mining_gain,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    succeeded_probe_at,
)


def test_effective_mining_gain_equals_mining_cell_count_v1() -> None:
    cells = frozenset({(1, 1), (2, 1), (3, 1)})
    candidate = make_bundle_candidate_for_test(mining_occupied_cells=cells)
    assert effective_mining_gain(candidate) == 3


def test_connector_goal_distance_uses_probe_start_not_raw_anchor_delta() -> None:
    candidate = make_bundle_candidate_for_test(
        anchor_coord=(5, 5),
        output_dir=Direction.W,
        route_probe_start_coord=(4, 5),
    )
    entry = RouteProbedBundleCandidate(
        candidate=candidate,
        route_probe_status=RouteProbeStatus.SUCCEEDED,
        route_probe_result=RouteProbeResult(
            reached_goal=True,
            goal_coord=(0, 5),
            path_coords=((4, 5), (0, 5)),
            steps_expanded=2,
            transport_kind=TransportKind.SHAPE_BELT,
            route_cost=4,
        ),
        route_goal_id="g0",
        reject_reason=None,
    )
    assert connector_goal_distance(entry) == 4.0


def test_sort_prefers_higher_mining_gain_over_equivalence_key_lex_order() -> None:
    low_key = succeeded_probe_at(
        (7, 3),
        equivalence_key="zzz",
        mining=frozenset({(7, 3), (6, 3), (5, 3)}),
        output_dir=Direction.W,
    )
    high_key = succeeded_probe_at(
        (7, 3),
        equivalence_key="aaa",
        mining=frozenset({(7, 3), (6, 3), (5, 3), (7, 4), (7, 5), (6, 4)}),
        output_dir=Direction.S,
    )
    assert candidate_sort_key(low_key) > candidate_sort_key(high_key)
