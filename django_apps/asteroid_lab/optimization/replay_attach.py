"""Optimization replay attach outcome (12E observability; output-only)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class OptimizationReplayAttachReason(StrEnum):
    """POST / log vocabulary for optimization replay persist (write path)."""

    ATTACHED = "attached"
    EMPTY_FRAMES = "empty_frames"
    INVALID_REPLAY_PAYLOAD = "invalid_replay_payload"


@dataclass(frozen=True, slots=True)
class OptimizationReplayAttachResult:
    """Outcome of attaching optimization replay frames to ``SolverRun.config_json``."""

    attached: bool
    reason: OptimizationReplayAttachReason
    diagnostic: str | None = None

    def to_json_dict(self) -> dict[str, object]:
        out: dict[str, object] = {
            "attached": self.attached,
            "reason": self.reason.value,
        }
        if self.diagnostic is not None:
            out["diagnostic"] = self.diagnostic
        return out


__all__ = [
    "OptimizationReplayAttachReason",
    "OptimizationReplayAttachResult",
]
