"""STEP 0.5 existing-layout analysis DTOs (§E) — pure domain; no I/O, Django, preview."""

from __future__ import annotations

from dataclasses import dataclass

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BBox,
    Coord,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    EquipmentKind,
    ExistingLayoutIssueCode,
    ExistingLayoutIssueSeverity,
    SourceKind,
    TransportComponentStatus,
    TransportKind,
)


@dataclass(frozen=True, slots=True)
class TransportComponentSummary:
    """One same-kind 4-neighbor transport component (§E.5)."""

    component_id: int
    kind: TransportKind
    cells: frozenset[Coord]
    cell_count: int
    bbox: BBox
    touches_external_margin: bool
    status: TransportComponentStatus


@dataclass(frozen=True, slots=True)
class ExistingTransportAnalysis:
    """Per-``TransportKind`` geometric components (§E.4); belt and pipe stay separate."""

    transport_kind: TransportKind
    component_count: int
    main_component_id: int | None
    components: tuple[TransportComponentSummary, ...]
    orphan_component_ids: tuple[int, ...]
    single_cell_artifacts: tuple[Coord, ...]


@dataclass(frozen=True, slots=True)
class EquipmentTransportAttachment:
    """Equipment cell ↔ adjacent transport (§E.7)."""

    equipment_coord: Coord
    equipment_kind: EquipmentKind
    adjacent_transport_coords: tuple[Coord, ...]
    adjacent_component_ids: tuple[int, ...]
    attached_to_main_component: bool


@dataclass(frozen=True, slots=True)
class ExistingEquipmentAnalysis:
    """Extractor/extension adjacency summary (§E.6)."""

    miner_count: int
    extension_count: int
    miners_without_adjacent_transport: tuple[Coord, ...]
    miners_attached_to_orphan_transport: tuple[Coord, ...]
    equipment_attachment: tuple[EquipmentTransportAttachment, ...]


@dataclass(frozen=True, slots=True)
class ExistingLayoutIssue:
    """STEP 0.5 issue row (§E.8); not interchangeable with STEP 9 validation rows."""

    code: ExistingLayoutIssueCode
    severity: ExistingLayoutIssueSeverity
    coords: tuple[Coord, ...]
    component_ids: tuple[int, ...]
    message: str


@dataclass(frozen=True, slots=True)
class ExistingLayoutSolverHints:
    """Derived trunk seed / cleanup unions (§E.9); does not imply hard-protected corridors."""

    trunk_seed_cell_union: frozenset[Coord]
    cleanup_candidate_cell_union: frozenset[Coord]


@dataclass(frozen=True, slots=True)
class ExistingLayoutAnalysis:
    """STEP 0.5 read-only context (§E).

    Never substitutes ``reconstruction.mineable_placement_cells``.
    """

    source_kind: SourceKind
    island_bbox: BBox
    belt_transport: ExistingTransportAnalysis
    pipe_transport: ExistingTransportAnalysis
    equipment: ExistingEquipmentAnalysis
    issues: tuple[ExistingLayoutIssue, ...]
    solver_hints: ExistingLayoutSolverHints


@dataclass(frozen=True, slots=True)
class DecodedExistingLayoutContext:
    """Wrapper for decoded-island analysis (§E.10)."""

    analysis: ExistingLayoutAnalysis


__all__ = [
    "DecodedExistingLayoutContext",
    "EquipmentTransportAttachment",
    "ExistingEquipmentAnalysis",
    "ExistingLayoutAnalysis",
    "ExistingLayoutIssue",
    "ExistingLayoutSolverHints",
    "ExistingTransportAnalysis",
    "TransportComponentSummary",
]
