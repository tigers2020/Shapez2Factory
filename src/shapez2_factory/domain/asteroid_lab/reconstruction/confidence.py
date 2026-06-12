"""Reconstruction confidence / ambiguity (production acceptance; fixtures calibrate only).

``ReconstructionResult.confirmed_cells`` equals all asteroid field cells (solver SoT).
Mask-derived subsets are diagnostic-only in ``summary_json``.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shapez2_factory.domain.asteroid_lab.cleanup.result import CleanupResult

from shapez2_factory.domain.asteroid_lab.coord_frames import CoordFrame
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord
from shapez2_factory.domain.asteroid_lab.reconstruction.acceptance_topology import (
    acceptance_topology_from_reconstruction,
    constraint_violation_count,
    topology_coord_for_cell,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.evidence import (
    ASTEROID_FIELD_KINDS,
    is_asteroid_evidence,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.result import ReconstructionResult
from shapez2_factory.domain.asteroid_lab.service_dtos import DecodedCellDTO
from shapez2_factory.domain.asteroid_lab.wire_coerce import wire_float, wire_int

QUALITY_TIER_CONFIDENT = "CONFIDENT_RECONSTRUCTION"
QUALITY_TIER_PARTIAL = "PARTIAL"
QUALITY_TIER_AMBIGUOUS = "AMBIGUOUS"
QUALITY_TIER_FAILED = "FAILED"

_AMBIGUOUS_RATIO_MAX = 0.05
_CONFIDENCE_SCORE_MIN = 0.95


def _topology_coord(
    cell: DecodedCellDTO,
    params: object | None = None,
    *,
    coord_frame: CoordFrame,
) -> Coord | None:
    try:
        return topology_coord_for_cell(cell, params, coord_frame=coord_frame)
    except ValueError:
        return None


def _is_hard_evidence_cell(cell: DecodedCellDTO) -> bool:
    if cell.raw_entry_json.get("_replay_synthetic"):
        return False
    return is_asteroid_evidence(cell)


def _is_inferred_fill(cell: DecodedCellDTO) -> bool:
    return (
        bool(cell.raw_entry_json.get("_replay_synthetic"))
        and cell.cell_kind in ASTEROID_FIELD_KINDS
    )


def build_candidate_masks(
    cells: Sequence[DecodedCellDTO],
    *,
    wall_coords: Iterable[Coord],
    interior_patch_coords: Iterable[Coord],
    coord_frame: CoordFrame = CoordFrame.ISLAND_RAW,
) -> tuple[frozenset[Coord], frozenset[Coord]]:
    """Two topology-coordinate masks: interior-patch hint and wall-adjacent fill."""

    walls = frozenset(wall_coords)
    interior_patch = frozenset(interior_patch_coords)
    wall_adjacent: set[Coord] = set()
    for cell in cells:
        if not _is_inferred_fill(cell):
            continue
        sv = _topology_coord(cell, coord_frame=coord_frame)
        if sv is None:
            continue
        x, y = cell.x, cell.y
        touch = sum(1 for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)) if (x + dx, y + dy) in walls)
        if touch >= 2:
            wall_adjacent.add(sv)
    return interior_patch, frozenset(wall_adjacent)


def merge_mask_agreement(
    mineable: frozenset[Coord],
    mask_a: frozenset[Coord],
    mask_b: frozenset[Coord],
    *,
    hard_evidence: frozenset[Coord],
) -> tuple[frozenset[Coord], frozenset[Coord], dict[Coord, float]]:
    """Classify mineable cells; hard evidence is never ambiguous."""

    confirmed: set[Coord] = set(hard_evidence & mineable)
    ambiguous: set[Coord] = set()
    by_cell: dict[Coord, float] = {}

    for sv in mineable:
        if sv in hard_evidence:
            confirmed.add(sv)
            by_cell[sv] = 1.0
            continue
        votes = (sv in mask_a) + (sv in mask_b)
        if votes >= 2 or sv in mask_a:
            confirmed.add(sv)
            by_cell[sv] = 0.95
        elif votes == 1:
            ambiguous.add(sv)
            by_cell[sv] = 0.75
        else:
            ambiguous.add(sv)
            by_cell[sv] = 0.4

    return frozenset(confirmed), frozenset(ambiguous), by_cell


def compute_confidence_metrics(
    mineable: frozenset[Coord],
    ambiguous: frozenset[Coord],
    confidence_by_cell: dict[Coord, float],
    *,
    constraint_violation_count: int,
) -> dict[str, float | int | bool]:
    total = len(mineable)
    amb = len(ambiguous)
    ratio = (amb / total) if total else 0.0
    scores = [confidence_by_cell[sv] for sv in mineable if sv in confidence_by_cell]
    mean_score = round(sum(scores) / len(scores), 6) if scores else 1.0
    return {
        "ambiguous_cell_count": amb,
        "confirmed_cell_count": total - amb,
        "ambiguous_ratio": round(ratio, 6),
        "confidence_score": mean_score,
        "constraint_violation_count": constraint_violation_count,
        "hard_evidence_preserved": constraint_violation_count == 0,
    }


def quality_tier_from_metrics(metrics: dict[str, float | int | bool]) -> str:
    if int(metrics.get("constraint_violation_count", 0)) > 0:
        return QUALITY_TIER_FAILED
    ratio = float(metrics.get("ambiguous_ratio", 1.0))
    score = float(metrics.get("confidence_score", 0.0))
    if ratio <= _AMBIGUOUS_RATIO_MAX and score >= _CONFIDENCE_SCORE_MIN:
        return QUALITY_TIER_CONFIDENT
    if ratio <= 0.15 and score >= 0.85:
        return QUALITY_TIER_PARTIAL
    if ratio <= 0.35:
        return QUALITY_TIER_AMBIGUOUS
    return QUALITY_TIER_FAILED


def reconstruction_acceptance_ok(result: ReconstructionResult) -> bool:
    summary = result.summary_json
    return (
        bool(summary.get("hard_evidence_preserved", True))
        and wire_int(summary.get("constraint_violation_count", 0)) == 0
        and wire_float(summary.get("ambiguous_ratio", 1.0)) <= _AMBIGUOUS_RATIO_MAX
        and result.confidence_score >= _CONFIDENCE_SCORE_MIN
        and result.quality_tier == QUALITY_TIER_CONFIDENT
    )


def _constraint_violations(result: ReconstructionResult) -> int:
    return constraint_violation_count(result, ambiguous=result.ambiguous_cells)


def apply_confidence_to_result(
    result: ReconstructionResult,
    *,
    wall_coords: Iterable[Coord],
    interior_patch_coords: Iterable[Coord],
    cleanup: CleanupResult | None = None,
) -> ReconstructionResult:
    """Attach confidence fields and summary metrics to a reconstruction result."""

    coord_frame = result.coord_frame
    hard: set[Coord] = set()
    mineable: set[Coord] = set()
    for cell in result.cells:
        sv = _topology_coord(cell, coord_frame=coord_frame)
        if sv is None:
            continue
        if cell.cell_kind in ASTEROID_FIELD_KINDS:
            mineable.add(sv)
        if _is_hard_evidence_cell(cell):
            hard.add(sv)

    mask_a, mask_b = build_candidate_masks(
        result.cells,
        wall_coords=wall_coords,
        interior_patch_coords=interior_patch_coords,
        coord_frame=coord_frame,
    )
    confirmed, ambiguous, by_cell = merge_mask_agreement(
        frozenset(mineable),
        mask_a,
        mask_b,
        hard_evidence=frozenset(hard),
    )

    if cleanup is not None:
        from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
            build_reconstruction_complete_map,
        )

        complete = build_reconstruction_complete_map(cleanup=cleanup, recon=result)
        field_cells = complete.field_cells
        external_void = complete.external_void_cells
    else:
        field_cells = frozenset(mineable)
        try:
            external_void = acceptance_topology_from_reconstruction(
                result, coord_frame=coord_frame
            ).external_void_cells
        except ValueError:
            external_void = frozenset()

    provisional = ReconstructionResult(
        cells=result.cells,
        summary_json=dict(result.summary_json),
        outer_rim_coords=result.outer_rim_coords,
        coord_frame=coord_frame,
        confirmed_cells=confirmed,
        ambiguous_cells=ambiguous,
        external_void_cells=external_void,
        confidence_score=1.0,
        confidence_by_cell=tuple(sorted(by_cell.items())),
        quality_flags=frozenset(),
        quality_tier=QUALITY_TIER_CONFIDENT,
    )
    violations = _constraint_violations(provisional)
    metrics = compute_confidence_metrics(
        frozenset(mineable),
        ambiguous,
        by_cell,
        constraint_violation_count=violations,
    )
    tier = quality_tier_from_metrics(metrics)
    flags: set[str] = set()
    if float(metrics["ambiguous_ratio"]) > _AMBIGUOUS_RATIO_MAX:
        flags.add("ambiguous_ratio_high")
    if float(metrics["confidence_score"]) < _CONFIDENCE_SCORE_MIN:
        flags.add("confidence_score_low")
    if violations:
        flags.add("constraint_violations")

    summary = dict(result.summary_json)
    summary.update(metrics)
    summary["quality_tier"] = tier
    summary["quality_flags"] = sorted(flags)

    return ReconstructionResult(
        cells=result.cells,
        summary_json=summary,
        outer_rim_coords=result.outer_rim_coords,
        coord_frame=coord_frame,
        confirmed_cells=field_cells,
        ambiguous_cells=frozenset(),
        external_void_cells=external_void,
        confidence_score=float(metrics["confidence_score"]),
        confidence_by_cell=tuple(sorted(by_cell.items())),
        quality_flags=frozenset(flags),
        quality_tier=tier,
    )


_PERSIST_SUMMARY_KEYS = (
    "quality_tier",
    "confidence_score",
    "ambiguous_ratio",
    "ambiguous_cell_count",
    "confirmed_cell_count",
    "constraint_violation_count",
    "hard_evidence_preserved",
    "quality_flags",
    "filled_hole_cell_count",
    "interior_candidate_count",
    "external_pocket_filled_count",
)


def reconstruction_persist_summary(result: ReconstructionResult) -> dict[str, object]:
    """Blueprint ``_asteroid_lab_reconstruction.summary_json`` (no per-cell scores)."""

    out: dict[str, object] = {
        k: result.summary_json[k] for k in _PERSIST_SUMMARY_KEYS if k in result.summary_json
    }
    out["reconstruction_acceptance_ok"] = reconstruction_acceptance_ok(result)
    return out


__all__ = [
    "QUALITY_TIER_AMBIGUOUS",
    "QUALITY_TIER_CONFIDENT",
    "QUALITY_TIER_FAILED",
    "QUALITY_TIER_PARTIAL",
    "apply_confidence_to_result",
    "build_candidate_masks",
    "compute_confidence_metrics",
    "merge_mask_agreement",
    "quality_tier_from_metrics",
    "reconstruction_acceptance_ok",
    "reconstruction_persist_summary",
]
