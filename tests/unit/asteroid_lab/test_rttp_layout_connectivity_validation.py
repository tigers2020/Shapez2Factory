"""Task A6 — layout connectivity validation (read-only fail-closed)."""

from __future__ import annotations

import copy

from django_apps.asteroid_lab.contracts.catalog_placement import (
    CardinalDirection,
    CatalogPlacementRef,
)
from django_apps.asteroid_lab.contracts.rttp_layout_issue_codes import (
    ISSUE_CODE_INSUFFICIENT_EXTERIOR_CONNECTORS,
    ISSUE_CODE_MISSING_EXTERIOR_ROUTE,
    ISSUE_CODE_MISSING_OUTPUT_TRANSPORT,
)
from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.coords import Coord
from django_apps.asteroid_lab.optimization.input_contracts import (
    OptimizationInput,
    RouteGoal,
    RouteGoalKind,
    TransportKind,
)
from django_apps.asteroid_lab.optimization.rttp_solver_summary import (
    RttpAlgorithmStepId,
    build_rttp_solver_summary,
)
from django_apps.asteroid_lab.optimization.validation.catalog_layout_validation import (
    layout_connectivity_issue_codes_from_algorithm_steps,
    pipeline_layout_issue_codes_from_algorithm_steps,
    validate_pipeline_layout,
)
from django_apps.asteroid_lab.optimization.validation.layout_connectivity_validation import (
    validate_layout_connectivity_issues,
)
from tests.unit.asteroid_lab.test_b_cs3_validation_gate_boundary import (
    _candidate,
    _catalog_slice,
    _minimal_inp,
)


def _committed_fixture(
    *,
    reserved: frozenset[Coord],
    trunk: frozenset[Coord] | None = None,
) -> tuple[tuple[str, ...], frozenset[Coord], dict[str, BundleCandidate], OptimizationInput]:
    sl = _catalog_slice()
    occupied = frozenset({(5, 7), (6, 7)})
    ref = CatalogPlacementRef("bv:1", (5, 7), CardinalDirection.E)
    cand = _candidate(occupied=occupied, ref=ref)
    inp = _minimal_inp(catalog_slice=sl)
    return ("c1",), reserved, {"c1": cand}, inp


def test_missing_output_transport_when_committed_without_route_reservation() -> None:
    committed_ids, reserved, candidates_by_id, _inp = _committed_fixture(reserved=frozenset())
    issues = validate_layout_connectivity_issues(
        committed_ids=committed_ids,
        reserved_route_cells=reserved,
        candidates_by_id=candidates_by_id,
        trunk_mask_cells=frozenset({(8, 7)}),
    )
    assert ISSUE_CODE_MISSING_OUTPUT_TRANSPORT in issues
    assert ISSUE_CODE_MISSING_EXTERIOR_ROUTE in issues


def test_insufficient_exterior_connectors_when_touched_below_required() -> None:
    from dataclasses import replace

    sl = _catalog_slice()
    occupied = frozenset({(5, 7), (6, 7)})
    ref = CatalogPlacementRef("bv:1", (5, 7), CardinalDirection.E)
    cand = _candidate(occupied=occupied, ref=ref)
    goals = (
        RouteGoal((9, 7), RouteGoalKind.EXTERNAL_MARGIN, TransportKind.SHAPE_BELT, 10, False),
        RouteGoal((10, 7), RouteGoalKind.EXTERNAL_MARGIN, TransportKind.SHAPE_BELT, 10, False),
        RouteGoal((11, 7), RouteGoalKind.EXTERNAL_MARGIN, TransportKind.SHAPE_BELT, 10, False),
    )
    inp = replace(
        _minimal_inp(catalog_slice=sl),
        route_goals=goals,
        required_external_connector_count=3,
    )
    reserved = frozenset({(9, 7)})
    issues = validate_layout_connectivity_issues(
        committed_ids=("c1", "c2", "c3"),
        reserved_route_cells=reserved,
        candidates_by_id={"c1": cand, "c2": cand, "c3": cand},
        trunk_mask_cells=frozenset({(8, 7)}),
        inp=inp,
    )
    assert ISSUE_CODE_INSUFFICIENT_EXTERIOR_CONNECTORS in issues


def test_missing_exterior_route_when_routes_disjoint_from_trunk() -> None:
    reserved = frozenset({(9, 7), (10, 7), (11, 7)})
    committed_ids, reserved_cells, candidates_by_id, inp = _committed_fixture(reserved=reserved)
    issues = validate_layout_connectivity_issues(
        committed_ids=committed_ids,
        reserved_route_cells=reserved_cells,
        candidates_by_id=candidates_by_id,
        trunk_mask_cells=frozenset({(0, 0)}),
    )
    assert issues == (ISSUE_CODE_MISSING_EXTERIOR_ROUTE,)


def test_connectivity_passes_when_stub_reserved_and_trunk_touches_route() -> None:
    reserved = frozenset({(9, 7), (8, 7)})
    committed_ids, reserved_cells, candidates_by_id, inp = _committed_fixture(reserved=reserved)
    passed, _catalog, issues = validate_pipeline_layout(
        committed_ids=committed_ids,
        reserved_route_cells=reserved_cells,
        candidates_by_id=candidates_by_id,
        inp=inp,
        catalog_mode="observe_only",
        trunk_mask_cells=frozenset({(8, 7)}),
    )
    assert issues == ()
    assert passed is True


def test_placement_goal_shortfall_not_a_connectivity_issue_code() -> None:
    shortfall_tokens = frozenset(
        {
            "placement_goal_shortfall",
            "throughput_target_shortfall",
            "route_feasible_shortfall",
            "anchor_capacity_shortfall",
            "commit_shortfall",
        }
    )
    committed_ids, reserved, candidates_by_id, _inp = _committed_fixture(
        reserved=frozenset({(9, 7), (8, 7)})
    )
    issues = validate_layout_connectivity_issues(
        committed_ids=committed_ids,
        reserved_route_cells=reserved,
        candidates_by_id=candidates_by_id,
        trunk_mask_cells=frozenset({(8, 7)}),
    )
    assert not shortfall_tokens.intersection(issues)


def test_validate_layout_connectivity_issues_is_read_only() -> None:
    committed_ids, reserved, candidates_by_id, inp = _committed_fixture(
        reserved=frozenset({(9, 7)})
    )
    before = (
        copy.deepcopy(committed_ids),
        copy.deepcopy(reserved),
        copy.deepcopy(candidates_by_id),
        copy.deepcopy(inp),
    )
    validate_layout_connectivity_issues(
        committed_ids=committed_ids,
        reserved_route_cells=reserved,
        candidates_by_id=candidates_by_id,
        trunk_mask_cells=frozenset({(8, 7)}),
    )
    assert (committed_ids, reserved, candidates_by_id, inp) == before


def test_layout_connectivity_issue_codes_from_commit_step_metrics() -> None:
    steps = (
        {
            "step_id": "rttp.commit",
            "metrics": {
                "layout_connectivity_issue_codes": [
                    ISSUE_CODE_MISSING_EXTERIOR_ROUTE,
                ],
            },
        },
    )
    assert layout_connectivity_issue_codes_from_algorithm_steps(steps) == (
        ISSUE_CODE_MISSING_EXTERIOR_ROUTE,
    )


def test_solver_summary_surfaces_layout_connectivity_issue_codes() -> None:
    steps = (
        {
            "step_id": RttpAlgorithmStepId.RTTP_COMMIT.value,
            "phase": "incremental_commit",
            "event_type": "rttp.commit.domain_snapshot",
            "title": "commit",
            "summary": "",
            "metrics": {
                "layout_connectivity_issue_codes": [ISSUE_CODE_MISSING_EXTERIOR_ROUTE],
            },
        },
    )
    merged = pipeline_layout_issue_codes_from_algorithm_steps(steps)
    summary = build_rttp_solver_summary(
        pipeline_ok=False,
        committed_count=1,
        normal_count=1,
        commit_order=("c1",),
        algorithm_steps=(),
        catalog_error_issue_codes=merged,
    )
    assert summary["validation_passed"] is False
    assert ISSUE_CODE_MISSING_EXTERIOR_ROUTE in summary["issue_codes"]
    assert "rttp_validation_failed" not in summary["issue_codes"]


def test_validate_pipeline_layout_fails_closed_with_explicit_codes() -> None:
    committed_ids, reserved, candidates_by_id, inp = _committed_fixture(reserved=frozenset())
    passed, catalog_result, issues = validate_pipeline_layout(
        committed_ids=committed_ids,
        reserved_route_cells=reserved,
        candidates_by_id=candidates_by_id,
        inp=inp,
        catalog_mode="observe_only",
        trunk_mask_cells=frozenset(),
    )
    assert passed is False
    assert catalog_result is None
    assert ISSUE_CODE_MISSING_OUTPUT_TRANSPORT in issues
    assert ISSUE_CODE_MISSING_EXTERIOR_ROUTE in issues
