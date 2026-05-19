"""In-memory optimization replay recorder for Solver Runtime (PR7)."""

from __future__ import annotations

from typing import Any

from django_apps.asteroid_lab.optimization.enums import OptimizationReplayEventType
from django_apps.asteroid_lab.optimization.replay_frame import (
    MAX_REPLAY_CELLS_PER_FRAME,
    MAX_REPLAY_FRAMES,
    OptimizationReplayFrame,
)


class RuntimeReplayRecorder:
    """Append-only optimization replay frames (output-only)."""

    def __init__(self, *, max_frames: int = MAX_REPLAY_FRAMES) -> None:
        self._max_frames = max(1, int(max_frames))
        self._frames: list[OptimizationReplayFrame] = []
        self._truncated = False
        self._truncation_reason: str | None = None

    @property
    def truncated(self) -> bool:
        return self._truncated

    def append(
        self,
        event_type: OptimizationReplayEventType,
        *,
        title: str,
        description: str = "",
        metrics: dict[str, Any] | None = None,
        visible_cells: tuple[dict[str, Any], ...] = (),
        overlay_cells: tuple[dict[str, Any], ...] = (),
    ) -> None:
        if self._truncated:
            return
        if len(self._frames) >= self._max_frames:
            self._truncated = True
            self._truncation_reason = "max_replay_frames"
            self._append_truncation_marker()
            return

        vis = visible_cells
        ovl = overlay_cells
        if len(vis) + len(ovl) > MAX_REPLAY_CELLS_PER_FRAME:
            vis = vis[:MAX_REPLAY_CELLS_PER_FRAME]
            ovl = ()

        frame_metrics = dict(metrics or {})
        self._frames.append(
            OptimizationReplayFrame(
                frame_index=len(self._frames),
                event_type=event_type,
                title=title,
                description=description,
                visible_cells=vis,
                overlay_cells=ovl,
                metrics=frame_metrics,
            )
        )

    def _append_truncation_marker(self) -> None:
        reason = self._truncation_reason or "max_replay_frames"
        if self._frames:
            last = self._frames[-1]
            metrics = {**dict(last.metrics), "replay_truncated": True, "truncation_reason": reason}
            self._frames[-1] = OptimizationReplayFrame(
                frame_index=last.frame_index,
                event_type=last.event_type,
                title=last.title,
                description=last.description,
                visible_cells=last.visible_cells,
                overlay_cells=last.overlay_cells,
                metrics=metrics,
            )
            return
        self._frames.append(
            OptimizationReplayFrame(
                frame_index=0,
                event_type=OptimizationReplayEventType.VALIDATION_COMPLETED,
                title="Replay truncated",
                description=reason,
                metrics={
                    "replay_truncated": True,
                    "truncation_reason": reason,
                },
            )
        )

    def frames(self) -> tuple[OptimizationReplayFrame, ...]:
        return tuple(self._frames)
