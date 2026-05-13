"""Pass2 STEP4-aligned probe gate: provisional when route uncertain; STEP4 resolves."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass1_timeline_integration as p12_tl,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass12_bundle_commit as p12_bc,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass12_route_probe as p12_rp,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitState,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_merge_routing as s4mr,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_route_failure_detail as s4rfd,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
    final_validation as finval,
)


def _cells_for_mineable(mineable: frozenset[Coord]) -> dict[Coord, dict]:
    return {
        c: {
            "x": c[0],
            "y": c[1],
            "role": "inferred",
            "layout_kind": "asteroid_field",
            "surface": "shape",
        }
        for c in mineable
    }


def test_try_commit_pass2_rejects_no_route_when_probe_pack_absent() -> None:
    """Legacy Pass2 gate: no external reach and no pack → no commit."""

    scratch = p12_bc.Pass12LayoutScratch(transport_kind="shape_belt")
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
    assert (
        p12_bc.try_commit_pass2_bundle(
            scratch,
            cand,
            is_external=lambda c: c[0] >= 100,
            pass2_route_probe_pack=None,
        )
        is False
    )
    assert scratch.extractor_cells == set()


def test_try_commit_pass2_rejects_uncertain_when_step4_stub_isolated_geometry_belt() -> None:
    """Pass2 ``uncertain`` but four STEP4-illegal stub exits → do not commit (belt)."""

    sink = p12_rp.new_pass2_route_probe_stats_sink()
    mineable = frozenset(
        {
            (4, 5),
            (5, 5),
            (6, 5),
            (5, 4),
            (5, 6),
            (7, 5),
            (8, 5),
            (9, 5),
            (10, 5),
        }
    )
    asteroid: frozenset[Coord] = frozenset()
    cells = _cells_for_mineable(mineable)
    pack = p12_bc.Pass2RouteProbePack(
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        existing_layout_analysis=None,
        stats_sink=sink,
    )
    scratch = p12_bc.Pass12LayoutScratch(transport_kind="shape_belt")
    scratch.transport_cells = {(7, 5), (8, 5), (9, 5), (10, 5)}
    scratch.blocked_cells = {(6, 5), (5, 4), (5, 6)}
    cand = p12_bc.Pass12BundleCandidate(
        blocked_cells=frozenset({(4, 5)}),
        new_transport=frozenset({(5, 5)}),
        stub_cell=(5, 5),
        extractor_cell=(4, 5),
        extension_facings=frozenset(),
        extractor_output_dir=(1, 0),
        placement_pass="pass2",
    )
    assert (
        p12_bc.try_commit_pass2_bundle(
            scratch,
            cand,
            is_external=lambda c: c == (11, 5),
            pass2_route_probe_pack=pack,
        )
        is False
    )
    assert int(sink.get("pass2_reject_step4_stub_isolated_count", 0)) == 1
    assert scratch.placement_records == {}


def test_try_commit_pass2_rejects_uncertain_when_step4_stub_isolated_geometry_fluid_pipe() -> None:
    """Same T3 cage geometry with ``fluid_pipe`` transport_kind (role ``pipe``)."""

    sink = p12_rp.new_pass2_route_probe_stats_sink()
    mineable = frozenset(
        {
            (4, 5),
            (5, 5),
            (6, 5),
            (5, 4),
            (5, 6),
            (7, 5),
            (8, 5),
            (9, 5),
            (10, 5),
        }
    )
    asteroid: frozenset[Coord] = frozenset()
    cells = {
        c: {
            "x": c[0],
            "y": c[1],
            "role": "inferred",
            "layout_kind": "asteroid_field",
            "surface": "fluid",
        }
        for c in mineable
    }
    pack = p12_bc.Pass2RouteProbePack(
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        existing_layout_analysis=None,
        stats_sink=sink,
    )
    scratch = p12_bc.Pass12LayoutScratch(transport_kind="fluid_pipe")
    scratch.transport_cells = {(7, 5), (8, 5), (9, 5), (10, 5)}
    scratch.blocked_cells = {(6, 5), (5, 4), (5, 6)}
    cand = p12_bc.Pass12BundleCandidate(
        blocked_cells=frozenset({(4, 5)}),
        new_transport=frozenset({(5, 5)}),
        stub_cell=(5, 5),
        extractor_cell=(4, 5),
        extension_facings=frozenset(),
        extractor_output_dir=(1, 0),
        placement_pass="pass2",
    )
    assert (
        p12_bc.try_commit_pass2_bundle(
            scratch,
            cand,
            is_external=lambda c: c == (11, 5),
            pass2_route_probe_pack=pack,
        )
        is False
    )
    assert int(sink.get("pass2_reject_step4_stub_isolated_count", 0)) == 1


def test_pass2_probe_stub_isolated_geometry_helper_matches_four_blocked_neighbors() -> None:
    """Direct check: helper True iff four orthogonal exits are STEP4-blocked/hard."""

    mineable = frozenset({(5, 5), (7, 5), (8, 5)})
    cells = _cells_for_mineable(mineable)
    blocked = frozenset({(4, 5), (6, 5), (5, 4), (5, 6)})
    assert s4rfd.pass2_provisional_stub_step4_stub_isolated_geometry(
        stub_cell=(5, 5),
        want_role="belt",
        transport_kind="shape_belt",
        cells_base=cells,
        transport_probe=frozenset({(5, 5)}),
        blocked_probe=blocked,
        mineable=mineable,
        asteroid=frozenset(),
        is_external=lambda c: c[0] >= 100,
    )
    assert not s4rfd.pass2_provisional_stub_step4_stub_isolated_geometry(
        stub_cell=(5, 5),
        want_role="belt",
        transport_kind="shape_belt",
        cells_base=cells,
        transport_probe=frozenset({(5, 5), (6, 5)}),
        blocked_probe=frozenset({(4, 5), (5, 4), (5, 6)}),
        mineable=mineable,
        asteroid=frozenset(),
        is_external=lambda c: c[0] >= 100,
    )


def test_try_commit_pass2_succeeds_when_probe_pack_and_exterior_reachable_baseline() -> None:
    """Pass2RouteProbePack + exterior-reachable baseline: commit succeeds (replaces island path)."""

    sink = p12_rp.new_pass2_route_probe_stats_sink()
    mineable = frozenset({(2, 0), (5, 0), (6, 0), (7, 0), (8, 0), (9, 0), (10, 0), (11, 0)})
    asteroid: frozenset[Coord] = frozenset()
    cells = _cells_for_mineable(mineable)
    pack = p12_bc.Pass2RouteProbePack(
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        existing_layout_analysis=None,
        stats_sink=sink,
    )
    scratch = p12_bc.Pass12LayoutScratch(transport_kind="shape_belt")
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
    assert (
        p12_bc.try_commit_pass2_bundle(
            scratch,
            cand,
            is_external=lambda c: c == (12, 0),
            pass2_route_probe_pack=pack,
        )
        is True
    )
    p12_rp.finalize_pass2_route_probe_stats(sink)
    assert int(sink.get("pass2_probe_goal_eval_count", 0)) >= 1
    assert scratch.placement_records


def test_integrate_pass12_then_step4_no_quarantine_valid_layout() -> None:
    """Shape timeline: Pass2 may leave PROVISIONAL; STEP4 confirms; final validation is clean."""

    decoded: dict = {
        "BP": {
            "Entries": [{"X": x, "Y": 0, "T": "Layout_ShapeMiner"} for x in range(10, 13)]
            + [{"X": x, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0} for x in range(13, 30)]
        }
    }
    from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline

    mt = build_map_timeline(decoded)
    wm, fm = mt[0]["mining_map"], mt[-1]["mining_map"]
    is_ext = finval.external_predicate_for_mining_map(mt[1]["mining_map"])
    _p1, m2, stats = p12_tl.integrate_pass12_placement_into_working_map(
        working_map=wm, final_mining_map=fm, is_external=is_ext
    )
    pr = stats.get("placement_records") or {}
    assert pr
    assert all(rec.state == PlacementCommitState.PROVISIONAL_PLACED for rec in pr.values())
    assert "pass2_probe_goal_set_kind" in stats
    assert "reachable_component_sample_by_size" in stats
    r = s4mr.run_step4_merge_aware_routing(
        m2, final_mining_map=fm, is_external=is_ext, placement_records=pr
    )
    assert r.committed
    assert all(
        s == PlacementCommitState.ROUTED_CONFIRMED.value for s in r.placement_commit_by_id.values()
    )
    assert PlacementCommitState.QUARANTINED_UNROUTED.value not in r.placement_commit_by_id.values()
    cells = finval.cells_dict_from_mining_map(r.map_after_routing)
    qc, _pc = finval.count_placement_fsm_rows_on_cells(cells)
    assert qc == 0
    rep = finval.validate_final_mining_layout(r.map_after_routing)
    assert rep.connectivity_valid
    assert rep.disconnected_stub_count == 0


def test_pass2_rejects_disconnected_component_even_if_probe_uncertain() -> None:
    """Interior dead-end: uncertain + unreachable precheck → no commit, scratch unchanged."""

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
    baseline_transport = frozenset(scratch.transport_cells)
    baseline_records = dict(scratch.placement_records)
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
    assert frozenset(scratch.transport_cells) == baseline_transport
    assert scratch.placement_records == baseline_records
    assert int(sink.get("pass2_reject_step4_unreachable_component_count", 0)) >= 1
