from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import BBox
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.corridor import (
    CorridorOpeningPlan,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ExtensionPlacement,
    ExtractorPlacement,
    OutputStub,
    Pass1Result,
    PlacementBundle,
    PlacementId,
    ReconstructionDTO,
    RoutePath,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    PlacementCommitState,
    TransportKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement import (
    corridor_opening,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.routing import (
    step4_corridor_recovery,
)


def _belt_recon_5x5() -> ReconstructionDTO:
    mineable = frozenset((x, y) for x in range(1, 6) for y in range(1, 6))
    m = tuple(sorted(mineable))
    return ReconstructionDTO(
        mineable_placement_cells=m,
        full_barrier_cells=m,
        belt_cells=m,
        pipe_cells=(),
        asteroid_bbox=BBox(1, 1, 5, 5),
        external_margin=2,
    )


def _bundle(
    *,
    eid: str,
    extractor: tuple[int, int],
    stub: tuple[int, int],
    extensions: tuple[tuple[tuple[int, int], tuple[int, int], tuple[int, int]], ...] = (),
) -> PlacementBundle:
    pid = PlacementId(eid)
    exts = tuple(
        ExtensionPlacement(
            placement_id=PlacementId(f"{eid}:x:{i}"),
            anchor_extractor_id=pid,
            cell=ec,
            parent_cell=pc,
            orientation_toward_parent=orient,
        )
        for i, (ec, pc, orient) in enumerate(extensions)
    )
    return PlacementBundle(
        extractor=ExtractorPlacement(
            placement_id=pid,
            cell=extractor,
            transport_kind=TransportKind.SHAPE_BELT,
        ),
        extensions=exts,
        output_stub=OutputStub(
            extractor_placement_id=pid,
            cell=stub,
            transport_kind=TransportKind.SHAPE_BELT,
        ),
    )


def test_apply_corridor_opening_marks_rolled_back() -> None:
    recon = _belt_recon_5x5()
    b0 = _bundle(eid="run:p1:e:0:2:3", extractor=(2, 3), stub=(2, 2))
    b1 = _bundle(eid="run:p1:e:1:3:3", extractor=(3, 3), stub=(3, 2))
    p1 = corridor_opening.assemble_pass1_from_bundles((b0, b1))
    ctx = SolverRunContext(
        run_id="run",
        reconstruction=recon,
        placement_commit_by_id={
            str(b0.extractor.placement_id): PlacementCommitState.PROVISIONAL_PLACED,
            str(b1.extractor.placement_id): PlacementCommitState.PROVISIONAL_PLACED,
        },
    )
    plan = CorridorOpeningPlan(
        path=RoutePath(transport_kind=TransportKind.SHAPE_BELT, cells=((2, 3), (3, 3))),
        cells_to_clear={(2, 3), (3, 3)},
        placement_ids_to_rollback={str(b0.extractor.placement_id)},
        estimated_lost_slots=1,
        estimated_cost=(0,) * 9,
        target_anchor=(2, 3),
        exterior_goal=(5, 5),
    )
    p1n, ctxn, res = corridor_opening.apply_corridor_opening_plan(
        ctx=ctx,
        pass1=p1,
        plan=plan,
        phase="pass1_post_gate",
        recovery_trigger=None,
    )
    assert res.committed is True
    assert str(b0.extractor.placement_id) not in {
        str(b.extractor.placement_id) for b in p1n.placements
    }
    assert (
        ctxn.placement_commit_by_id[str(b0.extractor.placement_id)]
        is PlacementCommitState.ROLLED_BACK
    )


def test_build_min_cost_plan_deterministic() -> None:
    recon = _belt_recon_5x5()
    cheap = _bundle(
        eid="run:p1:e:0:2:4",
        extractor=(2, 4),
        stub=(2, 5),
        extensions=(((2, 3), (2, 4), (0, -1)),),
    )
    expensive = _bundle(eid="run:p1:e:1:4:4", extractor=(4, 4), stub=(5, 4))
    p1 = corridor_opening.assemble_pass1_from_bundles((cheap, expensive))
    ctx = SolverRunContext(run_id="run", reconstruction=recon)
    fixed = corridor_opening.pass1_fixed_cells_for_probe(p1)
    a = corridor_opening.build_min_cost_egress_opening_plan(
        ctx=ctx,
        pass1=p1,
        reconstruction=recon,
        pass1_fixed_cells=fixed,
        start_cell=(2, 4),
        transport_kind=TransportKind.SHAPE_BELT,
        phase="pass1_post_gate",
    )
    b = corridor_opening.build_min_cost_egress_opening_plan(
        ctx=ctx,
        pass1=p1,
        reconstruction=recon,
        pass1_fixed_cells=fixed,
        start_cell=(2, 4),
        transport_kind=TransportKind.SHAPE_BELT,
        phase="pass1_post_gate",
    )
    assert a is not None and b is not None
    assert a.path.cells == b.path.cells
    assert a.placement_ids_to_rollback == b.placement_ids_to_rollback


def test_step4_recovery_trace_committed_false_when_no_plan() -> None:
    recon = _belt_recon_5x5()
    p1 = Pass1Result()
    ctx = SolverRunContext(run_id="s4", reconstruction=recon)
    _p1, _ctx, res = step4_corridor_recovery.step4_corridor_opening_recovery(
        ctx=ctx,
        pass1=p1,
        failed_stub_cell=(2, 2),
        attempt_index=0,
    )
    assert res is not None
    assert res.committed is False
    assert res.trace_rows[0].recovery_trigger is not None
    assert res.trace_rows[0].committed is False
