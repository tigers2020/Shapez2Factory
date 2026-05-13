"""Pass2 STEP4-aligned first-route goal set construction and trace (§3.2)."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass12_route_probe as p12rp,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_goal_trunk_seed as s4_goal,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_route_failure_diagnostic as s4frd,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
    final_validation as finval,
)


def _is_ext_factory(ext: Coord) -> Any:
    return lambda c: c == ext


def test_first_route_final_goal_positive_from_exterior_margin_only() -> None:
    """No committed trunk: margin ∪ per-kind seeds; exterior margin alone gives nonzero goals."""

    ext: Coord = (5, 0)
    is_external = _is_ext_factory(ext)
    mineable = frozenset({(4, 0), (3, 0)})
    asteroid: frozenset[Coord] = frozenset()
    cells: dict[Coord, dict[str, Any]] = {
        (3, 0): {
            "x": 3,
            "y": 0,
            "role": "inferred",
            "layout_kind": "asteroid_field",
            "surface": "shape",
        },
        (4, 0): {
            "x": 4,
            "y": 0,
            "role": "inferred",
            "layout_kind": "asteroid_field",
            "surface": "shape",
        },
    }
    probe_transport = frozenset({(4, 0)})
    sink = p12rp.new_pass2_route_probe_stats_sink()
    goals, kind, n, trace = p12rp.build_pass2_step4_aligned_routing_goals(
        transport_kind="shape_belt",
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        is_external=is_external,
        existing_layout_analysis=None,
        transport_cells_before=frozenset(),
        transport_cells_probe=probe_transport,
        blocked_for_probe=frozenset(),
        stats_sink=sink,
    )
    assert kind == "first_route"
    assert (4, 0) in goals
    assert n == len(goals) > 0
    assert trace["final_goal_count"] > 0
    assert trace["exterior_margin_cell_count"] >= 1
    assert trace["rejected_reason"] is None
    md = trace["pass2_external_margin_diagnostic"]
    assert md["universe_scan_cell_count"] >= 1
    assert md["margin_eligible_universe_cell_count"] >= 1
    assert "margin_generation_reason_if_zero" not in md
    out, diag = p12rp.pass2_bundle_route_probe_decision(
        (3, 0),
        transport_cells=probe_transport,
        blocked_cells=frozenset(),
        is_external=is_external,
        routing_goal_cells=goals,
        goal_set_kind=kind,
        goal_count=n,
        adjacent_preserve_trunk_baseline_cells=None,
        stats_sink=sink,
        goal_build_trace=trace,
    )
    assert "pass2_goal_set_trace" in diag
    p12rp.finalize_pass2_route_probe_stats(sink)
    assert sink["pass2_probe_goal_count"] == n
    assert out in ("routed", "uncertain")


def test_universe_extra_restores_margin_when_belt_missing_from_cells_keys() -> None:
    """Belt on non-mineable void: only ``universe_extra`` (probe transport) restores margin."""

    ext: Coord = (11, 0)
    is_external = _is_ext_factory(ext)
    mineable = frozenset({(9, 0)})
    asteroid: frozenset[Coord] = frozenset()
    cells: dict[Coord, dict[str, Any]] = {
        (9, 0): {
            "x": 9,
            "y": 0,
            "role": "inferred",
            "layout_kind": "asteroid_field",
            "surface": "shape",
        },
    }
    belt_edge: Coord = (10, 0)
    probe_transport = frozenset({belt_edge})
    goals_no_extra, k1, n1, t1 = p12rp.build_pass2_step4_aligned_routing_goals(
        transport_kind="shape_belt",
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        is_external=is_external,
        existing_layout_analysis=None,
        transport_cells_before=frozenset(),
        transport_cells_probe=frozenset(),
        blocked_for_probe=frozenset(),
    )
    assert belt_edge not in goals_no_extra
    assert n1 == 0
    assert t1["rejected_reason"] == str(s4frd.Step4RouteFailureReason.no_exterior_margin_for_probe)

    goals, kind, n, trace = p12rp.build_pass2_step4_aligned_routing_goals(
        transport_kind="shape_belt",
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        is_external=is_external,
        existing_layout_analysis=None,
        transport_cells_before=frozenset(),
        transport_cells_probe=probe_transport,
        blocked_for_probe=frozenset(),
    )
    assert kind == "first_route"
    assert belt_edge in goals
    assert n > 0
    assert trace["external_margin_bbox_source"] == (
        "universe_keys_mineable_asteroid_probe_transport_union"
    )


def test_transport_kind_separation_trunk_seed_hints() -> None:
    """ELA-style hint applies only to matching transport kind; other kind keeps margin only."""

    ext: Coord = (2, 3)
    is_external = _is_ext_factory(ext)
    margin_cell: Coord = (2, 2)
    hint_cell: Coord = (5, 5)
    mineable = frozenset({margin_cell, hint_cell})
    asteroid: frozenset[Coord] = frozenset()
    cells: dict[Coord, dict[str, Any]] = {
        margin_cell: {
            "x": margin_cell[0],
            "y": margin_cell[1],
            "role": "inferred",
            "layout_kind": "asteroid_field",
            "surface": "shape",
        },
        hint_cell: {
            "x": hint_cell[0],
            "y": hint_cell[1],
            "role": "belt",
            "surface": "shape",
        },
    }
    ela = {"solver_hints": {"trunk_seed_cell_union": [[hint_cell[0], hint_cell[1]]]}}
    probe = frozenset({margin_cell})
    g_shape, _, _, tr_s = p12rp.build_pass2_step4_aligned_routing_goals(
        transport_kind="shape_belt",
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        is_external=is_external,
        existing_layout_analysis=ela,
        transport_cells_before=frozenset(),
        transport_cells_probe=probe,
        blocked_for_probe=frozenset(),
    )
    g_fluid, _, _, tr_f = p12rp.build_pass2_step4_aligned_routing_goals(
        transport_kind="fluid_pipe",
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        is_external=is_external,
        existing_layout_analysis=ela,
        transport_cells_before=frozenset(),
        transport_cells_probe=probe,
        blocked_for_probe=frozenset(),
    )
    assert hint_cell in g_shape
    assert hint_cell not in g_fluid
    assert tr_s["same_kind_trunk_seed_count"] >= 1
    assert tr_f["same_kind_trunk_seed_count"] == 0


def test_island_empty_margin_does_not_promote_prior_transport_as_goals() -> None:
    """No exterior margin nor external-reachable prior trunk: empty goals (no island fallback)."""

    mineable = frozenset({(1, 0), (2, 0)})
    asteroid: frozenset[Coord] = frozenset()
    cells: dict[Coord, dict[str, Any]] = {
        (1, 0): {
            "x": 1,
            "y": 0,
            "role": "inferred",
            "layout_kind": "asteroid_field",
            "surface": "fluid",
        },
        (2, 0): {
            "x": 2,
            "y": 0,
            "role": "inferred",
            "layout_kind": "asteroid_field",
            "surface": "fluid",
        },
    }
    before = frozenset({(1, 0)})
    probe = frozenset({(1, 0), (2, 0)})
    goals, kind, n, trace = p12rp.build_pass2_step4_aligned_routing_goals(
        transport_kind="fluid_pipe",
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        is_external=lambda _c: False,
        existing_layout_analysis=None,
        transport_cells_before=before,
        transport_cells_probe=probe,
        blocked_for_probe=frozenset(),
    )
    assert kind == "first_route"
    assert goals == frozenset()
    assert n == 0
    assert trace["exterior_margin_cell_count"] == 0
    assert trace["final_goal_count"] == 0
    assert trace["transport_cells_before_count"] == 1
    assert trace["external_reachable_transport_before_count"] == 0
    assert "fallback_goal_source" not in trace
    exp_margin = str(s4frd.Step4RouteFailureReason.no_exterior_margin_for_probe)
    assert trace["rejected_reason"] == exp_margin
    md = trace["pass2_external_margin_diagnostic"]
    assert md["universe_scan_cell_count"] == 2
    assert md["margin_eligible_universe_cell_count"] == 2
    assert "margin_generation_reason_if_zero" in md
    assert "is_external_never_true_on_sampled_neighbors" in md["margin_generation_reason_if_zero"]


def test_pass2_margin_diagnostic_shell_breakdown_dense_inferred_block() -> None:
    """Neighbors outside routing universe can still lie inside §15 expanded mineable shell."""

    rows: list[dict[str, Any]] = []
    cells: dict[Coord, dict[str, Any]] = {}
    mineable_set: set[Coord] = set()
    for x in range(5, 14):
        for y in range(5, 14):
            c = (x, y)
            mineable_set.add(c)
            row = {
                "x": x,
                "y": y,
                "role": "inferred",
                "layout_kind": "asteroid_field",
                "surface": "shape",
            }
            rows.append(row)
            cells[c] = dict(row)
    mineable = frozenset(mineable_set)
    asteroid: frozenset[Coord] = frozenset()
    is_external = finval.external_predicate_for_mining_map(rows)
    shell_bm = finval.external_bbox_margin_for_mining_map(rows)
    assert shell_bm is not None
    shell_bbox, shell_margin = shell_bm
    _, kind, n, trace = p12rp.build_pass2_step4_aligned_routing_goals(
        transport_kind="shape_belt",
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        is_external=is_external,
        existing_layout_analysis=None,
        transport_cells_before=frozenset(),
        transport_cells_probe=frozenset(),
        blocked_for_probe=frozenset(),
        is_external_shell_bbox=shell_bbox,
        is_external_shell_margin=shell_margin,
    )
    assert kind == "first_route"
    assert n == 0
    assert trace["exterior_margin_cell_count"] == 0
    md = trace["pass2_external_margin_diagnostic"]
    assert md["is_external_true_neighbor_sample_count"] == 0
    br = md["sampled_neighbor_shell_breakdown"]
    assert br["sampled_neighbor_outside_expanded_mineable_bbox_count"] == 0
    assert br["sampled_neighbor_inside_expanded_mineable_bbox_count"] > 0
    assert md["is_external_predicate_mineable_bbox"] == {
        "x_min": 5,
        "x_max": 13,
        "y_min": 5,
        "y_max": 13,
    }
    assert md["is_external_predicate_margin"] == shell_margin
    reasons = md["margin_generation_reason_if_zero"]
    assert "all_sampled_neighbors_inside_predicate_shell_or_x0" in reasons


def test_pass2_external_margin_diagnostic_skipped_x0_only_universe() -> None:
    """``exterior_margin_cells`` skips ``x==0`` universe cells; diagnostic records that."""

    ext: Coord = (-1, 0)
    is_external = _is_ext_factory(ext)
    mineable = frozenset({(0, 0), (0, 1)})
    asteroid: frozenset[Coord] = frozenset()
    cells: dict[Coord, dict[str, Any]] = {
        (0, 0): {
            "x": 0,
            "y": 0,
            "role": "inferred",
            "layout_kind": "asteroid_field",
            "surface": "shape",
        },
        (0, 1): {
            "x": 0,
            "y": 1,
            "role": "inferred",
            "layout_kind": "asteroid_field",
            "surface": "shape",
        },
    }
    _, kind, n, trace = p12rp.build_pass2_step4_aligned_routing_goals(
        transport_kind="shape_belt",
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        is_external=is_external,
        existing_layout_analysis=None,
        transport_cells_before=frozenset(),
        transport_cells_probe=frozenset(),
        blocked_for_probe=frozenset(),
    )
    assert kind == "first_route"
    assert n == 0
    md = trace["pass2_external_margin_diagnostic"]
    assert md["universe_scan_cell_count"] == 2
    assert md["margin_eligible_universe_cell_count"] == 0
    assert "skipped_x0_only_universe" in md["margin_generation_reason_if_zero"]


def test_finalize_prefers_last_probe_goal_count_over_max() -> None:
    sink = p12rp.new_pass2_route_probe_stats_sink()
    p12rp.pass2_bundle_route_probe_decision(
        (1, 1),
        transport_cells=frozenset(),
        blocked_cells=frozenset(),
        is_external=lambda _: False,
        routing_goal_cells=frozenset({(1, 2)}),
        goal_set_kind="first_route",
        goal_count=10,
        adjacent_preserve_trunk_baseline_cells=None,
        stats_sink=sink,
        goal_build_trace={"final_goal_count": 10},
    )
    p12rp.pass2_bundle_route_probe_decision(
        (1, 1),
        transport_cells=frozenset(),
        blocked_cells=frozenset(),
        is_external=lambda _: False,
        routing_goal_cells=frozenset({(1, 2)}),
        goal_set_kind="first_route",
        goal_count=3,
        adjacent_preserve_trunk_baseline_cells=None,
        stats_sink=sink,
        goal_build_trace={"final_goal_count": 3},
    )
    p12rp.finalize_pass2_route_probe_stats(sink)
    assert sink["pass2_probe_goal_count_max"] == 10
    assert sink["pass2_probe_goal_count_sum"] == 13
    assert sink["pass2_probe_goal_count"] == 3


def test_empty_goal_set_increments_counter_and_trace() -> None:
    sink = p12rp.new_pass2_route_probe_stats_sink()
    _, diag = p12rp.pass2_bundle_route_probe_decision(
        (1, 1),
        transport_cells=frozenset(),
        blocked_cells=frozenset(),
        is_external=lambda _: False,
        routing_goal_cells=frozenset(),
        goal_set_kind="first_route",
        goal_count=0,
        adjacent_preserve_trunk_baseline_cells=None,
        stats_sink=sink,
        goal_build_trace={"final_goal_count": 0, "rejected_reason": "empty_goal_set"},
    )
    assert sink["pass2_probe_empty_goal_set_count"] == 1
    assert diag["pass2_goal_set_trace"]["rejected_reason"] == "empty_goal_set"
    assert diag["pass2_goal_assisted_probe"]["allowed_goal_void_cell_count"] == 0


def test_patch_a_margin_universe_extra_collects_belt_rows_missing_from_cells() -> None:
    """STEP4 Pass2 parity: belt/pipe map rows missing from ``cells`` become ``universe_extra``."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
        step4_merge_routing as s4mr,
    )

    rows = [
        {"x": 9, "y": 0, "role": "inferred", "layout_kind": "asteroid_field", "surface": "shape"},
        {"x": 10, "y": 0, "role": "belt", "surface": "shape"},
    ]
    cells_keys = {(9, 0)}
    extra = s4mr._margin_universe_extra_from_map_list(rows, cells_keys=cells_keys)
    assert extra == frozenset({(10, 0)})


def test_patch_a_exterior_margin_matches_pass2_when_extra_restores_belt() -> None:
    """Same belt-edge geometry as ``test_universe_extra_restores_margin_when_belt_missing_...``."""

    ext: Coord = (11, 0)

    def is_external(c: Coord) -> bool:
        return c == ext

    mineable = frozenset({(9, 0)})
    asteroid: frozenset[Coord] = frozenset()
    cells: dict[Coord, dict[str, Any]] = {
        (9, 0): {
            "x": 9,
            "y": 0,
            "role": "inferred",
            "layout_kind": "asteroid_field",
            "surface": "shape",
        },
    }
    belt_edge: Coord = (10, 0)
    m0 = s4_goal.exterior_margin_cells(
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        is_external=is_external,
        universe_extra=frozenset(),
    )
    m1 = s4_goal.exterior_margin_cells(
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        is_external=is_external,
        universe_extra=frozenset({belt_edge}),
    )
    assert m0 == set()
    assert (10, 0) in m1


def test_step4_first_route_empty_trunk_uses_margin_union_trunk_seed() -> None:
    """§08: no committed trunk → raw goals are exterior margin ∪ per-kind trunk_seed."""

    margin = {(20, 20), (21, 20)}
    seeds_shape = {(10, 10), (11, 10)}
    seeds_fluid = {(5, 5)}
    trunk_seed_by_kind: dict[str, set[Coord]] = {
        "shape_belt": set(seeds_shape),
        "fluid_pipe": set(seeds_fluid),
    }
    g_belt = s4_goal.build_step4_goal_set(
        "shape_belt",
        committed_trunk_by_kind={},
        exterior_margin_cells=set(margin),
        trunk_seed_candidates_by_kind=trunk_seed_by_kind,
    )
    assert g_belt == set(margin) | seeds_shape
    g_pipe = s4_goal.build_step4_goal_set(
        "fluid_pipe",
        committed_trunk_by_kind={},
        exterior_margin_cells=set(margin),
        trunk_seed_candidates_by_kind=trunk_seed_by_kind,
    )
    assert g_pipe == set(margin) | seeds_fluid
