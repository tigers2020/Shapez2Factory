"""Minimum-cost egress corridor opening (Pass1 post-gate, STEP4 recovery MVP)."""

from __future__ import annotations

from dataclasses import replace

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BBox,
    BlueprintCell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.corridor import (
    CorridorOpeningPlan,
    CorridorOpeningResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    Pass1Result,
    PlacementBundle,
    ReconstructionDTO,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    CommitReason,
    PlacementCommitState,
    RecoveryTrigger,
    RejectedReason,
    TransportKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.routing import (
    RoutePath,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.routing.corridor_probe import (
    MIN_PASS2_GATEWAYS,
    interior_anchor_cells_top_k,
    lexicographic_dijkstra_min_path,
    probe_pass2_corridor_availability,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.trace_events import (
    TraceEvent,
)

from . import pass2_route_probe as _pass2_route_probe
from .bundle_candidate import (
    blocked_by_building,
    infer_transport_kind,
)
from .pass1_outer import (
    _cheap_escape_resolve_bbox_and_margin,
    _outside_margin,
)
from .placement_fsm import (
    assert_placement_commit_transition,
)

MAX_PASS1_CORRIDOR_OPENINGS = 2
MAX_STEP4_CORRIDOR_OPENING_ATTEMPTS = 2

_LEX_INF = (999_999,) * 9


def _pass1_cell_sort_key(c: BlueprintCell) -> tuple[int, int]:
    return (c[1], c[0])


def _add_lex(a: tuple[int, ...], b: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(x + y for x, y in zip(a, b, strict=True))


def pass1_fixed_cells_for_probe(pass1: Pass1Result) -> frozenset[BlueprintCell]:
    """Pass1 equipment ∪ output stubs (same contract as Pass2 route probe)."""

    fixed = frozenset(pass1.placement_occupied_cells) | frozenset(pass1.output_stub_cells)
    if not fixed and pass1.occupied_cells:
        fixed = frozenset(pass1.occupied_cells)
    return fixed


def assemble_pass1_from_bundles(bundles: tuple[PlacementBundle, ...]) -> Pass1Result:
    """Rebuild ``Pass1Result`` after subsetting bundles (commit rows provisional only)."""

    placement_occ: set[BlueprintCell] = set()
    stub_cells: set[BlueprintCell] = set()
    commits: list[tuple[str, PlacementCommitState]] = []
    for b in bundles:
        placement_occ.add(b.extractor.cell)
        stub_cells.add(b.output_stub.cell)
        for ext in b.extensions:
            placement_occ.add(ext.cell)
        commits.append((str(b.extractor.placement_id), PlacementCommitState.PROVISIONAL_PLACED))
        for ext in b.extensions:
            commits.append((str(ext.placement_id), PlacementCommitState.PROVISIONAL_PLACED))
    union_occ = placement_occ | stub_cells
    placement_sorted = tuple(sorted(placement_occ, key=_pass1_cell_sort_key))
    stub_sorted = tuple(sorted(stub_cells, key=_pass1_cell_sort_key))
    occupied = tuple(sorted(union_occ, key=_pass1_cell_sort_key))
    return Pass1Result(
        placements=bundles,
        placement_occupied_cells=placement_sorted,
        output_stub_cells=stub_sorted,
        occupied_cells=occupied,
        placement_commit_entries=tuple(commits),
        beam_trace=None,
    )


def _bbox_fallback(cells: frozenset[BlueprintCell]) -> BBox | None:
    if not cells:
        return None
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    return BBox(min_x=min(xs), min_y=min(ys), max_x=max(xs), max_y=max(ys))


def _build_pass1_cell_maps(
    pass1: Pass1Result,
) -> tuple[dict[BlueprintCell, PlacementBundle], dict[BlueprintCell, str]]:
    cell_bundle: dict[BlueprintCell, PlacementBundle] = {}
    role: dict[BlueprintCell, str] = {}
    for b in pass1.placements:
        cell_bundle[b.extractor.cell] = b
        role[b.extractor.cell] = "extractor"
        cell_bundle[b.output_stub.cell] = b
        role[b.output_stub.cell] = "stub"
        for ext in b.extensions:
            cell_bundle[ext.cell] = b
            role[ext.cell] = "extension"
    return cell_bundle, role


def _confirmed_footprint_cells(
    ctx: SolverRunContext, pass1: Pass1Result
) -> frozenset[BlueprintCell]:
    out: set[BlueprintCell] = set()
    for b in pass1.placements:
        pid = str(b.extractor.placement_id)
        if ctx.placement_commit_by_id.get(pid) is PlacementCommitState.ROUTED_CONFIRMED:
            out.add(b.extractor.cell)
            out.add(b.output_stub.cell)
            out.update(e.cell for e in b.extensions)
    return frozenset(out)


def _lex_step_for_cell(
    c: BlueprintCell,
    *,
    transport_kind: TransportKind,
    reconstruction: ReconstructionDTO,
    cell_bundle: dict[BlueprintCell, PlacementBundle],
    role: dict[BlueprintCell, str],
    confirmed_cells: frozenset[BlueprintCell],
    hard_protected: frozenset[BlueprintCell],
    routed_geometry: frozenset[BlueprintCell],
    mineable_and_barrier: frozenset[BlueprintCell],
) -> tuple[int, ...]:
    """9-tuple increment entering ``c``: ex, ext, stub, lost, demo, rtrans, path, row, col."""

    y, x = c[1], c[0]
    tail = (1, y, x)
    if c not in mineable_and_barrier:
        return (0, 0, 0, 1, 0, 0, *tail)
    if c in hard_protected or c in routed_geometry:
        return _LEX_INF
    if c in confirmed_cells:
        return _LEX_INF
    if blocked_by_building(c, transport_kind, reconstruction):
        return _LEX_INF
    if c in cell_bundle:
        r = role[c]
        if r == "extractor":
            return (1, 0, 0, 50, 1, 0, *tail)
        if r == "extension":
            return (0, 1, 0, 0, 0, 0, *tail)
        if r == "stub":
            return (0, 0, 1, 200, 0, 0, *tail)
    if transport_kind is TransportKind.SHAPE_BELT and c in frozenset(reconstruction.belt_cells):
        return (0, 0, 0, 0, 0, 1, *tail)
    if transport_kind is TransportKind.FLUID_PIPE and c in frozenset(reconstruction.pipe_cells):
        return (0, 0, 0, 0, 0, 1, *tail)
    return (0, 0, 0, 0, 0, 0, *tail)


def build_min_cost_egress_opening_plan(
    *,
    ctx: SolverRunContext,
    pass1: Pass1Result,
    reconstruction: ReconstructionDTO,
    pass1_fixed_cells: frozenset[BlueprintCell],
    start_cell: BlueprintCell,
    transport_kind: TransportKind,
    phase: str,
    respect_final_route_cells: bool = True,
) -> CorridorOpeningPlan | None:
    """Single lexicographic shortest path from ``start_cell`` to exterior / trunk goals."""

    _ = phase, pass1_fixed_cells

    resolved = _cheap_escape_resolve_bbox_and_margin(reconstruction)
    if resolved is None:
        return None
    bbox, margin = resolved

    trunk_goals = _pass2_route_probe._trunk_goal_cells(ctx, transport_kind, reconstruction)

    def goal_predicate(c: BlueprintCell) -> bool:
        return _outside_margin(c, bbox, margin) or c in trunk_goals

    hard_protected = frozenset(ctx.routing_state.hard_protected_corridors)
    routed_geometry = (
        frozenset(ctx.routing_state.final_route_cells) if respect_final_route_cells else frozenset()
    )
    confirmed_cells = _confirmed_footprint_cells(ctx, pass1)
    cell_bundle, role = _build_pass1_cell_maps(pass1)

    mineable_and_barrier = frozenset(reconstruction.mineable_placement_cells) | frozenset(
        reconstruction.full_barrier_cells
    )

    cell_step_cost: dict[BlueprintCell, tuple[int, ...]] = {}
    default_step = (0, 0, 0, 0, 0, 0, 1, 0, 0)

    xmin = bbox.min_x - margin - 6
    xmax = bbox.max_x + margin + 6
    ymin = bbox.min_y - margin - 6
    ymax = bbox.max_y + margin + 6
    for x in range(xmin, xmax + 1):
        for y in range(ymin, ymax + 1):
            c = (x, y)
            cell_step_cost[c] = _lex_step_for_cell(
                c,
                transport_kind=transport_kind,
                reconstruction=reconstruction,
                cell_bundle=cell_bundle,
                role=role,
                confirmed_cells=confirmed_cells,
                hard_protected=hard_protected,
                routed_geometry=routed_geometry,
                mineable_and_barrier=mineable_and_barrier,
            )

    chain = lexicographic_dijkstra_min_path(
        start=start_cell,
        goal_predicate=goal_predicate,
        transport_kind=transport_kind,
        reconstruction=reconstruction,
        bbox=bbox,
        margin=margin,
        cell_step_cost=cell_step_cost,
        default_step=default_step,
    )
    if chain is None or len(chain) < 2:
        return None

    cells_to_clear: set[BlueprintCell] = set()
    bundles: set[PlacementBundle] = set()
    for c in chain:
        b = cell_bundle.get(c)
        if b is not None:
            cells_to_clear.add(c)
            bundles.add(b)

    if not bundles:
        return None

    pids: set[str] = set()
    lost_slots = 0
    for b in bundles:
        pids.add(str(b.extractor.placement_id))
        for ext in b.extensions:
            pids.add(str(ext.placement_id))
        lost_slots += 1

    est: tuple[int, ...] = (0, 0, 0, 0, 0, 0, 0, 0, 0)
    for c in chain:
        est = _add_lex(est, cell_step_cost.get(c, default_step))

    anchor = chain[0]
    goal = chain[-1]
    return CorridorOpeningPlan(
        path=RoutePath(transport_kind=transport_kind, cells=tuple(chain)),
        cells_to_clear=frozenset(cells_to_clear),
        placement_ids_to_rollback=frozenset(pids),
        estimated_lost_slots=lost_slots,
        estimated_cost=est,
        target_anchor=anchor,
        exterior_goal=goal,
    )


def apply_corridor_opening_plan(
    *,
    ctx: SolverRunContext,
    pass1: Pass1Result,
    plan: CorridorOpeningPlan,
    phase: str,
    recovery_trigger: RecoveryTrigger | None,
) -> tuple[Pass1Result, SolverRunContext, CorridorOpeningResult]:
    """Rollback touched bundles, shrink ``Pass1Result``, update ``ctx`` placement + stub map."""

    touched_eids: set[str] = set()
    for b in pass1.placements:
        bids = {str(b.extractor.placement_id), *(str(e.placement_id) for e in b.extensions)}
        if bids & plan.placement_ids_to_rollback:
            touched_eids.add(str(b.extractor.placement_id))

    kept = tuple(b for b in pass1.placements if str(b.extractor.placement_id) not in touched_eids)
    new_pass1 = assemble_pass1_from_bundles(kept)

    merged = dict(ctx.placement_commit_by_id)
    for b in pass1.placements:
        if str(b.extractor.placement_id) not in touched_eids:
            continue
        for pid in (
            str(b.extractor.placement_id),
            *(str(e.placement_id) for e in b.extensions),
        ):
            old = merged.get(pid, PlacementCommitState.PROVISIONAL_PLACED)
            if old is PlacementCommitState.ROLLED_BACK:
                continue
            assert_placement_commit_transition(old, PlacementCommitState.ROLLED_BACK)
            merged[pid] = PlacementCommitState.ROLLED_BACK

    rs = ctx.routing_state
    new_fixed = {
        k: v for k, v in rs.fixed_output_stub_by_extractor.items() if k not in touched_eids
    }
    new_rs = replace(rs, fixed_output_stub_by_extractor=new_fixed)
    if recovery_trigger is None:
        new_rs = replace(new_rs, final_route_cells=())
    new_ctx = replace(
        ctx,
        placement_commit_by_id=merged,
        routing_state=new_rs,
    )

    ev = TraceEvent(
        run_id=ctx.run_id,
        phase=phase,
        step_index=0,
        event_type="corridor_opening_recovery",
        committed=True,
        commit_reason=CommitReason.DEGRADED_CONNECTED_RECOVERY,
        rejected_reason=None,
        rollback_reason=None,
        recovery_trigger=recovery_trigger,
        route_level=False,
        transport_kind=plan.path.transport_kind,
    )
    trace_payload = CorridorOpeningResult(
        committed=True,
        plan=plan,
        rollback_reason=None,
        rejected_reason=None,
        trace_rows=(ev,),
    )
    return new_pass1, new_ctx, trace_payload


def maybe_open_corridors_before_pass2(
    *,
    ctx: SolverRunContext,
    pass1: Pass1Result,
) -> tuple[Pass1Result, SolverRunContext, tuple[dict[str, object], ...]]:
    """If gateway probe fails, apply up to ``MAX_PASS1_CORRIDOR_OPENINGS`` opening plans."""

    recon = ctx.reconstruction
    mineable = frozenset(recon.mineable_placement_cells)
    tk = infer_transport_kind(recon)
    trace_rows: list[dict[str, object]] = []
    p1 = pass1
    cctx = ctx
    openings = 0

    while openings < MAX_PASS1_CORRIDOR_OPENINGS:
        fixed = pass1_fixed_cells_for_probe(p1)
        probe = probe_pass2_corridor_availability(
            mineable_cells=mineable,
            pass1_fixed_cells=fixed,
            hard_barrier_cells=frozenset(recon.full_barrier_cells),
            transport_kind=tk,
            reconstruction=recon,
            ctx=cctx,
        )
        if probe.gateway_count >= MIN_PASS2_GATEWAYS:
            break
        bbox_eff = recon.asteroid_bbox or _bbox_fallback(mineable)
        if bbox_eff is None:
            break
        anchors = interior_anchor_cells_top_k(mineable, fixed, bbox_eff)
        pool = tuple(sorted(mineable - fixed))
        candidates: list[BlueprintCell] = list(anchors)
        for c in pool:
            if c not in candidates:
                candidates.append(c)
        for c in sorted(fixed):
            if c not in candidates and len(candidates) < 40:
                candidates.append(c)
        plan = None
        for start_cell in candidates:
            plan = build_min_cost_egress_opening_plan(
                ctx=cctx,
                pass1=p1,
                reconstruction=recon,
                pass1_fixed_cells=fixed,
                start_cell=start_cell,
                transport_kind=tk,
                phase="pass1_post_gate",
                respect_final_route_cells=False,
            )
            if plan is not None:
                break
        if plan is None:
            break
        p1, cctx, _res = apply_corridor_opening_plan(
            ctx=cctx,
            pass1=p1,
            plan=plan,
            phase="pass1_post_gate",
            recovery_trigger=None,
        )
        probe_after = probe_pass2_corridor_availability(
            mineable_cells=mineable,
            pass1_fixed_cells=pass1_fixed_cells_for_probe(p1),
            hard_barrier_cells=frozenset(recon.full_barrier_cells),
            transport_kind=tk,
            reconstruction=recon,
            ctx=cctx,
        )
        trace_rows.append(
            {
                "event_type": "corridor_opening_recovery",
                "phase": "pass1_post_gate",
                "recovery_trigger": None,
                "decision": {"committed": True, "commit_reason": "degraded_connected_recovery"},
                "metrics": {
                    "gateway_count_before": probe.gateway_count,
                    "gateway_count_after": probe_after.gateway_count,
                    "placements_removed_count": len(plan.placement_ids_to_rollback),
                    "extractor_removed_count": plan.estimated_lost_slots,
                    "extension_removed_count": 0,
                    "lost_slot_count": plan.estimated_lost_slots,
                    "path_length": len(plan.path.cells),
                },
                "search": {
                    "search_mode": "lexicographic_dijkstra",
                    "expanded_nodes": 0,
                    "search_time_ms": 0,
                    "optimality_guarantee": True,
                },
            }
        )
        openings += 1

    return p1, cctx, tuple(trace_rows)


def step4_corridor_opening_recovery(
    *,
    ctx: SolverRunContext,
    pass1: Pass1Result,
    failed_stub_cell: BlueprintCell,
    attempt_index: int,
) -> tuple[Pass1Result, SolverRunContext, CorridorOpeningResult | None]:
    """Bounded recovery entry for STEP4 routing failure (stub anchor)."""

    if attempt_index >= MAX_STEP4_CORRIDOR_OPENING_ATTEMPTS:
        return pass1, ctx, None
    recon = ctx.reconstruction
    tk = infer_transport_kind(recon)
    pass1_fixed = pass1_fixed_cells_for_probe(pass1)
    plan = build_min_cost_egress_opening_plan(
        ctx=ctx,
        pass1=pass1,
        reconstruction=recon,
        pass1_fixed_cells=pass1_fixed,
        start_cell=failed_stub_cell,
        transport_kind=tk,
        phase="step4_recovery",
        respect_final_route_cells=True,
    )
    if plan is None:
        ev = TraceEvent(
            run_id=ctx.run_id,
            phase="step4_recovery",
            step_index=attempt_index,
            event_type="corridor_opening_recovery",
            committed=False,
            commit_reason=None,
            rejected_reason=RejectedReason.REJECTED_BY_CONNECTIVITY,
            rollback_reason=None,
            recovery_trigger=RecoveryTrigger.STEP4_ROUTING_FAILURE,
            route_level=False,
            transport_kind=tk,
        )
        return (
            pass1,
            ctx,
            CorridorOpeningResult(
                committed=False,
                plan=None,
                rollback_reason=None,
                rejected_reason=RejectedReason.REJECTED_BY_CONNECTIVITY,
                trace_rows=(ev,),
            ),
        )

    return apply_corridor_opening_plan(
        ctx=ctx,
        pass1=pass1,
        plan=plan,
        phase="step4_recovery",
        recovery_trigger=RecoveryTrigger.STEP4_ROUTING_FAILURE,
    )


__all__ = [
    "MAX_PASS1_CORRIDOR_OPENINGS",
    "MAX_STEP4_CORRIDOR_OPENING_ATTEMPTS",
    "apply_corridor_opening_plan",
    "assemble_pass1_from_bundles",
    "build_min_cost_egress_opening_plan",
    "maybe_open_corridors_before_pass2",
    "pass1_fixed_cells_for_probe",
    "step4_corridor_opening_recovery",
]
