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
    """Same spine as provisional belt test: fluid stub can BFS-reach trunk/margin goals."""

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
        is True
    )
    assert int(sink.get("pass2_reject_step4_unreachable_fluid_stub_count", 0)) == 0
    assert scratch.placement_records


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
    """Belt keeps ``pass2_reject_step4_unreachable_stub`` (exhausted only, not fluid counter)."""

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
