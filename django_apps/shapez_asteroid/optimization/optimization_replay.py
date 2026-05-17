"""Output-only optimization replay recording (Sequence 3B / Phase 9 v0).

Replay artifacts are never algorithm input; recording must not affect search results.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from dataclasses import replace
from enum import Enum
from typing import Any, Protocol, cast, runtime_checkable

from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.dto import OptimizationReplayFrame
from django_apps.shapez_asteroid.optimization.enums import OptimizationReplayEventType

MAX_REPLAY_CELLS_PER_FRAME = 128
MAX_REPLAY_FRAMES = 500


@runtime_checkable
class OptimizationReplaySink(Protocol):
    """Protocol for optional replay sinks (real recorder or no-op)."""

    def record_replay_frame(
        self,
        *,
        event_type: OptimizationReplayEventType,
        title: str,
        description: str,
        visible_cells: tuple[object, ...] = (),
        overlay_cells: tuple[object, ...] = (),
        metrics: Mapping[str, object] | None = None,
    ) -> None: ...


class NoOpOptimizationReplayRecorder:
    """Replay disabled: no frames, no side effects beyond no-op calls."""

    @property
    def frames(self) -> tuple[OptimizationReplayFrame, ...]:
        return ()

    @property
    def replay_truncated(self) -> bool:
        return False

    def record_replay_frame(
        self,
        *,
        event_type: OptimizationReplayEventType,
        title: str,
        description: str,
        visible_cells: tuple[object, ...] = (),
        overlay_cells: tuple[object, ...] = (),
        metrics: Mapping[str, object] | None = None,
    ) -> None:
        return


def _truncate_cells(
    visible: tuple[object, ...],
    overlay: tuple[object, ...],
    max_total: int,
) -> tuple[tuple[object, ...], tuple[object, ...], bool]:
    if len(visible) + len(overlay) <= max_total:
        return visible, overlay, False
    if len(visible) >= max_total:
        return visible[:max_total], (), True
    remain = max_total - len(visible)
    return visible, overlay[:remain], True


class OptimizationReplayRecorder:
    """Append-only frame list with v0 caps.

    Does not read algorithm state beyond passed snapshots.
    """

    def __init__(
        self,
        *,
        max_frames: int | None = None,
        max_cells_per_frame: int | None = None,
    ) -> None:
        self._max_frames = max_frames if max_frames is not None else MAX_REPLAY_FRAMES
        self._max_cells = (
            max_cells_per_frame if max_cells_per_frame is not None else MAX_REPLAY_CELLS_PER_FRAME
        )
        self._frames: list[OptimizationReplayFrame] = []
        self._replay_truncated = False

    @property
    def frames(self) -> tuple[OptimizationReplayFrame, ...]:
        return tuple(self._frames)

    @property
    def replay_truncated(self) -> bool:
        return self._replay_truncated

    def _patch_last_metrics(self, **extra: object) -> None:
        if not self._frames:
            return
        last = self._frames[-1]
        merged = dict(last.metrics)
        merged.update(extra)
        self._frames[-1] = replace(last, metrics=merged)

    def record_replay_frame(
        self,
        *,
        event_type: OptimizationReplayEventType,
        title: str,
        description: str,
        visible_cells: tuple[object, ...] = (),
        overlay_cells: tuple[object, ...] = (),
        metrics: Mapping[str, object] | None = None,
    ) -> None:
        if len(self._frames) >= self._max_frames:
            self._replay_truncated = True
            self._patch_last_metrics(replay_truncated=True)
            return

        vis, ovl, cell_trunc = _truncate_cells(visible_cells, overlay_cells, self._max_cells)
        m: dict[str, Any] = dict(metrics or {})
        if cell_trunc:
            m["replay_truncated"] = True
            self._replay_truncated = True

        frame = OptimizationReplayFrame(
            frame_index=len(self._frames),
            event_type=event_type,
            title=title,
            description=description,
            visible_cells=vis,
            overlay_cells=ovl,
            metrics=m,
        )
        self._frames.append(frame)


def _dataclass_fields_to_json_safe(obj: object) -> dict[str, object]:
    """Shallow field walk so nested ``Coord``/enums use the same path as top-level values."""

    return {
        f.name: json_safe_replay_value(getattr(obj, f.name))
        for f in dataclasses.fields(cast(Any, obj))
    }


def json_safe_replay_value(obj: object) -> object:
    """Convert replay-related values to JSON-serializable structures (no algorithm round-trip)."""

    if obj is None or isinstance(obj, (bool, int, float, str)):
        return obj
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, Coord):
        return {"x": obj.x, "y": obj.y}
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return _dataclass_fields_to_json_safe(obj)
    if isinstance(obj, Mapping):
        return {str(k): json_safe_replay_value(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe_replay_value(x) for x in obj]
    if isinstance(obj, (frozenset, set)):
        ordered = sorted(obj, key=lambda z: (type(z).__name__, str(z)))
        return [json_safe_replay_value(x) for x in ordered]
    return str(obj)


def optimization_replay_frame_to_json_dict(frame: OptimizationReplayFrame) -> dict[str, Any]:
    """Serialize a single frame for JSON output (debug/export only)."""

    return {
        "frame_index": frame.frame_index,
        "event_type": frame.event_type.value,
        "title": frame.title,
        "description": frame.description,
        "visible_cells": json_safe_replay_value(frame.visible_cells),
        "overlay_cells": json_safe_replay_value(frame.overlay_cells),
        "metrics": json_safe_replay_value(frame.metrics),
    }


def optimization_replay_frames_to_json_list(
    frames: Sequence[OptimizationReplayFrame],
) -> list[dict[str, Any]]:
    return [optimization_replay_frame_to_json_dict(f) for f in frames]
