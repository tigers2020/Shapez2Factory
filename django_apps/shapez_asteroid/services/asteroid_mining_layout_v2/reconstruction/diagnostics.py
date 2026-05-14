"""
STEP 1 reconstruction diagnostics (read-only observability).

Does not modify ``ReconstructionDTO`` or drive Pass1/placement/routing input.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Literal

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.decode import (
    analyze_decoded_layout,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BlueprintCell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    MineableEmptyCause,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.reconstruction import (
    DuplicateCoordSampleDTO,
    ReconstructionDiagnosisDTO,
    ReconstructionDTO,
)
from django_apps.shapez_asteroid.services.blueprint_entry_parsing import int_or_none as _int_or_none
from django_apps.shapez_asteroid.services.style_classifier import PlotStyle, classify_layout_type

from ..domain.decoded_blueprint import DecodedBlueprintDocument
from .asteroid_reconstruction import (
    _is_asteroid_shell_layout_type,
    gather_bp_entries_recursive,
    reconstruct_asteroid_mining_field,
)

_EntryKind = Literal[
    "shell",
    "belt",
    "pipe",
    "extractor",
    "extension",
    "platform",
    "other",
]


def _compact_t(t: object) -> str:
    if t is None:
        return ""
    return str(t).strip().lower().replace("_", "")


def _normalize_t_raw(item: dict[str, Any]) -> str | None:
    t_raw = item.get("T")
    if isinstance(t_raw, str):
        return t_raw
    if t_raw is None:
        return None
    return str(t_raw)


def _entry_kind(t_str: str | None) -> _EntryKind:
    if _is_asteroid_shell_layout_type(t_str):
        return "shell"
    style = classify_layout_type(t_str)
    if style is PlotStyle.belt:
        return "belt"
    if style is PlotStyle.pipe:
        return "pipe"
    if style in (
        PlotStyle.fluid_miner,
        PlotStyle.miner,
        PlotStyle.extractor,
        PlotStyle.booster,
    ):
        return "extractor"
    if style in (PlotStyle.extension, PlotStyle.fluid_extension):
        return "extension"
    if style is PlotStyle.platform:
        return "platform"
    return "other"


def _permanent_blocking_kinds_from_cell_kinds(kinds: set[_EntryKind]) -> tuple[str, ...]:
    """Kinds that block restored mineable placement (belt/pipe/platform/other only)."""

    labels: list[str] = []
    if "belt" in kinds:
        labels.append("belt")
    if "pipe" in kinds:
        labels.append("pipe")
    if "platform" in kinds:
        labels.append("platform")
    if "other" in kinds:
        labels.append("other_barrier")
    return tuple(sorted(labels))


def _frozen_count_pairs(counter: Counter[str]) -> tuple[tuple[str, int], ...]:
    if not counter:
        return ()
    return tuple(sorted(counter.items(), key=lambda kv: (-kv[1], kv[0])))


def _other_barrier_cells_from_entries(doc: dict[str, Any]) -> frozenset[BlueprintCell]:
    """Cells classified as ``other_barrier`` (same branch as ``asteroid_reconstruction``)."""

    other: set[BlueprintCell] = set()
    for item in gather_bp_entries_recursive(doc):
        x_val = _int_or_none(item.get("X"))
        if x_val is None or x_val == 0:
            continue
        y_val = _int_or_none(item.get("Y"))
        if y_val is None:
            y_val = 0
        xy: BlueprintCell = (x_val, y_val)
        t_str = _normalize_t_raw(item)
        if _is_asteroid_shell_layout_type(t_str):
            continue
        style = classify_layout_type(t_str)
        if style is PlotStyle.belt:
            continue
        if style is PlotStyle.pipe:
            continue
        if style in (
            PlotStyle.fluid_miner,
            PlotStyle.miner,
            PlotStyle.extractor,
            PlotStyle.booster,
        ):
            continue
        if style in (PlotStyle.extension, PlotStyle.fluid_extension):
            continue
        if style is PlotStyle.platform:
            continue
        other.add(xy)
    return frozenset(other)


def _platform_cells_from_entries(doc: dict[str, Any]) -> frozenset[BlueprintCell]:
    """Platform cells (not on ``ReconstructionDTO``; mirror STEP 1 entry classification)."""

    plat: set[BlueprintCell] = set()
    for item in gather_bp_entries_recursive(doc):
        x_val = _int_or_none(item.get("X"))
        if x_val is None or x_val == 0:
            continue
        y_val = _int_or_none(item.get("Y"))
        if y_val is None:
            y_val = 0
        xy: BlueprintCell = (x_val, y_val)
        t_str = _normalize_t_raw(item)
        if _is_asteroid_shell_layout_type(t_str):
            continue
        if classify_layout_type(t_str) is PlotStyle.platform:
            plat.add(xy)
    return frozenset(plat)


def diagnose_reconstruction_mineable_empty(
    decoded_blueprint: dict[str, Any] | DecodedBlueprintDocument,
    reconstruction: ReconstructionDTO | None = None,
) -> ReconstructionDiagnosisDTO:
    """Aggregate reconstruction stats and a deterministic ``primary_cause`` label."""

    doc = (
        decoded_blueprint.as_mutable_dict()
        if isinstance(decoded_blueprint, DecodedBlueprintDocument)
        else dict(decoded_blueprint)
    )
    entries = gather_bp_entries_recursive(doc)
    total_entries = len(entries)

    by_cell: dict[BlueprintCell, list[str | None]] = defaultdict(list)
    for item in entries:
        x_val = _int_or_none(item.get("X"))
        if x_val is None or x_val == 0:
            continue
        y_val = _int_or_none(item.get("Y"))
        if y_val is None:
            y_val = 0
        xy: BlueprintCell = (x_val, y_val)
        by_cell[xy].append(_normalize_t_raw(item))

    unique_coord_count = len(by_cell)
    duplicate_coord_count = sum(1 for _c, ts in by_cell.items() if len(ts) > 1)

    recon = reconstruction if reconstruction is not None else reconstruct_asteroid_mining_field(doc)
    shell_f = frozenset(recon.extraction_shell_cells)
    interior_f = frozenset(recon.interior_patch_cells)
    belt_f = frozenset(recon.belt_cells)
    pipe_f = frozenset(recon.pipe_cells)
    ext_f = frozenset(recon.extractor_cells)
    exn_f = frozenset(recon.extension_cells)
    plat_f = _platform_cells_from_entries(doc)
    other_f = _other_barrier_cells_from_entries(doc)

    permanent_blocking_for_mineable = belt_f | pipe_f | plat_f | other_f

    coords_shell_blocking = sum(1 for c in shell_f if c in permanent_blocking_for_mineable)
    coords_shell_belt = sum(1 for c in shell_f if c in belt_f)
    coords_shell_pipe = sum(1 for c in shell_f if c in pipe_f)
    coords_shell_extractor = sum(1 for c in shell_f if c in ext_f)
    coords_shell_extension = sum(1 for c in shell_f if c in exn_f)

    candidate_union = shell_f | interior_f | ext_f | exn_f
    candidate_before_blocking = len(candidate_union)
    mineable_f = frozenset(recon.mineable_placement_cells)
    mineable_n = len(mineable_f)
    blocked_candidate = len(candidate_union - mineable_f)

    unrecognized: Counter[str] = Counter()
    asteroid_like_unrec: Counter[str] = Counter()
    for item in entries:
        t_str = _normalize_t_raw(item)
        kind = _entry_kind(t_str)
        if kind == "other" and t_str is not None:
            unrecognized[t_str] += 1
            if "asteroid" in _compact_t(t_str) and not _is_asteroid_shell_layout_type(t_str):
                asteroid_like_unrec[t_str] += 1

    sample_dtos: list[DuplicateCoordSampleDTO] = []
    for cell, t_vals in sorted(by_cell.items(), key=lambda kv: (-len(kv[1]), kv[0][1], kv[0][0])):
        kinds = {_entry_kind(t) for t in t_vals}
        has_shell = "shell" in kinds
        has_blocking = bool(kinds & {"belt", "pipe", "platform", "other"})
        if len(t_vals) <= 1 and not (has_shell and has_blocking):
            continue
        bk = _permanent_blocking_kinds_from_cell_kinds(kinds)
        sample_dtos.append(
            DuplicateCoordSampleDTO(
                cell=cell,
                t_values=tuple(t_vals),
                has_shell=has_shell,
                has_blocking=has_blocking,
                blocking_kinds=bk,
            )
        )
    duplicate_coord_samples = tuple(sample_dtos[:10])

    preview_count: int | None = None
    preview_ids: tuple[str, ...] = ()
    note_tail = ""
    try:
        from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2 import (
            preview_reconstruction_timeline as _preview,
        )

        sk = analyze_decoded_layout(doc).source_kind.value
        preview_res = _preview.build_v2_preview_map_frames(doc, recon, source_kind=sk)
        frames = preview_res.frames
        preview_count = len(frames)
        preview_ids = tuple(
            str(f.get("id", "")) for f in frames[:12] if isinstance(f, dict) and f.get("id")
        )
    except (ImportError, TypeError, ValueError, KeyError) as exc:
        preview_count = None
        preview_ids = ()
        note_tail = f"preview_frames_unavailable:{type(exc).__name__}"

    shell_n = len(recon.extraction_shell_cells)
    interior_n = len(recon.interior_patch_cells)

    primary, note = _classify_primary_cause(
        mineable_n=mineable_n,
        shell_n=shell_n,
        asteroid_like_unrecognized=asteroid_like_unrec,
        coords_shell_blocking=coords_shell_blocking,
        candidate_before_blocking=candidate_before_blocking,
        blocked_candidate=blocked_candidate,
    )
    if note_tail:
        note = (note + "; " if note else "") + note_tail

    return ReconstructionDiagnosisDTO(
        total_entries=total_entries,
        unique_coord_count=unique_coord_count,
        duplicate_coord_count=duplicate_coord_count,
        extraction_shell_count=shell_n,
        interior_patch_count=interior_n,
        mineable_placement_count=mineable_n,
        belt_count=len(recon.belt_cells),
        pipe_count=len(recon.pipe_cells),
        extractor_count=len(recon.extractor_cells),
        extension_count=len(recon.extension_cells),
        platform_count=len(plat_f),
        other_barrier_count=len(other_f),
        coords_with_shell_and_blocking_count=coords_shell_blocking,
        coords_with_shell_and_belt_count=coords_shell_belt,
        coords_with_shell_and_pipe_count=coords_shell_pipe,
        coords_with_shell_and_extractor_count=coords_shell_extractor,
        coords_with_shell_and_extension_count=coords_shell_extension,
        candidate_before_blocking_count=candidate_before_blocking,
        blocked_candidate_count=blocked_candidate,
        unrecognized_t_counts=_frozen_count_pairs(unrecognized),
        asteroid_like_unrecognized_t_counts=_frozen_count_pairs(asteroid_like_unrec),
        duplicate_coord_samples=duplicate_coord_samples,
        preview_timeline_frame_count=preview_count,
        preview_timeline_frame_ids_sample=preview_ids,
        primary_cause=primary,
        note=note,
    )


def _classify_primary_cause(
    *,
    mineable_n: int,
    shell_n: int,
    asteroid_like_unrecognized: Counter[str],
    coords_shell_blocking: int,
    candidate_before_blocking: int,
    blocked_candidate: int,
) -> tuple[MineableEmptyCause, str]:
    if mineable_n > 0:
        return MineableEmptyCause.NOT_EMPTY, ""

    if shell_n == 0 and asteroid_like_unrecognized:
        return (
            MineableEmptyCause.SHELL_T_NOT_RECOGNIZED,
            "asteroid_like_unrecognized_t_counts_non_empty",
        )

    if coords_shell_blocking > 0:
        return MineableEmptyCause.DUPLICATE_COORD_OVERLAY_BLOCKED, "shell_coords_overlap_blocking"

    if candidate_before_blocking > 0 and blocked_candidate == candidate_before_blocking:
        return MineableEmptyCause.ALL_CANDIDATES_BLOCKED, "all_union_candidates_removed_by_blocking"

    if 0 < shell_n < 4:
        return MineableEmptyCause.SMALL_OR_FRAGMENTED_SHELL, "extraction_shell_count_lt_4"

    return MineableEmptyCause.UNKNOWN, ""


__all__ = ["diagnose_reconstruction_mineable_empty"]
