"""Transient-only replay segment frame specs (assembler composes final map_view)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.timeline_dtos import ReplayOverlayCell


@dataclass(frozen=True, slots=True)
class ReplaySegmentFrameSpec:
    event_type: ReplayEventType
    phase: ReplayPhase
    title: str
    description: str
    metrics: dict[str, object]
    transient_overlay_cells: tuple[ReplayOverlayCell, ...] = ()
    inspector: dict[str, Any] = field(default_factory=dict)


__all__ = ["ReplaySegmentFrameSpec"]
