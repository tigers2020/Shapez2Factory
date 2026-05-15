"""
Pass1 outer-first placement (STEP 2, §7).

Cheap escape is probe-only (§7.3): never written to ``occupied_cells`` or
``routing_state.final_route_cells``. STEP 4 owns real routes and ``ROUTED_CONFIRMED``.

**Deterministic mineable scan (§7.2 item 6)** — equivalent to “12 o'clock clockwise”:

1. **Outer-first**: ascending minimum axis distance from ``(x, y)`` to the mineable
   ``bbox`` edge (L∞-shell index on an axis-aligned bbox).
2. **Clockwise from north around bbox center**: bearing
   ``atan2(dx, -dy)`` in ``[0, 2π)`` where ``(dx, dy)`` is cell minus centroid
   (north = smaller ``y`` → ``dy < 0`` → bearing ``0``).
3. **Tie-break**: ``(y, x)`` lexicographic.

Output-direction evaluation order is fixed ``CARDINAL_DIRS``: N → E → S → W.

Among feasible bundles with the same maximum extension count, prefer the output whose
straight chain runs **into the deposit** along the bbox inward normal of the tightest
face (corners break ties by alignment with the vector toward the bbox center). This
avoids west-rim extractors picking north output solely because N sorts before W.

**Grid**: STEP1 ``mineable_placement_cells`` never uses **X == 0** as an id (decode
convention). Neighbor moves and cheap-escape BFS use ``domain.grid.step_blueprint_cell``
(seam ``-1 ↔ 1``); never ``x + dx`` raw east/west.

**Rim-only extractor core (Pass1)**: the extractor cell must sit on the mineable graph
boundary — ``perimeter_depth == 0`` (4-neighbor ``step_cell`` to a cell not in
``mineable_placement_cells``). Extension chains may still occupy deeper cells; Pass2
owns interior cores.
"""

from __future__ import annotations

import math
from collections import deque
from typing import Any

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
    Pass1BundleCandidate,
    blocked_by_building,
    grow_pass1_straight_extension_chain,
    infer_transport_kind_for_mineable_cell,
    lex_key_pass1_best_output,
    step_cell,
)

_OUTPUT_DIRS = CARDINAL_DIRS

_PASS1_TRACE_PHASE = "pass1_outer"


def compute_mineable_perimeter_depth_by_cell(
    mineable: frozenset[BlueprintCell],
) -> dict[BlueprintCell, int]:
    """BFS depth inside ``mineable`` to the nearest cell with a 4-neighbor outside ``mineable``.

    ``depth == 0`` is a rim cell (touches non-mineable via ``step_cell``). Deterministic:
    multi-source BFS in discovery order from the initial rim queue (mineable iteration order).
    """

    if not mineable:
        return {}
    q: deque[BlueprintCell] = deque()
    depth: dict[BlueprintCell, int] = {}
    rim_ordered: list[BlueprintCell] = []
    for c in sorted(mineable, key=lambda x: (x[1], x[0])):
        for d in CARDINAL_DIRS:
            if step_cell(c, d) not in mineable:
                rim_ordered.append(c)
                break
    for c in rim_ordered:
        if c in depth:
            continue
        depth[c] = 0
        q.append(c)
    while q:
        cur = q.popleft()
        dc = depth[cur]
        for d in CARDINAL_DIRS:
            nxt = step_cell(cur, d)
            if nxt not in mineable or nxt in depth:
                continue
            depth[nxt] = dc + 1
            q.append(nxt)
    return depth


def is_pass1_rim_extractor_cell(
    cell: BlueprintCell, depth_by_cell: dict[BlueprintCell, int]
) -> bool:
    """True iff ``cell`` is mineable-adjacent to a non-mineable 4-neighbor (``depth == 0``)."""

    return depth_by_cell.get(cell) == 0


def _pass1_emit_trace_event(
    trace: TraceCollector,
    step_box: list[int],
    *,
    run_id: str,
    event_type: str,
    committed: bool,
    commit_reason: CommitReason | None,
) -> None:
    """Parallel to replay rows; emits even when replay buffer is ``None`` or capped."""

    step = step_box[0]
    step_box[0] = step + 1
    trace.emit(
        TraceEvent(
            run_id=run_id,
            phase=_PASS1_TRACE_PHASE,
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


def _bbox_fallback(cells: frozenset[BlueprintCell]) -> BBox | None:
    if not cells:
        return None
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    return BBox(min_x=min(xs), min_y=min(ys), max_x=max(xs), max_y=max(ys))


def _inward_chain_direction_from_bbox(extractor: BlueprintCell, bbox: BBox) -> tuple[int, int]:
    """Unit step from extractor toward the nearest bbox face, then into the deposit.

    On a tie (corner), pick the candidate best aligned with the vector toward bbox center.
    """

    x, y = extractor
    dw, de = x - bbox.min_x, bbox.max_x - x
    dn, ds = y - bbox.min_y, bbox.max_y - y
    m = min(dw, de, dn, ds)
    cand: list[tuple[int, int]] = []
    if dw == m:
        cand.append((1, 0))
    if de == m:
        cand.append((-1, 0))
    if dn == m:
        cand.append((0, 1))
    if ds == m:
        cand.append((0, -1))
    if not cand:
        return (0, -1)
    if len(cand) == 1:
        return cand[0]
    cx = (bbox.min_x + bbox.max_x) / 2.0
    cy = (bbox.min_y + bbox.max_y) / 2.0
    vx, vy = cx - float(x), cy - float(y)

    def dot(u: tuple[int, int]) -> float:
        return float(u[0]) * vx + float(u[1]) * vy

    return max(cand, key=dot)


def _preferred_pass1_output_direction(extractor: BlueprintCell, bbox: BBox) -> tuple[int, int]:
    """Output direction (extractor → stub) so straight chain grows along inward scan."""

    ix, iy = _inward_chain_direction_from_bbox(extractor, bbox)
    return (-ix, -iy)


def pass1_mineable_outer_first_order(
    mineable: frozenset[BlueprintCell],
    bbox: BBox,
) -> tuple[BlueprintCell, ...]:
    """Public deterministic Pass1 mineable iteration order (§7.2)."""

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
        return (edge_distance(c), ang, y, x)

    return tuple(sorted(mineable, key=sort_key))


def _outside_margin(c: BlueprintCell, bbox: BBox, margin: int) -> bool:
    x, y = c
    return (
        x < bbox.min_x - margin
        or x > bbox.max_x + margin
        or y < bbox.min_y - margin
        or y > bbox.max_y + margin
    )


def _movable_for_escape_probe(c: BlueprintCell, tk: TransportKind, r: ReconstructionDTO) -> bool:
    return not blocked_by_building(c, tk, r)


def _cheap_escape_resolve_bbox_and_margin(
    reconstruction: ReconstructionDTO,
) -> tuple[BBox, int] | None:
    bbox = reconstruction.asteroid_bbox or _bbox_fallback(
        frozenset(reconstruction.mineable_placement_cells)
    )
    if bbox is None:
        return None
    margin = reconstruction.external_margin or 3
    return (bbox, margin)


def _cheap_escape_bfs_reaches_outside(
    stub: BlueprintCell,
    bbox: BBox,
    margin: int,
    transport_kind: TransportKind,
    reconstruction: ReconstructionDTO,
) -> bool:
    xmin = min(stub[0], bbox.min_x) - margin - 6
    xmax = max(stub[0], bbox.max_x) + margin + 6
    ymin = min(stub[1], bbox.min_y) - margin - 6
    ymax = max(stub[1], bbox.max_y) + margin + 6

    q: deque[BlueprintCell] = deque([stub])
    seen: set[BlueprintCell] = {stub}
    while q:
        cur = q.popleft()
        if _outside_margin(cur, bbox, margin):
            return True
        for d in _OUTPUT_DIRS:
            nxt = step_cell(cur, d)
            if nxt in seen:
                continue
            if nxt[0] < xmin or nxt[0] > xmax or nxt[1] < ymin or nxt[1] > ymax:
                continue
            if not _movable_for_escape_probe(nxt, transport_kind, reconstruction):
                continue
            seen.add(nxt)
            q.append(nxt)
    return False


def cheap_escape_feasible(
    stub: BlueprintCell,
    transport_kind: TransportKind,
    reconstruction: ReconstructionDTO,
) -> bool:
    """4-neighbor BFS from stub; same-kind belt/pipe traversable (§3.1 merge hint)."""

    resolved = _cheap_escape_resolve_bbox_and_margin(reconstruction)
    if resolved is None:
        return False
    bbox, margin = resolved
    return _cheap_escape_bfs_reaches_outside(stub, bbox, margin, transport_kind, reconstruction)


def _replay_append(
    buf: list[dict[str, Any]] | None,
    row: dict[str, Any],
    *,
    cap: int | None,
) -> None:
    if buf is None:
        return
    if cap is not None and len(buf) >= cap:
        return
    buf.append(row)


def _build_candidate(
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
) -> Pass1BundleCandidate | None:
    stub = step_cell(extractor, out_dir)
    if not is_physical_x(stub[0]):
        return Pass1BundleCandidate(
            candidate_id=f"{run_id}:p1:cand:{scan_index}:{extractor}:{out_dir}",
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
        return Pass1BundleCandidate(
            candidate_id=f"{run_id}:p1:cand:{scan_index}:{extractor}:{out_dir}",
            scan_index=scan_index,
            extractor_cell=extractor,
            output_direction=out_dir,
            output_stub_cell=stub,
            extension_cells=(),
            transport_kind=transport_kind,
            score=-1.0,
            reject_reason="stub_blocked",
        )

    if not cheap_escape_feasible(stub, transport_kind, reconstruction):
        return Pass1BundleCandidate(
            candidate_id=f"{run_id}:p1:cand:{scan_index}:{extractor}:{out_dir}",
            scan_index=scan_index,
            extractor_cell=extractor,
            output_direction=out_dir,
            output_stub_cell=stub,
            extension_cells=(),
            transport_kind=transport_kind,
            score=-1.0,
            reject_reason="cheap_escape_failed",
        )

    trial_used = set(used)
    trial_used.add(extractor)
    trial_used.add(stub)
    exts = grow_pass1_straight_extension_chain(
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
    score = float(n_ext) * 1000.0 - float(edge) * 10.0

    return Pass1BundleCandidate(
        candidate_id=f"{run_id}:p1:cand:{scan_index}:{extractor}:{out_dir}",
        scan_index=scan_index,
        extractor_cell=extractor,
        output_direction=out_dir,
        output_stub_cell=stub,
        extension_cells=exts,
        transport_kind=transport_kind,
        score=score,
        reject_reason=None,
    )


def _candidate_to_bundle(
    cand: Pass1BundleCandidate,
    *,
    run_id: str,
    bundle_index: int,
) -> PlacementBundle:
    eid = PlacementId(
        f"{run_id}:p1:e:{bundle_index}:" + f"{cand.extractor_cell[0]}:{cand.extractor_cell[1]}"
    )
    exts = tuple(
        ExtensionPlacement(
            placement_id=PlacementId(f"{run_id}:p1:x:{bundle_index}:{i}:{ec[0]}:{ec[1]}"),
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


def _pass1_cell_sort_key(c: BlueprintCell) -> tuple[int, int]:
    return (c[1], c[0])


def _pass1_probe_outputs_for_scan_cell(
    *,
    run_id: str,
    scan_index: int,
    extractor: BlueprintCell,
    mineable: frozenset[BlueprintCell],
    used: set[BlueprintCell],
    transport_kind: TransportKind,
    reconstruction: ReconstructionDTO,
    bbox: BBox,
    replay_events: list[dict[str, Any]] | None,
    replay_event_cap: int | None,
    beam: list[dict[str, object]],
    trace: TraceCollector,
    trace_step_box: list[int],
) -> list[Pass1BundleCandidate]:
    feasible: list[Pass1BundleCandidate] = []
    for out_dir in _OUTPUT_DIRS:
        cand = _build_candidate(
            run_id=run_id,
            scan_index=scan_index,
            extractor=extractor,
            out_dir=out_dir,
            mineable=mineable,
            used=used,
            transport_kind=transport_kind,
            reconstruction=reconstruction,
            bbox=bbox,
        )
        if cand is None:
            continue
        reject = cand.reject_reason
        _replay_append(
            replay_events,
            {
                "placement_pass": "pass1",
                "kind": "probe_output",
                "scan_index": scan_index,
                "extractor_cell": [extractor[0], extractor[1]],
                "output_direction": [out_dir[0], out_dir[1]],
                "output_stub_cell": [cand.output_stub_cell[0], cand.output_stub_cell[1]],
                "reject_reason": reject,
            },
            cap=replay_event_cap,
        )
        if reject is None:
            _pass1_emit_trace_event(
                trace,
                trace_step_box,
                run_id=run_id,
                event_type="pass1_output_probe_succeeded",
                committed=True,
                commit_reason=CommitReason.NORMAL_GAIN,
            )
        else:
            _pass1_emit_trace_event(
                trace,
                trace_step_box,
                run_id=run_id,
                event_type="pass1_output_probe_rejected",
                committed=False,
                commit_reason=None,
            )
        if reject is not None:
            beam.append(
                {
                    "placement_pass": "pass1",
                    "scan_index": scan_index,
                    "extractor_cell": extractor,
                    "output_direction": out_dir,
                    "score": cand.score,
                    "committed": False,
                    "reject_reason": reject,
                }
            )
            continue
        feasible.append(cand)
    return feasible


def _pass1_pick_best_feasible(
    feasible: list[Pass1BundleCandidate],
    extractor: BlueprintCell,
    bbox: BBox,
) -> Pass1BundleCandidate | None:
    if not feasible:
        return None
    max_ext = max(len(c.extension_cells) for c in feasible)
    pool0 = (
        [c for c in feasible if len(c.extension_cells) == max_ext]
        if max_ext > 0
        else list(feasible)
    )
    want_out = _preferred_pass1_output_direction(extractor, bbox)
    tier1 = [c for c in pool0 if c.output_direction == want_out]
    pool = tier1 if tier1 else pool0

    def _best_key(c: Pass1BundleCandidate) -> tuple[int, int, int]:
        return lex_key_pass1_best_output(
            extractor,
            bbox,
            len(c.extension_cells),
            c.output_direction,
        )

    return min(pool, key=_best_key)


def _pass1_try_commit_bundle(
    best: Pass1BundleCandidate,
    *,
    ctx: SolverRunContext,
    scan_index: int,
    used: set[BlueprintCell],
    bundles: list[PlacementBundle],
    commits: list[tuple[str, PlacementCommitState]],
    beam: list[dict[str, object]],
    transport_kind: TransportKind,
    bundle_index: int,
    replay_events: list[dict[str, Any]] | None,
    replay_event_cap: int | None,
    trace: TraceCollector,
    trace_step_box: list[int],
) -> int | None:
    """Return ``bundle_index + 1`` after a successful commit; ``None`` if skipped."""

    b = _candidate_to_bundle(best, run_id=ctx.run_id, bundle_index=bundle_index)
    occ = {b.extractor.cell, b.output_stub.cell}
    occ.update(ext.cell for ext in b.extensions)
    if occ & used:
        return None
    used.update(occ)
    bundles.append(b)
    commits.append((str(b.extractor.placement_id), PlacementCommitState.PROVISIONAL_PLACED))
    for ext in b.extensions:
        commits.append((str(ext.placement_id), PlacementCommitState.PROVISIONAL_PLACED))
    beam.append(
        {
            "placement_pass": "pass1",
            "scan_index": scan_index,
            "extractor_cell": best.extractor_cell,
            "output_direction": best.output_direction,
            "output_stub_cell": best.output_stub_cell,
            "score": best.score,
            "committed": True,
            "reject_reason": None,
            "placement_ids": (str(b.extractor.placement_id),)
            + tuple(str(x.placement_id) for x in b.extensions),
        }
    )
    _replay_append(
        replay_events,
        {
            "placement_pass": "pass1",
            "kind": "commit_bundle",
            "scan_index": scan_index,
            "bundle_index": bundle_index,
            "transport_kind": str(transport_kind.value),
            "extractor_cell": [b.extractor.cell[0], b.extractor.cell[1]],
            "output_direction": [best.output_direction[0], best.output_direction[1]],
            "output_stub_cell": [b.output_stub.cell[0], b.output_stub.cell[1]],
            "output_stub_physical": is_physical_x(b.output_stub.cell[0]),
            "extension_cells": [[c[0], c[1]] for c in (e.cell for e in b.extensions)],
        },
        cap=replay_event_cap,
    )
    _pass1_emit_trace_event(
        trace,
        trace_step_box,
        run_id=ctx.run_id,
        event_type="pass1_bundle_committed",
        committed=True,
        commit_reason=CommitReason.NORMAL_GAIN,
    )
    return bundle_index + 1


def _pass1_assemble_result(
    bundles: list[PlacementBundle],
    commits: list[tuple[str, PlacementCommitState]],
    beam: list[dict[str, object]],
    replay_events: list[dict[str, Any]] | None,
    replay_event_cap: int | None,
    *,
    run_id: str,
    trace: TraceCollector,
    trace_step_box: list[int],
    pass1_extractor_rim_only: bool,
    max_committed_extractor_depth: int,
    reject_count_by_reason: dict[str, int],
    pass1_stop_reason: str,
) -> Pass1Result:
    _replay_append(
        replay_events,
        {
            "placement_pass": "pass1",
            "kind": "pass1_end",
            "bundle_count": len(bundles),
            "pass1_extractor_rim_only": pass1_extractor_rim_only,
            "max_committed_extractor_depth": max_committed_extractor_depth,
            "reject_count_by_reason": dict(sorted(reject_count_by_reason.items())),
            "pass1_stop_reason": pass1_stop_reason,
        },
        cap=replay_event_cap,
    )
    _pass1_emit_trace_event(
        trace,
        trace_step_box,
        run_id=run_id,
        event_type="pass1_end",
        committed=False,
        commit_reason=None,
    )

    placement_occ: set[BlueprintCell] = set()
    stub_cells: set[BlueprintCell] = set()
    for b in bundles:
        placement_occ.add(b.extractor.cell)
        stub_cells.add(b.output_stub.cell)
        for ext in b.extensions:
            placement_occ.add(ext.cell)
    union_occ = placement_occ | stub_cells

    placement_sorted = tuple(sorted(placement_occ, key=_pass1_cell_sort_key))
    stub_sorted = tuple(sorted(stub_cells, key=_pass1_cell_sort_key))
    occupied = tuple(sorted(union_occ, key=_pass1_cell_sort_key))

    return Pass1Result(
        placements=tuple(bundles),
        placement_occupied_cells=placement_sorted,
        output_stub_cells=stub_sorted,
        occupied_cells=occupied,
        placement_commit_entries=tuple(commits),
        beam_trace=tuple(beam) if beam else None,
    )


def run_pass1_outer_placement(
    ctx: SolverRunContext,
    reconstruction: ReconstructionDTO,
    *,
    replay_events: list[dict[str, Any]] | None = None,
    replay_event_cap: int | None = 320,
    trace: TraceCollector,
) -> Pass1Result:
    """Greedy outer-first Pass1 (§7); does not mutate ``ctx`` or routing geometry."""

    mineable_cells = frozenset(reconstruction.mineable_placement_cells)
    if not mineable_cells:
        return Pass1Result()

    bbox = reconstruction.asteroid_bbox or _bbox_fallback(mineable_cells)
    if bbox is None:
        return Pass1Result()

    ordered = pass1_mineable_outer_first_order(mineable_cells, bbox)
    depth_by_cell = compute_mineable_perimeter_depth_by_cell(mineable_cells)

    used: set[BlueprintCell] = set()
    bundles: list[PlacementBundle] = []
    beam: list[dict[str, object]] = []
    commits: list[tuple[str, PlacementCommitState]] = []
    bundle_index = 0
    trace_step_box: list[int] = [0]
    reject_count_by_reason: dict[str, int] = {}
    max_committed_extractor_depth = -1

    def _bump_reject(reason: str) -> None:
        reject_count_by_reason[reason] = reject_count_by_reason.get(reason, 0) + 1

    _replay_append(
        replay_events,
        {"placement_pass": "pass1", "kind": "pass1_begin", "run_id": ctx.run_id},
        cap=replay_event_cap,
    )
    _pass1_emit_trace_event(
        trace,
        trace_step_box,
        run_id=ctx.run_id,
        event_type="pass1_begin",
        committed=False,
        commit_reason=None,
    )

    for scan_index, extractor in enumerate(ordered):
        if extractor in used:
            continue
        transport_kind = infer_transport_kind_for_mineable_cell(reconstruction, extractor)
        pd = depth_by_cell.get(extractor, -1)
        rim_ok = is_pass1_rim_extractor_cell(extractor, depth_by_cell)
        row: dict[str, Any] = {
            "placement_pass": "pass1",
            "kind": "consider_extract",
            "scan_index": scan_index,
            "extractor_cell": [extractor[0], extractor[1]],
            "perimeter_depth": int(pd),
        }
        if not rim_ok:
            row["reject_reason"] = "pass1_extractor_not_on_rim"
            _bump_reject("pass1_extractor_not_on_rim")
        _replay_append(replay_events, row, cap=replay_event_cap)
        _pass1_emit_trace_event(
            trace,
            trace_step_box,
            run_id=ctx.run_id,
            event_type="pass1_candidate_scanned",
            committed=False,
            commit_reason=None,
        )
        if not rim_ok:
            continue
        feasible = _pass1_probe_outputs_for_scan_cell(
            run_id=ctx.run_id,
            scan_index=scan_index,
            extractor=extractor,
            mineable=mineable_cells,
            used=used,
            transport_kind=transport_kind,
            reconstruction=reconstruction,
            bbox=bbox,
            replay_events=replay_events,
            replay_event_cap=replay_event_cap,
            beam=beam,
            trace=trace,
            trace_step_box=trace_step_box,
        )
        best = _pass1_pick_best_feasible(feasible, extractor, bbox)
        if best is None or best.reject_reason is not None:
            continue
        nxt = _pass1_try_commit_bundle(
            best,
            ctx=ctx,
            scan_index=scan_index,
            used=used,
            bundles=bundles,
            commits=commits,
            beam=beam,
            transport_kind=transport_kind,
            bundle_index=bundle_index,
            replay_events=replay_events,
            replay_event_cap=replay_event_cap,
            trace=trace,
            trace_step_box=trace_step_box,
        )
        if nxt is not None:
            bundle_index = nxt
            max_committed_extractor_depth = max(
                max_committed_extractor_depth, int(depth_by_cell.get(best.extractor_cell, 0))
            )

    return _pass1_assemble_result(
        bundles,
        commits,
        beam,
        replay_events,
        replay_event_cap,
        run_id=ctx.run_id,
        trace=trace,
        trace_step_box=trace_step_box,
        pass1_extractor_rim_only=True,
        max_committed_extractor_depth=max_committed_extractor_depth,
        reject_count_by_reason=reject_count_by_reason,
        pass1_stop_reason="mineable_ordered_scan_complete",
    )


__all__ = [
    "cheap_escape_feasible",
    "compute_mineable_perimeter_depth_by_cell",
    "is_pass1_rim_extractor_cell",
    "pass1_mineable_outer_first_order",
    "run_pass1_outer_placement",
]
