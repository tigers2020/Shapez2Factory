"""Pass2 fluid: reject when bounded STEP4 BFS cannot reach any STEP4-aligned goal (no Dijkstra)."""

from __future__ import annotations

import json
from pathlib import Path

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass12_bundle_commit as p12_bc,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass12_route_probe as p12_rp,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
    build_solver_timeline,
)

_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "asteroid_mining_layout"
    / "step4_fluid_pipe_failure_regression_bp.json"
)


def _fluid_cell(x: int, y: int) -> dict:
    return {
        "x": x,
        "y": y,
        "role": "inferred",
        "layout_kind": "asteroid_field",
        "surface": "fluid",
    }


def test_pass2_rejects_fluid_stub_when_no_step4_goal_reachable() -> None:
    """Stub has one legal exit into a tiny dead end.

    Exterior goals and trunk lie outside that pocket.
    """

    sink = p12_rp.new_pass2_route_probe_stats_sink()
    mineable: frozenset[Coord] = frozenset(
        [(5, 5), (5, 6), (5, 7)] + [(x, 5) for x in range(10, 55)]
    )
    cells = {c: _fluid_cell(c[0], c[1]) for c in mineable}
    baseline_trunk = frozenset((x, 5) for x in range(10, 55))
    # Three cage walls on stub (5,5); fourth side opens into a 2-cell dead end (not isolated).
    blocked_ring = frozenset({(4, 5), (6, 5), (5, 4), (4, 7), (6, 7), (5, 8)})
    pack = p12_bc.Pass2RouteProbePack(
        mineable=mineable,
        asteroid=frozenset(),
        cells=cells,
        existing_layout_analysis=None,
        stats_sink=sink,
    )
    scratch = p12_bc.Pass12LayoutScratch(transport_kind="fluid_pipe")
    scratch.transport_cells = set(baseline_trunk)
    scratch.blocked_cells = {(2, 0)}
    cand = p12_bc.Pass12BundleCandidate(
        blocked_cells=blocked_ring,
        new_transport=frozenset({(5, 5)}),
        stub_cell=(5, 5),
        extractor_cell=(4, 5),
        extension_facings=frozenset(),
        extractor_output_dir=(1, 0),
        placement_pass="pass2",
    )

    def is_ext(c: Coord) -> bool:
        return c[0] >= 55

    assert (
        p12_bc.try_commit_pass2_bundle(
            scratch,
            cand,
            is_external=is_ext,
            pass2_route_probe_pack=pack,
        )
        is False
    )
    assert int(sink.get("pass2_reject_step4_unreachable_fluid_stub_count", 0)) == 1
    assert int(sink.get("pass2_reject_step4_unreachable_stub_count", 0)) == 0
    assert scratch.placement_records == {}


def test_pass2_fluid_reachable_stub_still_commits_provisional() -> None:
    """Fluid stub reaches exterior-touching same-kind trunk (canonical goals, no island ring)."""

    sink = p12_rp.new_pass2_route_probe_stats_sink()
    mineable = frozenset({(2, 0), (5, 0), (6, 0), (7, 0), (8, 0), (9, 0), (10, 0), (11, 0)})
    cells = {c: _fluid_cell(c[0], c[1]) for c in mineable}
    pack = p12_bc.Pass2RouteProbePack(
        mineable=mineable,
        asteroid=frozenset(),
        cells=cells,
        existing_layout_analysis=None,
        stats_sink=sink,
    )
    scratch = p12_bc.Pass12LayoutScratch(transport_kind="fluid_pipe")
    scratch.transport_cells = {(6, 0), (7, 0), (8, 0), (9, 0), (10, 0), (11, 0)}
    scratch.blocked_cells = {(2, 0)}
    cand = p12_bc.Pass12BundleCandidate(
        blocked_cells=frozenset({(2, 0)}),
        new_transport=frozenset({(5, 0)}),
        stub_cell=(5, 0),
        extractor_cell=(2, 0),
        extension_facings=frozenset(),
        extractor_output_dir=(1, 0),
        placement_pass="pass2",
    )

    def is_ext(c: Coord) -> bool:
        return c == (12, 0)

    assert (
        p12_bc.try_commit_pass2_bundle(
            scratch,
            cand,
            is_external=is_ext,
            pass2_route_probe_pack=pack,
        )
        is True
    )
    assert int(sink.get("pass2_reject_step4_unreachable_fluid_stub_count", 0)) == 0
    assert scratch.placement_records


def test_pass2_rejects_existing_layout_island_fallback_only_fluid_stub() -> None:
    """ELA가 있어도 외부 도달 trunk/margin이 없으면 island prior만으로 Pass2 commit 불가."""

    sink = p12_rp.new_pass2_route_probe_stats_sink()
    mineable = frozenset({(2, 0), (5, 0), (6, 0), (7, 0), (8, 0), (9, 0), (10, 0)})
    cells = {c: _fluid_cell(c[0], c[1]) for c in mineable}
    pack = p12_bc.Pass2RouteProbePack(
        mineable=mineable,
        asteroid=frozenset(),
        cells=cells,
        existing_layout_analysis={
            "source_kind": "existing_fluid_layout",
            "solver_hints": {"trunk_seed_cell_union": []},
        },
        stats_sink=sink,
    )
    scratch = p12_bc.Pass12LayoutScratch(transport_kind="fluid_pipe")
    scratch.transport_cells = {(6, 0), (7, 0), (8, 0), (9, 0), (10, 0)}
    scratch.blocked_cells = {(2, 0)}
    cand = p12_bc.Pass12BundleCandidate(
        blocked_cells=frozenset({(2, 0)}),
        new_transport=frozenset({(5, 0)}),
        stub_cell=(5, 0),
        extractor_cell=(2, 0),
        extension_facings=frozenset(),
        extractor_output_dir=(1, 0),
        placement_pass="pass2",
    )

    def is_ext(c: Coord) -> bool:
        return c[0] >= 100

    assert (
        p12_bc.try_commit_pass2_bundle(
            scratch,
            cand,
            is_external=is_ext,
            pass2_route_probe_pack=pack,
        )
        is False
    )
    gtrace = sink.get("pass2_probe_last_goal_trace") or {}
    assert int(gtrace.get("transport_cells_before_count") or 0) > 0
    assert int(gtrace.get("final_goal_count") or 0) == 0
    assert "fallback_goal_source" not in gtrace
    assert int(sink.get("pass2_reject_transport_cells_before_island_fallback_count", 0)) == 1
    assert int(sink.get("pass2_reject_step4_unreachable_fluid_stub_count", 0)) == 1
    assert scratch.placement_records == {}


def test_pass2_rejects_island_prior_fluid_without_existing_layout_analysis() -> None:
    """Island-only prior transport rejects even when ``existing_layout_analysis`` is absent."""

    sink = p12_rp.new_pass2_route_probe_stats_sink()
    mineable = frozenset({(2, 0), (5, 0), (6, 0), (7, 0), (8, 0), (9, 0), (10, 0)})
    cells = {c: _fluid_cell(c[0], c[1]) for c in mineable}
    pack = p12_bc.Pass2RouteProbePack(
        mineable=mineable,
        asteroid=frozenset(),
        cells=cells,
        existing_layout_analysis=None,
        stats_sink=sink,
    )
    scratch = p12_bc.Pass12LayoutScratch(transport_kind="fluid_pipe")
    scratch.transport_cells = {(6, 0), (7, 0), (8, 0), (9, 0), (10, 0)}
    scratch.blocked_cells = {(2, 0)}
    cand = p12_bc.Pass12BundleCandidate(
        blocked_cells=frozenset({(2, 0)}),
        new_transport=frozenset({(5, 0)}),
        stub_cell=(5, 0),
        extractor_cell=(2, 0),
        extension_facings=frozenset(),
        extractor_output_dir=(1, 0),
        placement_pass="pass2",
    )

    def is_ext(c: Coord) -> bool:
        return c[0] >= 100

    assert (
        p12_bc.try_commit_pass2_bundle(
            scratch,
            cand,
            is_external=is_ext,
            pass2_route_probe_pack=pack,
        )
        is False
    )
    gtrace = sink.get("pass2_probe_last_goal_trace") or {}
    assert int(gtrace.get("transport_cells_before_count") or 0) > 0
    assert int(gtrace.get("final_goal_count") or 0) == 0
    assert "fallback_goal_source" not in gtrace
    assert int(sink.get("pass2_reject_transport_cells_before_island_fallback_count", 0)) == 1
    assert int(sink.get("pass2_reject_step4_unreachable_fluid_stub_count", 0)) == 1


def test_fluid_regression_fixture_step4_failures_and_validation_stay_clean() -> None:
    """Locked BP: happy path keeps STEP4 failures at 0 and validation geometry/connectivity true."""

    raw = json.loads(_FIXTURE.read_text(encoding="utf-8"))
    out = build_solver_timeline(raw)
    ss = out.get("solver_summary") or {}
    assert int(ss.get("step4_routing_failure_count") or 0) == 0
    fv = out.get("final_validation") or {}
    assert fv.get("geometry_valid") is True
    assert fv.get("connectivity_valid") is True


def test_shape_belt_dead_end_still_uses_belt_unreachable_reason_only() -> None:
    """Belt dead-end: Pass2 uncertain rejects (pass2_reject_step4_unreachable_component)."""

    sink = p12_rp.new_pass2_route_probe_stats_sink()
    mineable: frozenset[Coord] = frozenset(
        [(5, 5), (5, 6), (5, 7)] + [(x, 5) for x in range(10, 55)]
    )
    cells = {
        c: {
            "x": c[0],
            "y": c[1],
            "role": "inferred",
            "layout_kind": "asteroid_field",
            "surface": "shape",
        }
        for c in mineable
    }
    baseline_trunk = frozenset((x, 5) for x in range(10, 55))
    blocked_ring = frozenset({(4, 5), (6, 5), (5, 4), (4, 7), (6, 7), (5, 8)})
    pack = p12_bc.Pass2RouteProbePack(
        mineable=mineable,
        asteroid=frozenset(),
        cells=cells,
        existing_layout_analysis=None,
        stats_sink=sink,
    )
    scratch = p12_bc.Pass12LayoutScratch(transport_kind="shape_belt")
    scratch.transport_cells = set(baseline_trunk)
    scratch.blocked_cells = set()
    cand = p12_bc.Pass12BundleCandidate(
        blocked_cells=blocked_ring,
        new_transport=frozenset({(5, 5)}),
        stub_cell=(5, 5),
        extractor_cell=(4, 5),
        extension_facings=frozenset(),
        extractor_output_dir=(1, 0),
        placement_pass="pass2",
    )

    def is_ext(c: Coord) -> bool:
        return c[0] >= 55

    assert (
        p12_bc.try_commit_pass2_bundle(
            scratch,
            cand,
            is_external=is_ext,
            pass2_route_probe_pack=pack,
        )
        is False
    )
    assert int(sink.get("pass2_reject_step4_unreachable_stub_count", 0)) == 1
    assert int(sink.get("pass2_reject_step4_unreachable_fluid_stub_count", 0)) == 0
    assert int(sink.get("pass2_reject_step4_unreachable_component_count", 0)) >= 1


def _shape_belt_row(c: Coord) -> dict:
    return {
        "x": c[0],
        "y": c[1],
        "role": "inferred",
        "layout_kind": "asteroid_field",
        "surface": "shape",
    }


def test_pass2_rejects_transport_disjoint_when_step4_prec_reachable_belt() -> None:
    """STEP4 BFS can reach margin goals through mineable void while transport stays off-trunk."""

    sink = p12_rp.new_pass2_route_probe_stats_sink()
    row_blocks = frozenset((x, 5) for x in range(6, 60))
    vertical_tunnel = frozenset((5, y) for y in range(6, 100))
    row_y99 = frozenset((x, 99) for x in range(6, 100))
    col_x99 = frozenset((99, y) for y in range(6, 100))
    margin_cell = (99, 5)
    trunk_span = frozenset((x, 5) for x in range(60, 100))
    mineable = frozenset(
        row_blocks
        | vertical_tunnel
        | row_y99
        | col_x99
        | trunk_span
        | frozenset({margin_cell, (5, 5)})
    )
    cells = {c: _shape_belt_row(c) for c in mineable}
    pack = p12_bc.Pass2RouteProbePack(
        mineable=mineable,
        asteroid=frozenset(),
        cells=cells,
        existing_layout_analysis=None,
        stats_sink=sink,
    )
    scratch = p12_bc.Pass12LayoutScratch(transport_kind="shape_belt")
    scratch.transport_cells = set(trunk_span)
    scratch.blocked_cells = set()
    cand = p12_bc.Pass12BundleCandidate(
        blocked_cells=frozenset({(4, 5)}) | row_blocks,
        new_transport=frozenset({(5, 5)}),
        stub_cell=(5, 5),
        extractor_cell=(4, 5),
        extension_facings=frozenset(),
        extractor_output_dir=(1, 0),
        placement_pass="pass2",
    )

    def is_ext(c: Coord) -> bool:
        return int(c[0]) >= 100

    assert (
        p12_bc.try_commit_pass2_bundle(
            scratch,
            cand,
            is_external=is_ext,
            pass2_route_probe_pack=pack,
        )
        is False
    )
    assert int(sink.get("pass2_reject_step4_unreachable_stub_count", 0)) == 1
    gate = sink.get("pass2_last_transport_component_gate") or {}
    assert gate.get("reject_reason") == "step4_unreachable_component"
    assert scratch.placement_records == {}


def test_pass2_rejects_transport_disjoint_when_step4_prec_reachable_fluid_pipe() -> None:
    """Same geometry as belt case; fluid_pipe uses the fluid unreachable counter."""

    sink = p12_rp.new_pass2_route_probe_stats_sink()
    row_blocks = frozenset((x, 5) for x in range(6, 60))
    vertical_tunnel = frozenset((5, y) for y in range(6, 100))
    row_y99 = frozenset((x, 99) for x in range(6, 100))
    col_x99 = frozenset((99, y) for y in range(6, 100))
    margin_cell = (99, 5)
    trunk_span = frozenset((x, 5) for x in range(60, 100))
    mineable = frozenset(
        row_blocks
        | vertical_tunnel
        | row_y99
        | col_x99
        | trunk_span
        | frozenset({margin_cell, (5, 5)})
    )
    cells = {c: _fluid_cell(c[0], c[1]) for c in mineable}
    pack = p12_bc.Pass2RouteProbePack(
        mineable=mineable,
        asteroid=frozenset(),
        cells=cells,
        existing_layout_analysis=None,
        stats_sink=sink,
    )
    scratch = p12_bc.Pass12LayoutScratch(transport_kind="fluid_pipe")
    scratch.transport_cells = set(trunk_span)
    scratch.blocked_cells = set()
    cand = p12_bc.Pass12BundleCandidate(
        blocked_cells=frozenset({(4, 5)}) | row_blocks,
        new_transport=frozenset({(5, 5)}),
        stub_cell=(5, 5),
        extractor_cell=(4, 5),
        extension_facings=frozenset(),
        extractor_output_dir=(1, 0),
        placement_pass="pass2",
    )

    def is_ext(c: Coord) -> bool:
        return int(c[0]) >= 100

    assert (
        p12_bc.try_commit_pass2_bundle(
            scratch,
            cand,
            is_external=is_ext,
            pass2_route_probe_pack=pack,
        )
        is False
    )
    assert int(sink.get("pass2_reject_step4_unreachable_fluid_stub_count", 0)) == 1
    gate = sink.get("pass2_last_transport_component_gate") or {}
    assert gate.get("reject_reason") == "step4_unreachable_component"
    assert scratch.placement_records == {}


def test_pass2_transport_component_gate_disjoint_direct_when_no_exterior() -> None:
    """No cell reaches ``is_external`` → empty exterior_reachable; disjoint stub must fail."""

    ok, det = p12_rp.pass2_transport_stub_reaches_exterior_reachable_transport(
        (10, 0),
        transport_cells=frozenset({(0, 0), (1, 0), (2, 0), (10, 0)}),
        blocked_cells=frozenset(),
        is_external=lambda c: False,
        reachable_goal_count=0,
    )
    assert ok is False
    assert det["reject_reason"] == "step4_unreachable_component_no_goals"
    assert det["exterior_reachable_transport_cell_count"] == 0


def test_pass2_transport_component_gate_first_fragment_skip_direct() -> None:
    """Merged graph is stub-only: still skip (STEP4 may connect first island)."""

    ok, det = p12_rp.pass2_transport_stub_reaches_exterior_reachable_transport(
        (5, 0),
        transport_cells=frozenset({(5, 0)}),
        blocked_cells=frozenset(),
        is_external=lambda c: False,
        reachable_goal_count=0,
    )
    assert ok is True
    assert det["reject_reason"] == "skipped_no_exterior_reachable_transport"


def test_pass2_transport_component_gate_connected_skip_direct() -> None:
    """Interior-only map but stub shares a transport component with other cells → skip."""

    ok, det = p12_rp.pass2_transport_stub_reaches_exterior_reachable_transport(
        (2, 0),
        transport_cells=frozenset({(0, 0), (1, 0), (2, 0)}),
        blocked_cells=frozenset(),
        is_external=lambda c: False,
        reachable_goal_count=0,
    )
    assert ok is True
    assert det["reject_reason"] == "skipped_no_exterior_reachable_transport"


def test_pass2_rejects_disjoint_when_is_external_never_true_island_goal_fallback() -> None:
    """Interior-only: island goal fallback; disjoint stub fails step_cost precheck before gate."""

    sink = p12_rp.new_pass2_route_probe_stats_sink()
    mineable: frozenset[Coord] = frozenset(
        [(5, 5), (5, 6), (5, 7)] + [(x, 5) for x in range(10, 55)]
    )
    cells = {c: _fluid_cell(c[0], c[1]) for c in mineable}
    baseline_trunk = frozenset((x, 5) for x in range(10, 55))
    blocked_ring = frozenset({(4, 5), (6, 5), (5, 4), (4, 7), (6, 7), (5, 8)})
    pack = p12_bc.Pass2RouteProbePack(
        mineable=mineable,
        asteroid=frozenset(),
        cells=cells,
        existing_layout_analysis=None,
        stats_sink=sink,
    )
    scratch = p12_bc.Pass12LayoutScratch(transport_kind="fluid_pipe")
    scratch.transport_cells = set(baseline_trunk)
    scratch.blocked_cells = {(2, 0)}
    cand = p12_bc.Pass12BundleCandidate(
        blocked_cells=blocked_ring,
        new_transport=frozenset({(5, 5)}),
        stub_cell=(5, 5),
        extractor_cell=(4, 5),
        extension_facings=frozenset(),
        extractor_output_dir=(1, 0),
        placement_pass="pass2",
    )

    def is_ext(_c: Coord) -> bool:
        return False

    assert (
        p12_bc.try_commit_pass2_bundle(
            scratch,
            cand,
            is_external=is_ext,
            pass2_route_probe_pack=pack,
        )
        is False
    )
    assert int(sink.get("pass2_reject_step4_unreachable_fluid_stub_count", 0)) == 1
    gtrace = sink.get("pass2_probe_last_goal_trace") or {}
    assert int(gtrace.get("transport_cells_before_count") or 0) > 0
    assert "fallback_goal_source" not in gtrace
    assert "pass2_last_transport_component_gate" not in sink
    assert scratch.placement_records == {}
