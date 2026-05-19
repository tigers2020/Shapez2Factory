"""Unified step replay DTOs (Phase 9A product contract; output-only artifact)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from django_apps.asteroid_lab.replay.unified_enums import ReplayEventType, ReplayPhase


@dataclass(frozen=True, slots=True)
class ReplayBBox:
    """Inclusive Lab/world bounding box for replay map_view (wire: min_x/max_x/min_y/max_y)."""

    min_x: int
    min_y: int
    max_x: int
    max_y: int


@dataclass(frozen=True, slots=True)
class ReplayCell:
    """Full snapshot cell in ``map_view.full_cells``."""

    x: int
    y: int
    kind: str = ""
    transport: str = ""


@dataclass(frozen=True, slots=True)
class ReplayCellDelta:
    """Materialized cell change in ``map_view.cell_delta``."""

    x: int
    y: int
    kind: str = ""
    transport: str = ""
    op: str = "set"


@dataclass(frozen=True, slots=True)
class ReplayOverlayCell:
    """Highlight / probe path / bundle overlay cell."""

    x: int
    y: int
    kind: str = ""
    transport: str = ""


@dataclass(frozen=True, slots=True)
class ReplayAnnotation:
    """Map annotation (label, reject reason, goal marker)."""

    x: int
    y: int
    label: str = ""


@dataclass(frozen=True, slots=True)
class ReplayMapView:
    """2D-renderable map payload; every unified frame must include one."""

    bbox: ReplayBBox
    base_ref: str | None = None
    full_cells: tuple[ReplayCell, ...] = ()
    cell_delta: tuple[ReplayCellDelta, ...] = ()
    overlay_cells: tuple[ReplayOverlayCell, ...] = ()
    annotations: tuple[ReplayAnnotation, ...] = ()


@dataclass(frozen=True, slots=True)
class UnifiedReplayFrame:
    """Single frame on the product unified replay timeline (never algorithm input)."""

    frame_index: int
    phase: ReplayPhase
    event_type: ReplayEventType
    title: str
    description: str
    map_view: ReplayMapView
    inspector: Mapping[str, Any] = field(default_factory=dict)
    metrics: Mapping[str, Any] = field(default_factory=dict)


def replay_map_view_is_renderable(map_view: ReplayMapView) -> bool:
    """True when the frame is not metadata-only (per unified replay contract)."""

    if map_view.base_ref:
        return True
    return bool(map_view.full_cells or map_view.cell_delta or map_view.overlay_cells)
