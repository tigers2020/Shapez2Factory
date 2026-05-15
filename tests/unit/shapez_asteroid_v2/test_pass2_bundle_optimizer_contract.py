"""Pass2 bundle packing optimizer: set packing, fallback, import boundaries, Pass2 contracts."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import BBox
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ReconstructionDTO,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    TransportKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement import (
    bundle_candidate,
    pass1_outer,
    pass2_bundle_optimizer,
    pass2_internal,
    pass2_route_probe,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement.placement_fsm import (
    assert_all_provisional_commits,
    assert_no_routed_confirmed,
)

Pass2BundleCandidate = bundle_candidate.Pass2BundleCandidate
Pass2PackingInput = pass2_bundle_optimizer.Pass2PackingInput
Pass2RouteProbe = pass2_route_probe.Pass2RouteProbe
optimize_pass2_bundle_packing = pass2_bundle_optimizer.optimize_pass2_bundle_packing
pass2_candidate_conflict_cells = pass2_bundle_optimizer.pass2_candidate_conflict_cells
pass2_candidate_occupied_cells = pass2_bundle_optimizer.pass2_candidate_occupied_cells
probe_pass2_stub_route = pass2_route_probe.probe_pass2_stub_route
select_pass2_bundles_greedy_fallback = pass2_bundle_optimizer.select_pass2_bundles_greedy_fallback
run_pass2_internal_fill = pass2_internal.run_pass2_internal_fill
run_pass1_outer_placement = pass1_outer.run_pass1_outer_placement


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def _cand(
    *,
    cid: str,
    scan_index: int,
    extractor: tuple[int, int],
    stub: tuple[int, int],
    score: float,
    extension_cells: tuple[tuple[tuple[int, int], tuple[int, int], tuple[int, int]], ...] = (),
    out_dir: tuple[int, int] = (0, 1),
) -> Pass2BundleCandidate:
    return Pass2BundleCandidate(
        candidate_id=cid,
        scan_index=scan_index,
        extractor_cell=extractor,
        output_direction=out_dir,
        output_stub_cell=stub,
        extension_cells=extension_cells,
        transport_kind=TransportKind.SHAPE_BELT,
        score=score,
        reject_reason=None,
    )


def test_overlapping_candidates_not_both_selected() -> None:
    a = _cand(cid="a", scan_index=0, extractor=(0, 0), stub=(0, 1), score=10.0)
    b = _cand(cid="b", scan_index=1, extractor=(0, 0), stub=(1, 0), score=20.0)
    inp = Pass2PackingInput(candidates=(a, b), blocked_cells=frozenset())
    r = optimize_pass2_bundle_packing(inp)
    occ_union: set[tuple[int, int]] = set()
    for c in r.selected:
        occ_union |= set(pass2_candidate_occupied_cells(c))
    assert len(r.selected) <= 1
    for c in r.selected:
        o = pass2_candidate_occupied_cells(c)
        assert len(o & occ_union) == len(o)


def test_non_overlapping_candidates_both_selected() -> None:
    a = _cand(cid="a", scan_index=0, extractor=(0, 0), stub=(0, 1), score=10.0)
    b = _cand(cid="b", scan_index=1, extractor=(5, 5), stub=(5, 6), score=20.0)
    inp = Pass2PackingInput(candidates=(a, b), blocked_cells=frozenset())
    r = optimize_pass2_bundle_packing(inp)
    assert len(r.selected) == 2


def test_stub_conflicts_with_other_extractor_cell() -> None:
    a = _cand(cid="a", scan_index=0, extractor=(0, 0), stub=(0, 1), score=100.0)
    b = _cand(
        cid="b",
        scan_index=1,
        extractor=(0, 1),
        stub=(0, 2),
        score=50.0,
    )
    inp = Pass2PackingInput(candidates=(a, b), blocked_cells=frozenset())
    r = optimize_pass2_bundle_packing(inp)
    assert len(r.selected) == 1


def test_stub_conflicts_with_other_extension_cell() -> None:
    ext_a = (((1, 0), (0, 0), (1, 0)),)
    a = _cand(
        cid="a",
        scan_index=0,
        extractor=(0, 0),
        stub=(0, 1),
        score=100.0,
        extension_cells=ext_a,
    )
    b = _cand(cid="b", scan_index=1, extractor=(1, 0), stub=(1, 1), score=50.0)
    inp = Pass2PackingInput(candidates=(a, b), blocked_cells=frozenset())
    r = optimize_pass2_bundle_packing(inp)
    assert len(r.selected) == 1


def test_fallback_when_cp_model_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pass2_bundle_optimizer, "ortools_cp_model", None)
    a = _cand(cid="a", scan_index=0, extractor=(0, 0), stub=(0, 1), score=10.0)
    inp = Pass2PackingInput(candidates=(a,), blocked_cells=frozenset(), use_cp_sat=True)
    r = optimize_pass2_bundle_packing(inp)
    assert r.optimizer_name == "greedy_fallback"
    assert r.fallback_used is True


def test_greedy_fallback_deterministic_repeat() -> None:
    cands = (
        _cand(cid="z", scan_index=2, extractor=(0, 0), stub=(0, 1), score=5.0),
        _cand(cid="y", scan_index=1, extractor=(3, 3), stub=(3, 4), score=10.0),
        _cand(cid="x", scan_index=0, extractor=(6, 6), stub=(6, 7), score=10.0),
    )
    inp = Pass2PackingInput(candidates=cands, blocked_cells=frozenset(), use_cp_sat=False)
    r1 = optimize_pass2_bundle_packing(inp)
    r2 = optimize_pass2_bundle_packing(inp)
    assert r1.selected == r2.selected


def test_selected_order_deterministic_sorted() -> None:
    a = _cand(cid="a", scan_index=1, extractor=(0, 0), stub=(0, 1), score=10.0)
    b = _cand(cid="b", scan_index=0, extractor=(5, 5), stub=(5, 6), score=10.0)
    inp = Pass2PackingInput(candidates=(a, b), blocked_cells=frozenset(), use_cp_sat=False)
    r = optimize_pass2_bundle_packing(inp)
    keys = [
        (c.scan_index, c.extractor_cell, c.output_direction, c.candidate_id) for c in r.selected
    ]
    assert keys == sorted(keys)


def test_packing_result_metadata_fields() -> None:
    a = _cand(cid="a", scan_index=0, extractor=(0, 0), stub=(0, 1), score=1.5)
    inp = Pass2PackingInput(candidates=(a,), blocked_cells=frozenset(), use_cp_sat=False)
    r = optimize_pass2_bundle_packing(inp)
    assert r.candidate_count == 1
    assert r.selected_count == 1
    assert r.fallback_used is False
    assert isinstance(r.conflict_constraint_count, int)
    assert r.objective_value >= 0


def test_run_pass2_internal_fill_provisional_only() -> None:
    mineable = tuple((x, y) for x in range(20, 26) for y in range(20, 26) if (x, y) != (22, 22))
    bbox = BBox(min_x=20, min_y=20, max_x=25, max_y=25)
    shell = tuple(
        sorted(
            (
                c
                for c in mineable
                if min(
                    c[0] - bbox.min_x,
                    bbox.max_x - c[0],
                    c[1] - bbox.min_y,
                    bbox.max_y - c[1],
                )
                == 0
            ),
            key=lambda c: (c[1], c[0]),
        )
    )
    barrier = tuple({*mineable, (22, 22)})
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=shell,
        full_barrier_cells=barrier,
        belt_cells=mineable,
        asteroid_bbox=bbox,
    )
    ctx = SolverRunContext(run_id="p2_opt_contract", reconstruction=recon)
    p1 = run_pass1_outer_placement(ctx, recon)
    p2 = run_pass2_internal_fill(ctx, p1)
    if p2.placement_commit_entries:
        assert_all_provisional_commits(p2.placement_commit_entries)
        assert_no_routed_confirmed(p2.placement_commit_entries)


def test_pass2_modules_do_not_reference_final_route_cells() -> None:
    root = _repo_root()
    for rel in (
        "django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass2_internal.py",
        "django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass2_bundle_optimizer.py",
        "django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/pass2_route_probe.py",
    ):
        text = (root / rel).read_text(encoding="utf-8")
        assert "final_route_cells" not in text
        assert "asteroid_mining_layout_v2.routing" not in text


def test_pass2_bundle_optimizer_import_boundaries() -> None:
    root = _repo_root()
    path = root / (
        "django_apps/shapez_asteroid/services/asteroid_mining_layout_v2/placement/"
        "pass2_bundle_optimizer.py"
    )
    text = path.read_text(encoding="utf-8")
    assert "merge_aware_router" not in text
    assert "trunk_seed" not in text
    legacy = "django_apps.shapez_asteroid.services.asteroid_mining_layout."
    for i, line in enumerate(text.splitlines(), 1):
        s = line.split("#", 1)[0]
        if legacy in s and "asteroid_mining_layout_v2" not in s:
            pytest.fail(f"v1 layout reference at {path}:{i}: {line.strip()}")
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("import ") or stripped.startswith("from "):
            if re.search(r"\breplay\b", stripped):
                pytest.fail(f"replay import at {path}:{i}: {line.strip()}")
            if "merge_aware_router" in stripped or "trunk_seed" in stripped:
                pytest.fail(f"forbidden routing import at {path}:{i}: {line.strip()}")


def test_cp_sat_prefers_b_and_c_over_a_when_installed() -> None:
    pytest.importorskip("ortools")
    # A: high score, spans (0,0),(1,0),(2,0). B and C: lower score, disjoint from each other.
    ext_a = (((2, 0), (1, 0), (1, 0)),)
    a = _cand(
        cid="A",
        scan_index=0,
        extractor=(0, 0),
        stub=(1, 0),
        score=100.0,
        extension_cells=ext_a,
        out_dir=(1, 0),
    )
    b = _cand(cid="B", scan_index=1, extractor=(0, 0), stub=(0, 1), score=60.0, out_dir=(0, 1))
    c = _cand(cid="C", scan_index=2, extractor=(2, 0), stub=(2, 1), score=60.0, out_dir=(0, 1))
    inp = Pass2PackingInput(candidates=(a, b, c), blocked_cells=frozenset(), use_cp_sat=True)
    r = optimize_pass2_bundle_packing(inp)
    assert r.optimizer_name == "cp_sat"
    assert not r.fallback_used
    ids = {x.candidate_id for x in r.selected}
    assert ids == {"B", "C"}, ids
    assert r.objective_value == int(round(60.0 * 1000)) * 2


def test_select_pass2_bundles_greedy_fallback_order() -> None:
    a = _cand(cid="a", scan_index=0, extractor=(0, 0), stub=(0, 1), score=1.0)
    b = _cand(cid="b", scan_index=0, extractor=(2, 0), stub=(2, 1), score=2.0)
    out = select_pass2_bundles_greedy_fallback((a, b), blocked_cells=frozenset(), route_probes=None)
    assert len(out) == 2


def test_pass2_candidate_conflict_cells_includes_shadow_path() -> None:
    a = _cand(cid="a", scan_index=0, extractor=(0, 0), stub=(0, 1), score=10.0)
    probes = {
        "a": Pass2RouteProbe(
            candidate_id="a",
            reachable=True,
            path_cells=((5, 5), (5, 6)),
            goal_cell=(5, 7),
            reject_reason=None,
        )
    }
    cells = pass2_candidate_conflict_cells(a, blocked_cells=frozenset(), route_probes=probes)
    assert (5, 5) in cells and (5, 6) in cells
    assert (5, 7) not in cells
    assert (0, 1) not in {(5, 5), (5, 6)}


def test_cp_sat_shadow_corridor_overlap_selects_at_most_one() -> None:
    pytest.importorskip("ortools")
    a = _cand(cid="A", scan_index=0, extractor=(0, 0), stub=(0, 1), score=100.0)
    b = _cand(cid="B", scan_index=1, extractor=(10, 0), stub=(10, 1), score=100.0)
    shared = (5, 5)
    probes = {
        "A": Pass2RouteProbe(
            candidate_id="A",
            reachable=True,
            path_cells=(shared,),
            goal_cell=(0, 10),
            reject_reason=None,
        ),
        "B": Pass2RouteProbe(
            candidate_id="B",
            reachable=True,
            path_cells=(shared,),
            goal_cell=(10, 10),
            reject_reason=None,
        ),
    }
    inp = Pass2PackingInput(
        candidates=(a, b), blocked_cells=frozenset(), route_probes=probes, use_cp_sat=True
    )
    r = optimize_pass2_bundle_packing(inp)
    assert len(r.selected) == 1


def test_greedy_fallback_respects_shadow_corridor() -> None:
    a = _cand(cid="A", scan_index=0, extractor=(0, 0), stub=(0, 1), score=10.0)
    b = _cand(cid="B", scan_index=1, extractor=(10, 0), stub=(10, 1), score=9.0)
    shared = (5, 5)
    probes = {
        "A": Pass2RouteProbe(
            candidate_id="A",
            reachable=True,
            path_cells=(shared,),
            goal_cell=(0, 9),
            reject_reason=None,
        ),
        "B": Pass2RouteProbe(
            candidate_id="B",
            reachable=True,
            path_cells=(shared,),
            goal_cell=(10, 9),
            reject_reason=None,
        ),
    }
    out = select_pass2_bundles_greedy_fallback(
        (a, b), blocked_cells=frozenset(), route_probes=probes
    )
    assert len(out) == 1


def test_probe_pass2_stub_route_unreachable_enclosed_dead_end() -> None:
    """Stub surrounded by barrier (non-belt) and extractor; BFS cannot reach margin or trunk."""

    mineable = ((400, 200), (401, 200))
    bbox = BBox(min_x=400, min_y=200, max_x=401, max_y=200)
    frame: set[tuple[int, int]] = set()
    for x in range(399, 403):
        for y in range(199, 202):
            c = (x, y)
            if c not in mineable:
                frame.add(c)
    barrier = tuple(sorted(set(mineable) | frame))
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=mineable,
        full_barrier_cells=barrier,
        belt_cells=mineable,
        asteroid_bbox=bbox,
        external_margin=3,
    )
    ctx = SolverRunContext(run_id="probe_dead", reconstruction=recon)
    cand = _cand(
        cid="dead",
        scan_index=0,
        extractor=(400, 200),
        stub=(401, 200),
        score=1.0,
        out_dir=(1, 0),
    )
    pr = probe_pass2_stub_route(
        cand,
        pass1_fixed_cells=frozenset(),
        reconstruction=recon,
        ctx=ctx,
    )
    assert not pr.reachable
    assert pr.reject_reason == "pass2_stub_not_externally_reachable"
    assert pr.path_cells == ()
    assert pr.goal_cell is None


def test_probe_path_cells_exclude_stub_and_goal() -> None:
    mineable = tuple((x, y) for x in range(10, 15) for y in range(10, 15))
    bbox = BBox(min_x=10, min_y=10, max_x=14, max_y=14)
    barrier = tuple(mineable)
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=(),
        full_barrier_cells=barrier,
        belt_cells=mineable,
        asteroid_bbox=bbox,
        external_margin=3,
    )
    ctx = SolverRunContext(run_id="probe_path", reconstruction=recon)
    cand = _cand(
        cid="p",
        scan_index=0,
        extractor=(12, 12),
        stub=(12, 11),
        score=1.0,
        out_dir=(0, -1),
    )
    pr = probe_pass2_stub_route(
        cand,
        pass1_fixed_cells=frozenset(),
        reconstruction=recon,
        ctx=ctx,
    )
    assert pr.reachable
    assert pr.goal_cell is not None
    assert cand.output_stub_cell not in pr.path_cells
    assert pr.goal_cell not in pr.path_cells


def test_pass2_blocked_cells_delta_is_equipment_only() -> None:
    mineable = tuple((x, y) for x in range(20, 26) for y in range(20, 26) if (x, y) != (22, 22))
    bbox = BBox(min_x=20, min_y=20, max_x=25, max_y=25)
    shell = tuple(
        sorted(
            (
                c
                for c in mineable
                if min(
                    c[0] - bbox.min_x,
                    bbox.max_x - c[0],
                    c[1] - bbox.min_y,
                    bbox.max_y - c[1],
                )
                == 0
            ),
            key=lambda c: (c[1], c[0]),
        )
    )
    barrier = tuple({*mineable, (22, 22)})
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=shell,
        full_barrier_cells=barrier,
        belt_cells=mineable,
        asteroid_bbox=bbox,
    )
    ctx = SolverRunContext(run_id="p2_delta_contract", reconstruction=recon)
    p1 = run_pass1_outer_placement(ctx, recon)
    p2 = run_pass2_internal_fill(ctx, p1)
    equip: set[tuple[int, int]] = set()
    for b in p2.provisional_placements:
        equip.add(b.extractor.cell)
        equip.add(b.output_stub.cell)
        for ext in b.extensions:
            equip.add(ext.cell)
    assert set(p2.blocked_cells_delta) == equip
