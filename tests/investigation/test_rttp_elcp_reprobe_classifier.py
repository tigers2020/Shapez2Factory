"""Pure tests for ELCP reprobe failure classifier (P1-ELCP-RF)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.routing.route_probe import RouteProbeResult
from harness.investigation.rttp_elcp_reprobe_forensics import (
    ElcpProbeFailureClass,
    classify_probe_failure,
)


def _probe(*, reachable: bool, expanded: int) -> RouteProbeResult:
    return RouteProbeResult(reachable, 0, None, (), expanded)


def test_classify_start_blocked() -> None:
    assert (
        classify_probe_failure(
            probe_start=None,
            fill_first_ok=False,
            probe=None,
            max_expansions=500,
            goals_nonempty=True,
            candidate_reachable=True,
            post_probe_committed=False,
            committed_route_cell_count=0,
            traversable_cell_count=100,
            tm_new_trunk_len=0,
            trunk_pressure_correlated=False,
        )
        is ElcpProbeFailureClass.START_BLOCKED
    )


def test_classify_lane_capacity_shortfall() -> None:
    assert (
        classify_probe_failure(
            probe_start=(0, 0),
            fill_first_ok=False,
            probe=None,
            max_expansions=500,
            goals_nonempty=True,
            candidate_reachable=True,
            post_probe_committed=False,
            committed_route_cell_count=0,
            traversable_cell_count=100,
            tm_new_trunk_len=0,
            trunk_pressure_correlated=False,
        )
        is ElcpProbeFailureClass.LANE_CAPACITY_SHORTFALL
    )


def test_classify_budget_exceeded() -> None:
    assert (
        classify_probe_failure(
            probe_start=(0, 0),
            fill_first_ok=True,
            probe=_probe(reachable=False, expanded=500),
            max_expansions=500,
            goals_nonempty=True,
            candidate_reachable=True,
            post_probe_committed=False,
            committed_route_cell_count=0,
            traversable_cell_count=100,
            tm_new_trunk_len=0,
            trunk_pressure_correlated=False,
        )
        is ElcpProbeFailureClass.BUDGET_EXCEEDED
    )


def test_classify_stale_candidate_reachable_before_post_probe() -> None:
    assert (
        classify_probe_failure(
            probe_start=(0, 0),
            fill_first_ok=True,
            probe=_probe(reachable=True, expanded=10),
            max_expansions=500,
            goals_nonempty=True,
            candidate_reachable=True,
            post_probe_committed=False,
            committed_route_cell_count=0,
            traversable_cell_count=100,
            tm_new_trunk_len=0,
            trunk_pressure_correlated=False,
        )
        is ElcpProbeFailureClass.STALE_CANDIDATE_REACHABLE
    )


def test_classify_post_probe_commit_fail_when_not_candidate_reachable() -> None:
    assert (
        classify_probe_failure(
            probe_start=(0, 0),
            fill_first_ok=True,
            probe=_probe(reachable=True, expanded=10),
            max_expansions=500,
            goals_nonempty=True,
            candidate_reachable=False,
            post_probe_committed=False,
            committed_route_cell_count=0,
            traversable_cell_count=100,
            tm_new_trunk_len=0,
            trunk_pressure_correlated=False,
        )
        is ElcpProbeFailureClass.POST_PROBE_COMMIT_FAIL
    )
