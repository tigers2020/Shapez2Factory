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
"""

from __future__ import annotations

import math
from collections import deque
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BBox,
    BlueprintCell,
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
    PlacementCommitState,
    TransportKind,
)

from .bundle_candidate import (
    CARDINAL_DIRS,
    Pass1BundleCandidate,
    blocked_by_building,
    grow_extension_cells,
    infer_transport_kind,
    lex_key_pass1_best_output,
    step_cell,
)

_OUTPUT_DIRS = CARDINAL_DIRS


def _bbox_fallback(cells: frozenset[BlueprintCell]) -> BBox | None:
    if not cells:
        return None
    xs = [c[0] for c in cells]
    ys = [c[1] for c in cells]
    return BBox(min_x=min(xs), min_y=min(ys), max_x=max(xs), max_y=max(ys))


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


def cheap_escape_feasible(
    stub: BlueprintCell,
    transport_kind: TransportKind,
    reconstruction: ReconstructionDTO,
) -> bool:
    """4-neighbor BFS from stub; same-kind belt/pipe traversable (§3.1 merge hint)."""

    bbox = reconstruction.asteroid_bbox or _bbox_fallback(
        frozenset(reconstruction.mineable_placement_cells)
    )
    if bbox is None:
        return False
    margin = reconstruction.external_margin or 3

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
    bundle_index: int,
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
    exts = grow_extension_cells(
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
        f"{run_id}:p1:e:{bundle_index}:" f"{cand.extractor_cell[0]}:{cand.extractor_cell[1]}"
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


def run_pass1_outer_placement(
    ctx: SolverRunContext,
    reconstruction: ReconstructionDTO,
    *,
    replay_events: list[dict[str, Any]] | None = None,
    replay_event_cap: int | None = 320,
) -> Pass1Result:
    """Greedy outer-first Pass1 (§7); does not mutate ``ctx`` or routing geometry."""

    mineable_cells = frozenset(reconstruction.mineable_placement_cells)
    if not mineable_cells:
        return Pass1Result()

    bbox = reconstruction.asteroid_bbox or _bbox_fallback(mineable_cells)
    if bbox is None:
        return Pass1Result()

    transport_kind = infer_transport_kind(reconstruction)
    ordered = pass1_mineable_outer_first_order(mineable_cells, bbox)

    used: set[BlueprintCell] = set()
    bundles: list[PlacementBundle] = []
    beam: list[dict[str, object]] = []
    commits: list[tuple[str, PlacementCommitState]] = []
    bundle_index = 0

    _replay_append(
        replay_events,
        {"placement_pass": "pass1", "kind": "pass1_begin", "run_id": ctx.run_id},
        cap=replay_event_cap,
    )

    for scan_index, extractor in enumerate(ordered):
        if extractor in used:
            continue
        _replay_append(
            replay_events,
            {
                "placement_pass": "pass1",
                "kind": "consider_extract",
                "scan_index": scan_index,
                "extractor_cell": [extractor[0], extractor[1]],
            },
            cap=replay_event_cap,
        )
        best: Pass1BundleCandidate | None = None
        feasible: list[Pass1BundleCandidate] = []
        for out_dir in _OUTPUT_DIRS:
            cand = _build_candidate(
                run_id=ctx.run_id,
                bundle_index=bundle_index,
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

        if feasible:
            max_ext = max(len(c.extension_cells) for c in feasible)
            if max_ext > 0:
                feasible = [c for c in feasible if len(c.extension_cells) > 0]
            best = min(
                feasible,
                key=lambda c: lex_key_pass1_best_output(
                    extractor,
                    bbox,
                    len(c.extension_cells),
                    c.output_direction,
                ),
            )

        if best is None or best.reject_reason is not None:
            continue

        b = _candidate_to_bundle(best, run_id=ctx.run_id, bundle_index=bundle_index)
        occ = {b.extractor.cell, b.output_stub.cell}
        occ.update(ext.cell for ext in b.extensions)
        if occ & used:
            continue
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
                "output_stub_physical": False,
                "extension_cells": [[c[0], c[1]] for c in (e.cell for e in b.extensions)],
            },
            cap=replay_event_cap,
        )
        bundle_index += 1

    _replay_append(
        replay_events,
        {
            "placement_pass": "pass1",
            "kind": "pass1_end",
            "bundle_count": len(bundles),
        },
        cap=replay_event_cap,
    )

    placement_occ: set[BlueprintCell] = set()
    stub_cells: set[BlueprintCell] = set()
    for b in bundles:
        placement_occ.add(b.extractor.cell)
        stub_cells.add(b.output_stub.cell)
        for ext in b.extensions:
            placement_occ.add(ext.cell)
    union_occ = placement_occ | stub_cells

    def _cell_sort_key(c: BlueprintCell) -> tuple[int, int]:
        return (c[1], c[0])

    placement_sorted = tuple(sorted(placement_occ, key=_cell_sort_key))
    stub_sorted = tuple(sorted(stub_cells, key=_cell_sort_key))
    occupied = tuple(sorted(union_occ, key=_cell_sort_key))

    return Pass1Result(
        placements=tuple(bundles),
        placement_occupied_cells=placement_sorted,
        output_stub_cells=stub_sorted,
        occupied_cells=occupied,
        placement_commit_entries=tuple(commits),
        beam_trace=tuple(beam) if beam else None,
    )


__all__ = [
    "cheap_escape_feasible",
    "pass1_mineable_outer_first_order",
    "run_pass1_outer_placement",
]
