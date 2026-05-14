"""Pass1/Pass2 must only emit ``PROVISIONAL_PLACED`` until STEP 4 (§9.6)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import BBox
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    Pass1Result,
    ReconstructionDTO,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    PlacementCommitState,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement import (
    run_pass1_outer_placement,
    run_pass2_internal_fill,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement.placement_fsm import (
    assert_all_provisional_commits,
    assert_no_routed_confirmed,
)


def _ctx() -> SolverRunContext:
    return SolverRunContext(run_id="contract", reconstruction=ReconstructionDTO())


def test_pass1_pass2_commit_entries_are_provisional_only() -> None:
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
    ctx = _ctx()
    p1 = run_pass1_outer_placement(ctx, recon)
    entries1 = p1.placement_commit_entries
    if entries1:
        assert_all_provisional_commits(entries1)
        assert_no_routed_confirmed(entries1)
    p2 = run_pass2_internal_fill(ctx, p1)
    entries2 = p2.placement_commit_entries
    if entries2:
        assert_all_provisional_commits(entries2)
        assert_no_routed_confirmed(entries2)


def test_manual_pass1_result_never_routed_before_step4() -> None:
    ctx = _ctx()
    p1 = Pass1Result(
        placement_commit_entries=(("p", PlacementCommitState.PROVISIONAL_PLACED),),
    )
    assert p1.placement_commit_entries
    assert_all_provisional_commits(p1.placement_commit_entries)
    assert_no_routed_confirmed(p1.placement_commit_entries)
    _ = ctx


def test_pass1_outer_first_order_includes_interior_patch_cells_in_scan() -> None:
    """Pass1 iterates ``mineable_placement_cells``; interior voids must appear in scan order."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement import (
        pass1_outer as pass1o,
    )

    ring: list[tuple[int, int]] = []
    for x in range(30, 34):
        for y in range(30, 34):
            if x in (30, 33) or y in (30, 33):
                ring.append((x, y))
    ring_t = tuple(sorted(ring, key=lambda c: (c[1], c[0])))
    inner = {(31, 31), (32, 31), (31, 32), (32, 32)}
    mineable = tuple(sorted(set(ring_t) | inner, key=lambda c: (c[1], c[0])))
    bbox = BBox(min_x=30, min_y=30, max_x=33, max_y=33)
    ordered = pass1o.pass1_mineable_outer_first_order(frozenset(mineable), bbox)
    assert (31, 31) in ordered


def test_pass1_consider_extract_never_targets_off_mineable_grid() -> None:
    mineable = ((50, 50), (51, 50))
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        full_barrier_cells=mineable,
        asteroid_bbox=BBox(min_x=50, min_y=50, max_x=51, max_y=50),
    )
    ctx = SolverRunContext(run_id="p1_edge", reconstruction=recon)
    events: list[dict[object, object]] = []
    run_pass1_outer_placement(ctx, recon, replay_events=events, replay_event_cap=200)
    for e in events:
        if e.get("kind") == "consider_extract":
            assert tuple(e["extractor_cell"]) in {(50, 50), (51, 50)}
