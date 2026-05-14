"""Typed wire shapes for STEP 0.5 existing-layout analysis."""

from __future__ import annotations

from typing import Literal, TypedDict

type CoordWire = list[int]
type IssueSeverity = Literal["info", "warning", "error"]
type SourceKindWire = Literal[
    "raw_asteroid_field",
    "existing_fluid_layout",
    "existing_shape_layout",
    "mixed_existing_layout",
    "unknown",
]


class ExistingLayoutBBoxWire(TypedDict):
    """JSON bbox object emitted by existing-layout analysis."""

    x_min: int
    x_max: int
    y_min: int
    y_max: int


class ExistingTransportComponentWire(TypedDict, total=False):
    """One connected transport component in wire form."""

    component_id: int
    kind: str
    cells: list[CoordWire]
    cell_count: int
    bbox: ExistingLayoutBBoxWire
    touches_external_margin: bool
    status: str


class ExistingTransportAnalysisWire(TypedDict, total=False):
    """Transport block from ``ExistingLayoutAnalysis``."""

    transport_kind: str
    component_count: int
    main_component_id: int | None
    components: list[ExistingTransportComponentWire]
    orphan_component_ids: list[int]
    single_cell_artifacts: list[CoordWire]
    by_kind: dict[str, ExistingTransportAnalysisWire]


class ExistingEquipmentAnalysisWire(TypedDict, total=False):
    """Equipment summary from existing-layout analysis."""

    miner_count: int
    extension_count: int
    miners_without_adjacent_transport: list[CoordWire]
    miners_attached_to_orphan_transport: list[CoordWire]
    equipment_attachment: list[dict[str, object]]


class ExistingLayoutIssueWire(TypedDict, total=False):
    """One existing-layout issue row."""

    code: str
    severity: IssueSeverity
    coords: list[CoordWire]
    component_ids: list[int]
    message: str


class ExistingLayoutSolverHintsWire(TypedDict, total=False):
    """Solver hint lists derived from existing layout."""

    trunk_seed_cell_union: list[CoordWire]
    cleanup_candidate_cell_union: list[CoordWire]


class ExistingLayoutAnalysisWire(TypedDict, total=False):
    """JSON-friendly STEP 0.5 analysis payload."""

    source_kind: SourceKindWire
    island_bbox: ExistingLayoutBBoxWire | None
    transport: ExistingTransportAnalysisWire
    transport_by_kind: dict[str, ExistingTransportAnalysisWire] | None
    equipment: ExistingEquipmentAnalysisWire
    issues: list[ExistingLayoutIssueWire]
    solver_hints: ExistingLayoutSolverHintsWire


__all__ = [
    "CoordWire",
    "ExistingEquipmentAnalysisWire",
    "ExistingLayoutAnalysisWire",
    "ExistingLayoutBBoxWire",
    "ExistingLayoutIssueWire",
    "ExistingLayoutSolverHintsWire",
    "ExistingTransportAnalysisWire",
    "ExistingTransportComponentWire",
    "IssueSeverity",
    "SourceKindWire",
]
