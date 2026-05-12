"""Pass2 STEP4-aligned first-route goal set construction and trace (§3.2)."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass12_route_probe as p12rp,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_route_failure_diagnostic as s4frd,
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
    assert t1["rejected_reason"] == str(s4frd.Step4RouteFailureReason.empty_goal_set)

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
