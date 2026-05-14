"""
Pass2 internal fill placement (STEP 3, §8).

Blocked set = Pass1 fixed geometry + preserved blueprint barriers. Cheap escape is
probe-only (§8.2–§8.3). ``routing_state.final_route_cells`` is not read or written.
"""

from __future__ import annotations

import math

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BBox,
    BlueprintCell,
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
    PlacementCommitState,
    TransportKind,
)

from .bundle_candidate import (
    CARDINAL_DIRS,
    Pass2BundleCandidate,
    blocked_by_building,
    grow_pass2_branching_extension_cells,
    infer_transport_kind,
    lex_key_pass2_best_output,
    step_cell,
)
from .pass1_outer import cheap_escape_feasible


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


def _sort_mineable_interior_first(
    cells: frozenset[BlueprintCell],
    bbox: BBox,
) -> tuple[BlueprintCell, ...]:
    """Inner cells first (max edge distance), then same angular sweep as Pass1."""

    cx = (bbox.min_x + bbox.max_x) / 2.0
    cy = (bbox.min_y + bbox.max_y) / 2.0

    def edge_distance(c: BlueprintCell) -> int:
        x, y = c
        return min(x - bbox.min_x, bbox.max_x - x, y - bbox.min_y, bbox.max_y - y)

    def sort_key(c: BlueprintCell) -> tuple[int, float, int, int]:
        ang = math.atan2(c[0] - cx, -(c[1] - cy))
        return (-edge_distance(c), ang, c[1], c[0])

    return tuple(sorted(cells, key=sort_key))


def _build_pass2_candidate(
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
) -> Pass2BundleCandidate | None:
    stub = step_cell(extractor, out_dir)
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

    if not cheap_escape_feasible(stub, transport_kind, reconstruction):
        return Pass2BundleCandidate(
            candidate_id=f"{run_id}:p2:cand:{scan_index}:{extractor}:{out_dir}",
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


def _pass2_candidate_to_bundle(
    cand: Pass2BundleCandidate,
    *,
    run_id: str,
    bundle_index: int,
) -> PlacementBundle:
    eid = PlacementId(
        f"{run_id}:p2:e:{bundle_index}:" f"{cand.extractor_cell[0]}:{cand.extractor_cell[1]}"
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


def run_pass2_internal_fill(ctx: SolverRunContext, pass1: Pass1Result) -> Pass2Result:
    """Greedy interior Pass2 (§8); does not read ``final_route_cells`` or mutate ``ctx``."""

    reconstruction = ctx.reconstruction
    mineable_cells = frozenset(reconstruction.mineable_placement_cells)
    if not mineable_cells:
        return Pass2Result()

    bbox = reconstruction.asteroid_bbox or _bbox_fallback(mineable_cells)
    if bbox is None:
        return Pass2Result()

    blocked = build_pass2_blocked_set(pass1, reconstruction)
    used: set[BlueprintCell] = set(blocked)
    remaining = frozenset(c for c in mineable_cells if c not in blocked)
    if not remaining:
        return Pass2Result()

    transport_kind = infer_transport_kind(reconstruction)
    ordered = _sort_mineable_interior_first(remaining, bbox)

    bundles: list[PlacementBundle] = []
    beam: list[dict[str, object]] = []
    commits: list[tuple[str, PlacementCommitState]] = []
    bundle_index = 0

    for scan_index, extractor in enumerate(ordered):
        if extractor in used:
            continue
        feasible: list[Pass2BundleCandidate] = []
        for out_dir in CARDINAL_DIRS:
            cand = _build_pass2_candidate(
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
            if cand.reject_reason is not None:
                beam.append(
                    {
                        "placement_pass": "pass2",
                        "extractor_cell": extractor,
                        "output_direction": out_dir,
                        "score": cand.score,
                        "committed": False,
                        "reject_reason": cand.reject_reason,
                    }
                )
                continue
            feasible.append(cand)

        best: Pass2BundleCandidate | None = None
        if feasible:
            max_ext = max(len(c.extension_cells) for c in feasible)
            if max_ext > 0:
                feasible = [c for c in feasible if len(c.extension_cells) > 0]
            best = min(
                feasible,
                key=lambda c: lex_key_pass2_best_output(
                    extractor,
                    bbox,
                    len(c.extension_cells),
                    c.output_direction,
                ),
            )

        if best is None or best.reject_reason is not None:
            continue

        b = _pass2_candidate_to_bundle(best, run_id=ctx.run_id, bundle_index=bundle_index)
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
                "placement_pass": "pass2",
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
        bundle_index += 1

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
    )


__all__ = ["build_pass2_blocked_set", "run_pass2_internal_fill"]
