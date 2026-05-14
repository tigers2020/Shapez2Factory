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
    barrier = tuple({*mineable, (22, 22)})
    recon = ReconstructionDTO(
        mineable_placement_cells=mineable,
        extraction_shell_cells=mineable,
        full_barrier_cells=barrier,
        asteroid_bbox=BBox(min_x=20, min_y=20, max_x=25, max_y=25),
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
