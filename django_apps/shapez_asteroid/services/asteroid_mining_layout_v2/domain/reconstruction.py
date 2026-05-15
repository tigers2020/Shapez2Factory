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
    "asteroid_field_inferred",
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
    extension footprint, minus **layout** obstacles (belt, pipe, platform, other solid
    layout kinds) that are not mineable placement targets. ``extractor_cells`` /
    ``extension_cells`` keep blueprint snapshots; ``equipment_footprint_mineable_cells``
    is their sorted union (prior mineable evidence). ``full_barrier_cells`` remains the
    union of all occupied blueprint coordinates (not equivalent to
    ``transport_and_solid_blocker_cells`` alone).

    ``interior_patch_cells`` are included in the same formal asteroid field as mineable
    placement targets; they are not ``RouteZone.INTERNAL_VOID`` / off-map void for later passes.

    ``mineable_cell_semantics`` has exactly one row per ``mineable_placement_cell`` when
    produced by ``reconstruct_asteroid_mining_field``; later passes should prefer this over
    map labels for shape vs fluid. Inferred interior mineable uses ``asteroid_field_inferred``
    (same field-body role as preview ``mineable`` + ``asteroid_field`` promotion).

    **Void topology (STEP 1, Pass1 gating)**: ``external_void_cells`` classifies empty
    lattice sites inside ``asteroid_bbox ± external_margin`` reachable from the rectangle
    border without crossing ``mineable_placement_cells`` or ``void_flood_blocker_cells``
    (platform/other solids only; belt/pipe do **not** block void flood, matching the
    transport-stripped hull used for interior inference). **Single Pass1 rim (no
    separate “inferred interior rim”)**: ``outer_rim_mineable_cells`` — every mineable
    cell (shell **or** inferred interior patch) that is 4-adjacent to that **one**
    exterior void flood; fully enclosed void pockets adjacent only to mineable do not
    count as exterior, so their touching mineable cells are excluded (annulus rule).

    ``transport_and_solid_blocker_cells`` is belt ∪ pipe ∪ platform ∪ other: **current
    blueprint layout** cells excluded from **mineable membership** (not an immutable
    “permanent” map; hull/interior already strips belt/pipe for closure, and later edits
    could change mineability). The same belt/pipe coordinates **remain** in
    ``belt_cells`` / ``pipe_cells`` and in ``full_barrier_cells`` for occupancy / overlays.
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
    transport_and_solid_blocker_cells: tuple[BlueprintCell, ...] = ()
    void_flood_blocker_cells: tuple[BlueprintCell, ...] = ()
    external_void_cells: tuple[BlueprintCell, ...] = ()
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
