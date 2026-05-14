from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import BBox
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    Pass1Result,
    ReconstructionDTO,
    RoutingStateSnapshot,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    TransportKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.placement_fsm import (
    apply_pass1_provisional_commits,
    apply_pass2_provisional_commits,
    assert_all_provisional_commits,
    assert_no_routed_confirmed,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement import (
    build_pass2_blocked_set,
    run_pass2_internal_fill,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement.pass1_outer import (
    run_pass1_outer_placement,
)


def _mineable_square(lo: int = 2, hi: int = 4) -> tuple[tuple[int, int], ...]:
    return tuple((x, y) for x in range(lo, hi + 1) for y in range(lo, hi + 1))


def _mineable_square_5() -> tuple[tuple[int, int], ...]:
    return tuple((x, y) for x in range(1, 6) for y in range(1, 6))


def _ctx_with_routing() -> SolverRunContext:
    return SolverRunContext(
        run_id="test",
        reconstruction=ReconstructionDTO(),
        routing_state=RoutingStateSnapshot(final_route_cells=((9, 9),)),
    )


def _reco_3x3_void() -> ReconstructionDTO:
    cells = _mineable_square()
    return ReconstructionDTO(
        mineable_placement_cells=cells,
        full_barrier_cells=(),
        belt_cells=(),
        pipe_cells=(),
        asteroid_bbox=BBox(min_x=2, min_y=2, max_x=4, max_y=4),
        external_margin=3,
        external_margin_bbox_source="mineable",
    )


def _reco_fluid_pipe_hint() -> ReconstructionDTO:
    cells = _mineable_square()
    return ReconstructionDTO(
        mineable_placement_cells=cells,
        full_barrier_cells=((5, 0),),
        belt_cells=(),
        pipe_cells=((5, 0),),
        asteroid_bbox=BBox(min_x=2, min_y=2, max_x=4, max_y=4),
        external_margin=3,
        external_margin_bbox_source="mineable",
    )


def _reco_5x5_with_center_barrier() -> ReconstructionDTO:
    cells = _mineable_square_5()
    return ReconstructionDTO(
        mineable_placement_cells=cells,
        full_barrier_cells=((3, 3),),
        belt_cells=(),
        pipe_cells=(),
        asteroid_bbox=BBox(min_x=1, min_y=1, max_x=5, max_y=5),
        external_margin=3,
        external_margin_bbox_source="mineable",
    )


def test_pass2_runs_on_empty_pass1() -> None:
    ctx = SolverRunContext(run_id="r2", reconstruction=_reco_3x3_void())
    p1 = Pass1Result()
    p2 = run_pass2_internal_fill(ctx, p1)
    assert p2.provisional_placements
    assert_all_provisional_commits(p2.placement_commit_entries)
    assert_no_routed_confirmed(p2.placement_commit_entries)


def test_pass2_cannot_overlap_pass1_geometry() -> None:
    ctx = SolverRunContext(run_id="r2", reconstruction=_reco_5x5_with_center_barrier())
    p1 = run_pass1_outer_placement(ctx, ctx.reconstruction)
    p2 = run_pass2_internal_fill(ctx, p1)
    pass1_cells = set(p1.occupied_cells)
    for b in p2.provisional_placements:
        cells = {b.extractor.cell, b.output_stub.cell} | {e.cell for e in b.extensions}
        assert cells.isdisjoint(pass1_cells)


def test_pass2_respects_full_barrier_in_blocked_set() -> None:
    ctx = SolverRunContext(run_id="r2", reconstruction=_reco_5x5_with_center_barrier())
    p1 = run_pass1_outer_placement(ctx, ctx.reconstruction)
    blocked = build_pass2_blocked_set(p1, ctx.reconstruction)
    assert (3, 3) in blocked
    p2 = run_pass2_internal_fill(ctx, p1)
    for b in p2.provisional_placements:
        assert (3, 3) not in {b.extractor.cell, b.output_stub.cell}
        assert all(e.cell != (3, 3) for e in b.extensions)


def test_pass2_occupied_delta_is_only_pass2_bundles() -> None:
    ctx = SolverRunContext(run_id="r2", reconstruction=_reco_5x5_with_center_barrier())
    p1 = run_pass1_outer_placement(ctx, ctx.reconstruction)
    p2 = run_pass2_internal_fill(ctx, p1)
    expected: set[tuple[int, int]] = set()
    for b in p2.provisional_placements:
        expected.add(b.extractor.cell)
        expected.add(b.output_stub.cell)
        for e in b.extensions:
            expected.add(e.cell)
    assert set(p2.blocked_cells_delta) == expected


def test_pass2_does_not_read_final_route_cells() -> None:
    ctx = _ctx_with_routing()
    ctx = SolverRunContext(
        run_id=ctx.run_id,
        reconstruction=_reco_5x5_with_center_barrier(),
        routing_state=ctx.routing_state,
    )
    before = ctx.routing_state.final_route_cells
    p1 = run_pass1_outer_placement(ctx, ctx.reconstruction)
    run_pass2_internal_fill(ctx, p1)
    assert ctx.routing_state.final_route_cells == before


def test_pass2_deterministic() -> None:
    ctx = SolverRunContext(run_id="r2", reconstruction=_reco_5x5_with_center_barrier())
    p1 = run_pass1_outer_placement(ctx, ctx.reconstruction)
    a = run_pass2_internal_fill(ctx, p1)
    b = run_pass2_internal_fill(ctx, p1)
    assert a == b


def test_apply_pass2_commits_merges_into_context() -> None:
    ctx = SolverRunContext(run_id="r2", reconstruction=_reco_5x5_with_center_barrier())
    p1 = run_pass1_outer_placement(ctx, ctx.reconstruction)
    p2 = run_pass2_internal_fill(ctx, p1)
    merged = apply_pass2_provisional_commits(ctx, p2)
    for pid, st in p2.placement_commit_entries:
        assert merged.placement_commit_by_id[pid] is st


def test_pass2_route_overlap_not_applied_no_final_route_in_blocked() -> None:
    """§8.5: Pass2 blocked set does not subtract ``final_route_cells``."""

    ctx = _ctx_with_routing()
    ctx = SolverRunContext(
        run_id="r2",
        reconstruction=_reco_5x5_with_center_barrier(),
        routing_state=ctx.routing_state,
    )
    p1 = run_pass1_outer_placement(ctx, ctx.reconstruction)
    blocked = build_pass2_blocked_set(p1, ctx.reconstruction)
    assert (9, 9) not in blocked


def test_pass1_places_at_least_one_bundle_on_open_patch() -> None:
    ctx = SolverRunContext(run_id="r1", reconstruction=_reco_3x3_void())
    r = run_pass1_outer_placement(ctx, ctx.reconstruction)
    assert len(r.placements) >= 1


def test_pass1_one_stub_per_extractor() -> None:
    ctx = SolverRunContext(run_id="r1", reconstruction=_reco_3x3_void())
    r = run_pass1_outer_placement(ctx, ctx.reconstruction)
    for b in r.placements:
        assert b.output_stub.extractor_placement_id == b.extractor.placement_id
        assert b.output_stub.transport_kind == b.extractor.transport_kind


def test_pass1_extensions_exclude_output_direction_and_max_three() -> None:
    ctx = SolverRunContext(run_id="r1", reconstruction=_reco_3x3_void())
    r = run_pass1_outer_placement(ctx, ctx.reconstruction)
    for b in r.placements:
        ex, stub = b.extractor.cell, b.output_stub.cell
        odir = (stub[0] - ex[0], stub[1] - ex[1])
        assert abs(odir[0]) + abs(odir[1]) == 1
        assert len(b.extensions) <= 3
        for ext in b.extensions:
            pdir = (ext.parent_cell[0] - ext.cell[0], ext.parent_cell[1] - ext.cell[1])
            assert pdir != (0, 0)
            assert abs(pdir[0]) + abs(pdir[1]) == 1
            assert ext.cell != stub


def test_pass1_extension_parent_adjacent_cardinal() -> None:
    ctx = SolverRunContext(run_id="r1", reconstruction=_reco_3x3_void())
    r = run_pass1_outer_placement(ctx, ctx.reconstruction)
    dirs4 = {(0, -1), (1, 0), (0, 1), (-1, 0)}
    for b in r.placements:
        for ext in b.extensions:
            d = (ext.parent_cell[0] - ext.cell[0], ext.parent_cell[1] - ext.cell[1])
            assert d in dirs4


def test_pass1_occupied_cells_only_bundle_geometry() -> None:
    ctx = SolverRunContext(run_id="r1", reconstruction=_reco_3x3_void())
    r = run_pass1_outer_placement(ctx, ctx.reconstruction)
    expected: set[tuple[int, int]] = set()
    for b in r.placements:
        expected.add(b.extractor.cell)
        expected.add(b.output_stub.cell)
        for ext in b.extensions:
            expected.add(ext.cell)
    assert set(r.occupied_cells) == expected


def test_pass1_all_commits_provisional_no_routed() -> None:
    ctx = SolverRunContext(run_id="r1", reconstruction=_reco_3x3_void())
    r = run_pass1_outer_placement(ctx, ctx.reconstruction)
    assert_all_provisional_commits(r.placement_commit_entries)
    assert_no_routed_confirmed(r.placement_commit_entries)


def test_pass1_deterministic() -> None:
    ctx = SolverRunContext(run_id="r1", reconstruction=_reco_3x3_void())
    a = run_pass1_outer_placement(ctx, ctx.reconstruction)
    b = run_pass1_outer_placement(ctx, ctx.reconstruction)
    assert a == b


def test_pass1_does_not_write_final_route_cells() -> None:
    ctx = _ctx_with_routing()
    before = ctx.routing_state.final_route_cells
    run_pass1_outer_placement(ctx, _reco_3x3_void())
    assert ctx.routing_state.final_route_cells == before


def test_pass1_fluid_pipe_transport_kind_when_only_pipe_hint() -> None:
    ctx = SolverRunContext(run_id="r1", reconstruction=_reco_fluid_pipe_hint())
    r = run_pass1_outer_placement(ctx, ctx.reconstruction)
    assert r.placements
    assert all(p.extractor.transport_kind is TransportKind.FLUID_PIPE for p in r.placements)


def test_apply_pass1_commits_merges_into_context() -> None:
    ctx = SolverRunContext(run_id="r1", reconstruction=_reco_3x3_void())
    r = run_pass1_outer_placement(ctx, ctx.reconstruction)
    merged = apply_pass1_provisional_commits(ctx, r)
    for pid, st in r.placement_commit_entries:
        assert merged.placement_commit_by_id[pid] is st
