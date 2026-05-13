"""Patch B: fixed output stub materialization vs inferred rows (STEP4 collect / STEP9 gate)."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import shape_miner_output_cell
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    collect_routing_jobs,
    stub_row_materialized_for_want_role,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_failure_category as s4fc,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_routing_permission as s4rp,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_map_ops import (
    same_kind_transport_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_route_failure_diagnostic import (  # noqa: E501
    build_step4_route_failure_diagnostic,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
    final_validation as fv,
)


def _never_external(_: tuple[int, int]) -> bool:
    return False


def test_collect_routing_jobs_fixed_output_stub_inferred_pipe_row() -> None:
    """Job emitted when stub is inferred with fixed-output flag and pipe layout (§9 start)."""

    core = (10, 10)
    r = 0
    stub = shape_miner_output_cell(core, r)
    assert stub is not None
    cells: dict[tuple[int, int], dict[str, Any]] = {
        core: {
            "x": core[0],
            "y": core[1],
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "surface": "fluid",
            "r": r,
        },
        stub: {
            "x": stub[0],
            "y": stub[1],
            "role": "inferred",
            "layout_kind": "fluid_pipe_segment",
            "surface": "fluid",
            "fixed_output_stub": True,
        },
    }
    jobs = collect_routing_jobs(cells)
    assert (core, stub, "fluid_pipe", None) in jobs


def test_stub_row_materialized_rejects_opposite_kind_token() -> None:
    """TransportKind: inferred row with explicit belt token must not satisfy pipe want_role."""

    row: dict[str, Any] = {
        "role": "inferred",
        "layout_kind": "shape_belt_segment",
        "fixed_output_stub": True,
    }
    assert stub_row_materialized_for_want_role(row, "belt") is True
    assert stub_row_materialized_for_want_role(row, "pipe") is False


def test_step4_step_cost_inferred_fixed_pipe_stub_matches_same_role_transport() -> None:
    """STEP4 Dijkstra must treat legal fixed stub like same-role transport (not mineable open)."""

    stub: dict[str, Any] = {
        "x": 3,
        "y": 0,
        "role": "inferred",
        "layout_kind": "fluid_pipe_segment",
        "fixed_output_stub": True,
    }
    cells = {(3, 0): stub}
    assert (
        s4rp.step4_step_cost(
            (3, 0),
            want_role="pipe",
            cells=cells,
            mineable=frozenset({(3, 0)}),
            asteroid=frozenset(),
            is_external=_never_external,
        )
        == 10.0
    )


def test_same_kind_transport_cells_includes_inferred_fixed_pipe_stub() -> None:
    stub: dict[str, Any] = {
        "x": 2,
        "y": 1,
        "role": "inferred",
        "layout_kind": "fluid_pipe_segment",
        "pass12_fixed_output_stub": True,
    }
    cells = {(2, 1): stub}
    assert (2, 1) in same_kind_transport_cells(cells, "pipe")
    assert (2, 1) not in same_kind_transport_cells(cells, "belt")


def test_route_failure_diagnostic_stub_cell_role_ok_inferred_fixed() -> None:
    stub_cell = (4, 4)
    cells = {
        stub_cell: {
            "x": 4,
            "y": 4,
            "role": "inferred",
            "layout_kind": "fluid_pipe_segment",
            "fixed_output_stub": True,
        }
    }
    detail: dict[str, Any] = {
        "nearest_existing_transport_distance": 2,
        "blocked_reason_near_stub": [],
        "last_error": "no_route",
    }
    d = build_step4_route_failure_diagnostic(
        rec=None,
        extractor_cell=(3, 4),
        stub_cell=stub_cell,
        transport_kind="fluid_pipe",
        want_role="pipe",
        raw_goal=set(),
        goal_cells=frozenset(),
        trunk_cells=frozenset(),
        trunk_seed_candidates_by_kind={"shape_belt": set(), "fluid_pipe": set()},
        margin_cells=set(),
        committed_trunk_for_kind=set(),
        blocked=frozenset(),
        hard_extras=frozenset(),
        cells=cells,
        mineable=frozenset(),
        asteroid=frozenset(),
        is_external=lambda c: False,
        cheap_reuse_cells=None,
        search_stats={"stop_reason": "exhausted", "search_mode": "goal_cells_union_legacy"},
        detail=detail,
        final_state=None,
    )
    assert d["stub_cell_role_ok"] is True


def test_step4_failure_category_geometry_cage_neighbor_pattern() -> None:
    """Neighbor reasons blocked + step_cost_none (no hard-only ring) → geometry_cage."""

    near = [
        {"cell": [0, 0], "reason": "blocked"},
        {"cell": [2, 1], "reason": "step_cost_none"},
        {"cell": [1, 2], "reason": "blocked"},
        {"cell": [0, 2], "reason": "step_cost_none"},
    ]
    cat = s4fc.classify_step4_failure_category(
        stop_reason="exhausted",
        last_error="no_route",
        nearest_transport_hops=3,
        near=near,
        goal_cells_count=2,
        reachable_goal_count=0,
        cells={},
        want_role="belt",
        stub_cell=(1, 1),
        hard_extras=frozenset(),
    )
    assert cat == s4fc.Step4FailureCategory.geometry_cage.value


def test_validate_missing_stub_zero_when_inferred_stub_materialized() -> None:
    """STEP9 missing_stub_count: inferred fixed-output pipe stub satisfies fluid extractor."""

    core = (5, 5)
    r = 0
    stub = shape_miner_output_cell(core, r)
    assert stub is not None
    mining_map: list[dict[str, Any]] = [
        {
            "x": core[0],
            "y": core[1],
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "surface": "fluid",
            "r": r,
        },
        {
            "x": stub[0],
            "y": stub[1],
            "role": "inferred",
            "layout_kind": "fluid_pipe_segment",
            "surface": "fluid",
            "fixed_output_stub": True,
        },
        # bbox / external reachability: belt bridge east from stub to margin
        {"x": stub[0] + 1, "y": stub[1], "role": "pipe", "surface": "fluid"},
        {"x": stub[0] + 2, "y": stub[1], "role": "pipe", "surface": "fluid"},
        {"x": stub[0] + 3, "y": stub[1], "role": "pipe", "surface": "fluid"},
        {"x": stub[0] + 4, "y": stub[1], "role": "pipe", "surface": "fluid"},
        {"x": stub[0] + 5, "y": stub[1], "role": "pipe", "surface": "fluid"},
    ]
    rep = fv.validate_final_mining_layout(mining_map)
    assert rep.missing_stub_count == 0


def test_validate_overlap_counts_transport_on_extractor_body() -> None:
    """§15: belt/pipe must not share a cell with extractor/extension body."""

    mining_map: list[dict[str, Any]] = [
        {
            "x": 8,
            "y": 8,
            "role": "occupied",
            "layout_kind": "miner",
            "surface": "shape",
            "r": 0,
        },
        {"x": 8, "y": 8, "role": "belt", "surface": "shape"},
    ]
    rep = fv.validate_final_mining_layout(mining_map)
    assert rep.overlap_violation_count >= 1
    assert rep.geometry_valid is False


def test_fixed_output_stub_not_removed_when_cells_remain_inferred_materialized() -> None:
    mining_map: list[dict[str, Any]] = [
        {
            "x": 11,
            "y": 10,
            "role": "inferred",
            "layout_kind": "shape_belt_segment",
            "surface": "shape",
            "fixed_output_stub": True,
        },
    ]
    rep = fv.validate_final_mining_layout(mining_map)
    assert rep.fixed_output_stub_removed_count == 0
