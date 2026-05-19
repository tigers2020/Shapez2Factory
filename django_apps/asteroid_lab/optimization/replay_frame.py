"""Optimization replay frame DTO (output-only, PR7)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from django_apps.asteroid_lab.optimization.enums import OptimizationReplayEventType
from django_apps.asteroid_lab.replay.replay_limits import (
    MAX_OPTIMIZATION_REPLAY_CELLS_PER_FRAME,
    MAX_OPTIMIZATION_REPLAY_FRAMES,
)

MAX_REPLAY_FRAMES = MAX_OPTIMIZATION_REPLAY_FRAMES
MAX_REPLAY_CELLS_PER_FRAME = MAX_OPTIMIZATION_REPLAY_CELLS_PER_FRAME


@dataclass(frozen=True, slots=True)
class OptimizationReplayFrame:
    """Single optimization replay observation frame (never algorithm input)."""

    frame_index: int
    event_type: OptimizationReplayEventType
    title: str
    description: str
    visible_cells: tuple[dict[str, Any], ...] = ()
    overlay_cells: tuple[dict[str, Any], ...] = ()
    metrics: dict[str, Any] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "frame_index": int(self.frame_index),
            "event_type": self.event_type.value,
            "title": str(self.title),
            "description": str(self.description),
            "visible_cells": [dict(c) for c in self.visible_cells],
            "overlay_cells": [dict(c) for c in self.overlay_cells],
            "metrics": dict(self.metrics),
        }
