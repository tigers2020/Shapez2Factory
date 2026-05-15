"""
Pass2 internal fill placement (STEP 3, §8).

Blocked set = Pass1 fixed geometry + preserved blueprint barriers. Stub→exterior/trunk
BFS (``pass2_route_probe``) is admission + packing-shadow only (§8). STEP 4 route
geometry on ``SolverRunContext`` is not read or written here.
"""

from __future__ import annotations

import math

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BBox,
    BlueprintCell,
    is_physical_x,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ExtensionPlacement,
    ExtractorPlacement,
    OutputStub,
    Pass1Result,
    Pass2Result,
    PlacementBundle,
    PlacementId,
    ReconstructionDTO,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    CommitReason,
    PlacementCommitState,
    TransportKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.trace_collector import (
    TraceCollector,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.trace_events import (
    TraceEvent,
)

from .bundle_candidate import (
    CARDINAL_DIRS,
    Pass2BundleCandidate,
    blocked_by_building,
    grow_pass2_branching_extension_cells,
    infer_transport_kind,
    step_cell,
)
from .corridor_opening import maybe_open_corridors_before_pass2
from .pass2_bundle_optimizer import (
    Pass2PackingInput,
    optimize_pass2_bundle_packing,
)
from .pass2_route_probe import Pass2RouteProbe, probe_pass2_stub_route

_PASS2_TRACE_PHASE = "pass2_internal"


def _pass2_emit_trace_event(
    trace: TraceCollector,
    step_box: list[int],
    *,
    run_id: str,
    event_type: str,
    committed: bool,
    commit_reason: CommitReason | None,
) -> None:
    """Runtime trace parallel to ``beam_trace``; semantics via ``TraceEvent`` only."""

    step = step_box[0]
    step_box[0] = step + 1
    trace.emit(
        TraceEvent(
            run_id=run_id,
            phase=_PASS2_TRACE_PHASE,
            step_index=step,
            event_type=event_type,
            committed=committed,
            commit_reason=commit_reason if committed else None,
            rejected_reason=None,
            rollback_reason=None,
            recovery_trigger=None,
            computation_cycle=None,
            route_level=False,
            transport_kind=None,
        )
    )


def _pass2_emit_observation(
    trace: TraceCollector,
    step_box: list[int],
    *,
    run_id: str,
    event_type: str,
) -> None:
    _pass2_emit_trace_event(
        trace,
        step_box,
        run_id=run_id,
        event_type=event_type,
        committed=False,
        commit_reason=None,
    )


def _pass2_emit_committed(
    trace: TraceCollector,
    step_box: list[int],
    *,
    run_id: str,
    event_type: str,
) -> None:
    _pass2_emit_trace_event(
        trace,
        step_box,
        run_id=run_id,
        event_type=event_type,
        committed=True,
        commit_reason=CommitReason.NORMAL_GAIN,
    )


def _pass2_emit_rejected(
    trace: TraceCollector,
    step_box: list[int],
    *,
    run_id: str,
    event_type: str,
) -> None:
    _pass2_emit_trace_event(
        trace,
        step_box,
        run_id=run_id,
        event_type=event_type,
        committed=False,
        commit_reason=None,
    )


def _bbox_fallback(cells: frozenset[BlueprintCell]) -> BBox | None:
    if not cells:
        return None
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    return BBox(min_x=min(xs), min_y=min(ys), max_x=max(xs), max_y=max(ys))


def build_pass2_blocked_set(
    pass1: Pass1Result,
    reconstruction: ReconstructionDTO,
) -> frozenset[BlueprintCell]:
    """§8.2: Pass1 equipment + reserved output stubs + hard barriers / preserved blueprint."""

    fixed = frozenset(pass1.placement_occupied_cells) | frozenset(pass1.output_stub_cells)
    if not fixed and pass1.occupied_cells:
        fixed = frozenset(pass1.occupied_cells)
    barrier = frozenset(reconstruction.full_barrier_cells)
    return fixed | barrier


def _pass1_fixed_cells_for_probe(pass1: Pass1Result) -> frozenset[BlueprintCell]:
    """Pass1 equipment ∪ output stubs (BFS hard occupancy; not full ``full_barrier``)."""

    fixed = frozenset(pass1.placement_occupied_cells) | frozenset(pass1.output_stub_cells)
    if not fixed and pass1.occupied_cells:
        fixed = frozenset(pass1.occupied_cells)
    return fixed


def _sort_mineable_interior_first(
    cells: frozenset[BlueprintCell],
    bbox: BBox,
) -> tuple[BlueprintCell, ...]:
    """Inner cells first (max edge distance), then same angular sweep as Pass1 (§7.2)."""

    cx = (bbox.min_x + bbox.max_x) / 2.0
    cy = (bbox.min_y + bbox.max_y) / 2.0

    def edge_distance(c: BlueprintCell) -> int:
        x, y = c
        return min(x - bbox.min_x, bbox.max_x - x, y - bbox.min_y, bbox.max_y - y)

    def sort_key(c: BlueprintCell) -> tuple[int, float, int, int]:
        x, y = c
        dx, dy = x - cx, y - cy
        ang = math.atan2(dx, -dy)
        if ang < 0.0:
            ang += 2.0 * math.pi
        return (-edge_distance(c), ang, y, x)

    return tuple(sorted(cells, key=sort_key))


def _build_pass2_candidate(
    *,
    run_id: str,
    scan_index: int,
    extractor: BlueprintCell,
    out_dir: tuple[int, int],
    mineable: frozenset[BlueprintCell],
    used: set[BlueprintCell],
    transport_kind: TransportKind,
    reconstruction: ReconstructionDTO,
    bbox: BBox,
) -> Pass2BundleCandidate | None:
    stub = step_cell(extractor, out_dir)
    if not is_physical_x(stub[0]):
        return Pass2BundleCandidate(
            candidate_id=f"{run_id}:p2:cand:{scan_index}:{extractor}:{out_dir}",
            scan_index=scan_index,
            extractor_cell=extractor,
            output_direction=out_dir,
            output_stub_cell=stub,
            extension_cells=(),
            transport_kind=transport_kind,
            score=-1.0,
            reject_reason="stub_non_physical_coordinate",
        )
    if stub in used:
        return None
    if blocked_by_building(stub, transport_kind, reconstruction):
        return Pass2BundleCandidate(
            candidate_id=f"{run_id}:p2:cand:{scan_index}:{extractor}:{out_dir}",
            scan_index=scan_index,
            extractor_cell=extractor,
            output_direction=out_dir,
            output_stub_cell=stub,
            extension_cells=(),
            transport_kind=transport_kind,
            score=-1.0,
            reject_reason="stub_blocked",
        )

    trial_used = set(used)
    trial_used.add(extractor)
    trial_used.add(stub)
    exts = grow_pass2_branching_extension_cells(
        extractor,
        out_dir,
        stub,
        mineable,
        trial_used,
        transport_kind,
        reconstruction,
    )

    edge = min(
        extractor[0] - bbox.min_x,
        bbox.max_x - extractor[0],
        extractor[1] - bbox.min_y,
        bbox.max_y - extractor[1],
    )
    n_ext = len(exts)
    score = float(n_ext) * 1000.0 + float(edge) * 5.0

    return Pass2BundleCandidate(
        candidate_id=f"{run_id}:p2:cand:{scan_index}:{extractor}:{out_dir}",
        scan_index=scan_index,
        extractor_cell=extractor,
        output_direction=out_dir,
        output_stub_cell=stub,
        extension_cells=exts,
        transport_kind=transport_kind,
        score=score,
        reject_reason=None,
    )


def _pass2_prepare_state(
    ctx: SolverRunContext,
    pass1: Pass1Result,
) -> (
    tuple[
        ReconstructionDTO,
        frozenset[BlueprintCell],
        BBox,
        set[BlueprintCell],
        tuple[BlueprintCell, ...],
        TransportKind,
    ]
    | None
):
    reconstruction = ctx.reconstruction
    mineable_cells = frozenset(reconstruction.mineable_placement_cells)
    if not mineable_cells:
        return None
    bbox = reconstruction.asteroid_bbox or _bbox_fallback(mineable_cells)
    if bbox is None:
        return None
    blocked = build_pass2_blocked_set(pass1, reconstruction)
    used: set[BlueprintCell] = set(blocked)
    remaining = frozenset(c for c in mineable_cells if c not in blocked)
    if not remaining:
        return None
    transport_kind = infer_transport_kind(reconstruction)
    ordered = _sort_mineable_interior_first(remaining, bbox)
    return (reconstruction, mineable_cells, bbox, used, ordered, transport_kind)


def _pass2_gather_feasible_for_extractor(
    *,
    run_id: str,
    scan_index: int,
    extractor: BlueprintCell,
    mineable_cells: frozenset[BlueprintCell],
    used: set[BlueprintCell],
    transport_kind: TransportKind,
    reconstruction: ReconstructionDTO,
    bbox: BBox,
    trace: TraceCollector,
    trace_step_box: list[int],
) -> tuple[list[Pass2BundleCandidate], list[dict[str, object]]]:
    feasible: list[Pass2BundleCandidate] = []
    beam_rejects: list[dict[str, object]] = []
    for out_dir in CARDINAL_DIRS:
        cand = _build_pass2_candidate(
            run_id=run_id,
            scan_index=scan_index,
            extractor=extractor,
            out_dir=out_dir,
            mineable=mineable_cells,
            used=used,
            transport_kind=transport_kind,
            reconstruction=reconstruction,
            bbox=bbox,
        )
        if cand is None:
            continue
        if cand.reject_reason is not None:
            beam_rejects.append(
                {
                    "placement_pass": "pass2",
                    "extractor_cell": extractor,
                    "output_direction": out_dir,
                    "score": cand.score,
                    "committed": False,
                    "reject_reason": cand.reject_reason,
                }
            )
            _pass2_emit_rejected(
                trace,
                trace_step_box,
                run_id=run_id,
                event_type="pass2_candidate_rejected",
            )
            continue
        feasible.append(cand)
    return feasible, beam_rejects


def _pass2_collect_candidate_pool(
    *,
    run_id: str,
    ordered: tuple[BlueprintCell, ...],
    mineable_cells: frozenset[BlueprintCell],
    baseline_used: set[BlueprintCell],
    transport_kind: TransportKind,
    reconstruction: ReconstructionDTO,
    bbox: BBox,
    trace: TraceCollector,
    trace_step_box: list[int],
) -> tuple[tuple[Pass2BundleCandidate, ...], list[dict[str, object]]]:
    """Feasible ``out_dir`` candidates per extractor; baseline ``used`` only."""

    pool: list[Pass2BundleCandidate] = []
    beam_rejects: list[dict[str, object]] = []
    for scan_index, extractor in enumerate(ordered):
        if extractor in baseline_used:
            continue
        feasible, rejects = _pass2_gather_feasible_for_extractor(
            run_id=run_id,
            scan_index=scan_index,
            extractor=extractor,
            mineable_cells=mineable_cells,
            used=baseline_used,
            transport_kind=transport_kind,
            reconstruction=reconstruction,
            bbox=bbox,
            trace=trace,
            trace_step_box=trace_step_box,
        )
        beam_rejects.extend(rejects)
        pool.extend(feasible)
    return tuple(pool), beam_rejects


def _pass2_assemble_result(
    bundles: list[PlacementBundle],
    commits: list[tuple[str, PlacementCommitState]],
    beam: list[dict[str, object]],
    *,
    corridor_opening_trace: tuple[dict[str, object], ...] = (),
    pass1_after_corridor_gate: Pass1Result | None = None,
    solver_ctx_after_corridor_gate: SolverRunContext | None = None,
) -> Pass2Result:
    pass2_occ: set[BlueprintCell] = set()
    for b in bundles:
        pass2_occ.add(b.extractor.cell)
        pass2_occ.add(b.output_stub.cell)
        for ext in b.extensions:
            pass2_occ.add(ext.cell)
    blocked_delta = tuple(sorted(pass2_occ, key=lambda c: (c[1], c[0])))
    return Pass2Result(
        provisional_placements=tuple(bundles),
        blocked_cells_delta=blocked_delta,
        placement_commit_entries=tuple(commits),
        beam_trace=tuple(beam) if beam else None,
        corridor_opening_trace=corridor_opening_trace,
        pass1_after_corridor_gate=pass1_after_corridor_gate,
        solver_ctx_after_corridor_gate=solver_ctx_after_corridor_gate,
    )


def _pass2_candidate_to_bundle(
    cand: Pass2BundleCandidate,
    *,
    run_id: str,
    bundle_index: int,
) -> PlacementBundle:
    eid = PlacementId(
        f"{run_id}:p2:e:{bundle_index}:" + f"{cand.extractor_cell[0]}:{cand.extractor_cell[1]}"
    )
    exts = tuple(
        ExtensionPlacement(
            placement_id=PlacementId(f"{run_id}:p2:x:{bundle_index}:{i}:{ec[0]}:{ec[1]}"),
            anchor_extractor_id=eid,
            cell=ec,
            parent_cell=pc,
            orientation_toward_parent=orient,
        )
        for i, (ec, pc, orient) in enumerate(cand.extension_cells)
    )
    ext = ExtractorPlacement(
        placement_id=eid,
        cell=cand.extractor_cell,
        transport_kind=cand.transport_kind,
    )
    stub = OutputStub(
        extractor_placement_id=eid,
        cell=cand.output_stub_cell,
        transport_kind=cand.transport_kind,
    )
    return PlacementBundle(extractor=ext, extensions=exts, output_stub=stub)


def run_pass2_internal_fill(
    ctx: SolverRunContext,
    pass1: Pass1Result,
    *,
    trace: TraceCollector,
) -> Pass2Result:
    """Interior Pass2 (§8): optional Pass1 corridor gate, then pool + packing.

    Corridor gate may return ``pass1_after_corridor_gate`` / ``solver_ctx_after_corridor_gate``
    on ``Pass2Result`` when openings were applied (caller merges ctx for downstream steps).
    """

    p1_work, ctx_work, corridor_trace = maybe_open_corridors_before_pass2(ctx=ctx, pass1=pass1)
    gate_ran = bool(corridor_trace) or (p1_work is not pass1)

    trace_step_box: list[int] = [0]
    prepared = _pass2_prepare_state(ctx_work, p1_work)
    if prepared is None:
        _pass2_emit_observation(
            trace,
            trace_step_box,
            run_id=ctx_work.run_id,
            event_type="pass2_noop",
        )
        return Pass2Result(
            corridor_opening_trace=corridor_trace,
            pass1_after_corridor_gate=p1_work if gate_ran else None,
            solver_ctx_after_corridor_gate=ctx_work if gate_ran else None,
        )
    reconstruction, mineable_cells, bbox, baseline_used, ordered, transport_kind = prepared

    beam: list[dict[str, object]] = list(corridor_trace)

    pool, pool_rejects = _pass2_collect_candidate_pool(
        run_id=ctx_work.run_id,
        ordered=ordered,
        mineable_cells=mineable_cells,
        baseline_used=baseline_used,
        transport_kind=transport_kind,
        reconstruction=reconstruction,
        bbox=bbox,
        trace=trace,
        trace_step_box=trace_step_box,
    )
    beam.extend(pool_rejects)

    p1_fixed = _pass1_fixed_cells_for_probe(p1_work)
    route_probes: dict[str, Pass2RouteProbe] = {}
    filtered_pool: list[Pass2BundleCandidate] = []
    for cand in pool:
        pr = probe_pass2_stub_route(
            cand,
            pass1_fixed_cells=p1_fixed,
            reconstruction=reconstruction,
            ctx=ctx_work,
        )
        route_probes[cand.candidate_id] = pr
        if not pr.reachable:
            beam.append(
                {
                    "placement_pass": "pass2",
                    "extractor_cell": cand.extractor_cell,
                    "output_direction": cand.output_direction,
                    "output_stub_cell": cand.output_stub_cell,
                    "score": cand.score,
                    "committed": False,
                    "reject_reason": "pass2_stub_not_externally_reachable",
                }
            )
            _pass2_emit_rejected(
                trace,
                trace_step_box,
                run_id=ctx_work.run_id,
                event_type="pass2_stub_route_probe_rejected",
            )
            continue
        filtered_pool.append(cand)

    pack_inp = Pass2PackingInput(
        candidates=tuple(filtered_pool),
        blocked_cells=frozenset(baseline_used),
        route_probes=route_probes,
    )
    packing = optimize_pass2_bundle_packing(pack_inp)
    beam.extend(packing.rejected)

    bundles: list[PlacementBundle] = []
    commits: list[tuple[str, PlacementCommitState]] = []

    for rank, cand in enumerate(packing.selected):
        b = _pass2_candidate_to_bundle(cand, run_id=ctx_work.run_id, bundle_index=rank)
        bundles.append(b)
        commits.append((str(b.extractor.placement_id), PlacementCommitState.PROVISIONAL_PLACED))
        for ext in b.extensions:
            commits.append((str(ext.placement_id), PlacementCommitState.PROVISIONAL_PLACED))
        beam.append(
            {
                "placement_pass": "pass2",
                "event_type": "pass2_optimizer_selected",
                "optimizer_selected": True,
                "optimizer_rank": rank,
                "objective_score": int(round(float(cand.score) * 1000.0)),
                "candidate_score": cand.score,
                "scan_index": cand.scan_index,
                "extractor_cell": cand.extractor_cell,
                "output_direction": cand.output_direction,
                "output_stub_cell": cand.output_stub_cell,
                "score": cand.score,
                "committed": True,
                "reject_reason": None,
                "placement_ids": (str(b.extractor.placement_id),)
                + tuple(str(x.placement_id) for x in b.extensions),
            }
        )
        _pass2_emit_committed(
            trace,
            trace_step_box,
            run_id=ctx_work.run_id,
            event_type="pass2_optimizer_selected",
        )

    beam.append(
        {
            "placement_pass": "pass2",
            "event_type": "pass2_optimizer_summary",
            "optimizer": packing.optimizer_name,
            "optimizer_status": packing.optimizer_status,
            "candidate_count": packing.candidate_count,
            "selected_count": packing.selected_count,
            "conflict_constraint_count": packing.conflict_constraint_count,
            "objective_value": packing.objective_value,
            "fallback_used": packing.fallback_used,
            "cp_sat_status": packing.cp_sat_status,
            "time_limit_ms": pack_inp.time_limit_ms,
            "max_candidates": pack_inp.max_candidates,
        }
    )
    _pass2_emit_observation(
        trace,
        trace_step_box,
        run_id=ctx_work.run_id,
        event_type="pass2_optimizer_summary",
    )

    return _pass2_assemble_result(
        bundles,
        commits,
        beam,
        corridor_opening_trace=corridor_trace,
        pass1_after_corridor_gate=p1_work if gate_ran else None,
        solver_ctx_after_corridor_gate=ctx_work if gate_ran else None,
    )


__all__ = ["build_pass2_blocked_set", "run_pass2_internal_fill"]
