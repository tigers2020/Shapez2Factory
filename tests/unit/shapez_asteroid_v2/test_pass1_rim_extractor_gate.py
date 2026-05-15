"""Pass1 extractor core must be a mineable rim cell (``perimeter_depth == 0``)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain import (
    mining_void_topology as _mining_void_topology,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import BBox
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ReconstructionDTO,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement.pass1_outer import (
    compute_mineable_perimeter_depth_by_cell,
    is_pass1_rim_extractor_cell,
    run_pass1_outer_placement,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.trace_collector import (
    TraceCollector,
)


def _ctx(rid: str = "rim_gate") -> SolverRunContext:
    return SolverRunContext(run_id=rid, reconstruction=ReconstructionDTO())


def test_perimeter_depth_ring_with_inner_patch() -> None:
    ring: list[tuple[int, int]] = []
    for x in range(30, 34):
        for y in range(30, 34):
            if x in (30, 33) or y in (30, 33):
                ring.append((x, y))
    inner = {(31, 31), (32, 31), (31, 32), (32, 32)}
    mineable = frozenset(ring) | inner
    depth = compute_mineable_perimeter_depth_by_cell(mineable)
    for c in inner:
        assert depth[c] >= 1
    for c in mineable - inner:
        assert depth[c] == 0
    assert is_pass1_rim_extractor_cell((31, 31), depth) is False
    assert is_pass1_rim_extractor_cell((30, 31), depth) is True


def test_pass1_consider_extract_marks_interior_reject_and_skips_probe() -> None:
    """Solid 12×12 patch: interior cells scanned as extractors get rim reject (no output probe)."""

    n = 12
    mineable = tuple((x, y) for x in range(100, 100 + n) for y in range(100, 100 + n))
    bbox = BBox(min_x=100, min_y=100, max_x=100 + n - 1, max_y=100 + n - 1)
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=mineable,
        full_barrier_cells=mineable,
        belt_cells=mineable,
        asteroid_bbox=bbox,
        external_margin=3,
        external_margin_bbox_source="mineable",
    )
    events: list[dict[object, object]] = []
    run_pass1_outer_placement(
        _ctx(),
        recon,
        replay_events=events,
        replay_event_cap=2000,
        trace=TraceCollector("rim_gate"),
    )
    rejects = [
        e
        for e in events
        if e.get("kind") == "consider_extract"
        and e.get("reject_reason") == "pass1_extractor_not_on_external_rim"
    ]
    assert len(rejects) >= 8
    assert all(int(e["perimeter_depth"]) >= 1 for e in rejects)
    for e in rejects[:5]:
        ext = tuple(e["extractor_cell"])
        assert not any(
            pe.get("kind") == "probe_output" and tuple(pe["extractor_cell"]) == ext for pe in events
        )
    ends = [e for e in events if e.get("kind") == "pass1_end"]
    assert len(ends) == 1
    assert ends[0].get("pass1_extractor_rim_only") is True
    assert ends[0].get("pass1_stop_reason") == "mineable_ordered_scan_complete"
    rj = ends[0].get("reject_count_by_reason") or {}
    assert rj.get("pass1_extractor_not_on_external_rim", 0) == len(rejects)


def test_pass1_committed_extractors_are_rim_only() -> None:
    mineable = tuple((x, y) for x in range(20, 26) for y in range(20, 26) if (x, y) != (22, 22))
    bbox = BBox(min_x=20, min_y=20, max_x=25, max_y=25)
    barrier = tuple({*mineable, (22, 22)})
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=tuple(
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
        ),
        full_barrier_cells=barrier,
        belt_cells=mineable,
        asteroid_bbox=bbox,
        external_margin=3,
        external_margin_bbox_source="mineable",
    )
    p1 = run_pass1_outer_placement(
        _ctx("rim_only_box"), recon, trace=TraceCollector("rim_only_box")
    )
    perm_fb = frozenset(recon.belt_cells) | frozenset(recon.pipe_cells)
    outer_rim = frozenset(
        _mining_void_topology.compute_mining_void_topology(
            frozenset(mineable), bbox, recon.external_margin, perm_fb
        ).outer_rim_mineable_cells
    )
    for b in p1.placements:
        assert b.extractor.cell in outer_rim


def test_pass1_extension_may_be_deeper_than_extractor_on_thick_patch() -> None:
    """Rim extractor (depth 0); straight chain may occupy interior cells (depth >= 2)."""

    mineable = tuple((x, y) for x in range(20, 25) for y in range(20, 25))
    bbox = BBox(min_x=20, min_y=20, max_x=24, max_y=24)
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=mineable,
        full_barrier_cells=mineable,
        belt_cells=mineable,
        asteroid_bbox=bbox,
        external_margin=3,
        external_margin_bbox_source="mineable",
    )
    depth = compute_mineable_perimeter_depth_by_cell(frozenset(mineable))
    p1 = run_pass1_outer_placement(_ctx("thick5"), recon, trace=TraceCollector("thick5"))
    assert p1.placements
    assert any(
        depth.get(b.extractor.cell) == 0 and any(depth.get(e.cell, -1) >= 2 for e in b.extensions)
        for b in p1.placements
    )


def test_pass1_hole_adjacent_mineable_not_used_as_extractor_core() -> None:
    """Central void: mineable cells bordering only the internal void are not Pass1 cores."""

    mineable = tuple((x, y) for x in range(20, 26) for y in range(20, 26) if (x, y) != (22, 22))
    bbox = BBox(min_x=20, min_y=20, max_x=25, max_y=25)
    barrier = tuple({*mineable, (22, 22)})
    topo = _mining_void_topology.compute_mining_void_topology(
        frozenset(mineable), bbox, 3, frozenset()
    )
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=mineable,
        full_barrier_cells=barrier,
        belt_cells=(),
        pipe_cells=(),
        outer_rim_mineable_cells=topo.outer_rim_mineable_cells,
        internal_hole_rim_mineable_cells=topo.internal_hole_rim_mineable_cells,
        asteroid_bbox=bbox,
        external_margin=3,
        external_margin_bbox_source="mineable",
    )
    hole_touch = {(22, 21), (21, 22), (23, 22), (22, 23)}
    events: list[dict[str, object]] = []
    p1 = run_pass1_outer_placement(
        _ctx("donut1"),
        recon,
        replay_events=events,
        replay_event_cap=2000,
        trace=TraceCollector("donut1"),
    )
    for b in p1.placements:
        assert b.extractor.cell not in hole_touch
    rejects = [
        e
        for e in events
        if e.get("kind") == "consider_extract" and tuple(e["extractor_cell"]) in hole_touch
    ]
    assert rejects
    assert all(e.get("internal_hole_rim") is True for e in rejects)
    assert all(e.get("external_rim") is False for e in rejects)
    assert all(e.get("reject_reason") == "pass1_extractor_not_on_external_rim" for e in rejects)
