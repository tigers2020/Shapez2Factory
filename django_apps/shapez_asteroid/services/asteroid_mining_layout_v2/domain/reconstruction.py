"""STEP 1 reconstruction domain DTOs (§6) — pure domain; no I/O, Django, preview, serialization."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BBox,
    BlueprintCell,
    Coord,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    AsteroidResourceKind,
    MineableEmptyCause,
)

MineableSemanticSource = Literal[
    "extraction_shell",
    "interior_patch_inferred",
    "equipment_footprint",
]


@dataclass(frozen=True, slots=True)
class MineableCellSemantic:
    """Canonical asteroid field semantics for one mineable placement cell (STEP 1)."""

    cell: BlueprintCell
    resource_kind: AsteroidResourceKind
    source: MineableSemanticSource


@dataclass(frozen=True, slots=True)
class GridMask:
    """Immutable blueprint cell set (passable / blocked / occupied masks)."""

    cells: frozenset[BlueprintCell]

    @classmethod
    def from_coords(cls, coords: tuple[Coord, ...]) -> GridMask:
        return cls(frozenset(c.as_tuple() for c in coords))


@dataclass(frozen=True, slots=True)
class ReconstructionDTO:
    """STEP 1 outputs (§6): shell, barriers, transport split, inferred interior, mineable.

    ``mineable_placement_cells`` is the restored asteroid mining region for placement:
    extraction shell ∪ inferred interior **mining-region** cells (inside the closed
    transport-stripped hull ``full_barrier − belt − pipe``, not arbitrary off-map void)
    ∪ existing extractor/miner footprint ∪ existing
    extension footprint, minus **permanent** obstacles (belt, pipe, platform, other solid
    layout kinds). ``extractor_cells`` / ``extension_cells`` keep blueprint snapshots;
    ``equipment_footprint_mineable_cells`` is their sorted union (prior mineable evidence).
    ``full_barrier_cells`` remains the union of all occupied blueprint coordinates (not
    equivalent to permanent mineable blockers).

    ``interior_patch_cells`` are included in the same formal asteroid field as mineable
    placement targets; they are not ``RouteZone.INTERNAL_VOID`` / off-map void for later passes.

    ``mineable_cell_semantics`` has exactly one row per ``mineable_placement_cell`` when
    produced by ``reconstruct_asteroid_mining_field``; later passes should prefer this over
    map labels for shape vs fluid.

    **Void topology (STEP 1, Pass1 gating)**: ``external_void_cells`` / ``internal_void_cells``
    classify empty lattice sites inside ``asteroid_bbox ± external_margin`` reachable (or
    not) from the rectangle border without crossing ``mineable_placement_cells`` or
    ``permanent_mineable_blocker_cells``. **Single Pass1 rim:** ``outer_rim_mineable_cells``
    — mineable cells 4-adjacent to external void only. There is no separate “hole rim”
    field; a filled hole is just mineable and only the true exterior rim remains.
    """

    mineable_placement_cells: tuple[BlueprintCell, ...] = ()
    extraction_shell_cells: tuple[BlueprintCell, ...] = ()
    full_barrier_cells: tuple[BlueprintCell, ...] = ()
    belt_cells: tuple[BlueprintCell, ...] = ()
    pipe_cells: tuple[BlueprintCell, ...] = ()
    extractor_cells: tuple[BlueprintCell, ...] = ()
    extension_cells: tuple[BlueprintCell, ...] = ()
    equipment_footprint_mineable_cells: tuple[BlueprintCell, ...] = ()
    interior_patch_cells: tuple[BlueprintCell, ...] = ()
    mineable_cell_semantics: tuple[MineableCellSemantic, ...] = ()
    permanent_mineable_blocker_cells: tuple[BlueprintCell, ...] = ()
    external_void_cells: tuple[BlueprintCell, ...] = ()
    internal_void_cells: tuple[BlueprintCell, ...] = ()
    outer_rim_mineable_cells: tuple[BlueprintCell, ...] = ()
    asteroid_bbox: BBox | None = None
    external_margin: int = 0
    external_margin_bbox_source: Literal["mineable", "shell", "none"] = "none"


# Alias for CANON §6 naming (``SolverRunContext.reconstruction`` keeps field type).
ReconstructionResult = ReconstructionDTO


@dataclass(frozen=True, slots=True)
class DuplicateCoordSampleDTO:
    """One coordinate with multiple blueprint entries (overlay / duplicate ``T`` rows)."""

    cell: BlueprintCell
    t_values: tuple[str | None, ...]
    has_shell: bool
    has_blocking: bool
    blocking_kinds: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ReconstructionDiagnosisDTO:
    """Read-only STEP 1 reconstruction diagnostics; must not drive solver or placement input."""

    total_entries: int = 0
    unique_coord_count: int = 0
    duplicate_coord_count: int = 0

    extraction_shell_count: int = 0
    interior_patch_count: int = 0
    mineable_placement_count: int = 0

    belt_count: int = 0
    pipe_count: int = 0
    extractor_count: int = 0
    extension_count: int = 0
    platform_count: int = 0
    other_barrier_count: int = 0

    coords_with_shell_and_blocking_count: int = 0
    coords_with_shell_and_belt_count: int = 0
    coords_with_shell_and_pipe_count: int = 0
    coords_with_shell_and_extractor_count: int = 0
    coords_with_shell_and_extension_count: int = 0

    candidate_before_blocking_count: int = 0
    blocked_candidate_count: int = 0

    unrecognized_t_counts: tuple[tuple[str, int], ...] = ()
    asteroid_like_unrecognized_t_counts: tuple[tuple[str, int], ...] = ()

    duplicate_coord_samples: tuple[DuplicateCoordSampleDTO, ...] = ()

    preview_timeline_frame_count: int | None = None
    preview_timeline_frame_ids_sample: tuple[str, ...] = ()

    primary_cause: MineableEmptyCause = MineableEmptyCause.UNKNOWN
    note: str = ""


__all__ = [
    "DuplicateCoordSampleDTO",
    "GridMask",
    "MineableCellSemantic",
    "MineableSemanticSource",
    "ReconstructionDTO",
    "ReconstructionDiagnosisDTO",
    "ReconstructionResult",
]
