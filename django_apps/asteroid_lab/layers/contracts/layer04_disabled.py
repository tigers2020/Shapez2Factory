"""Layer 04 disabled result (superseded by rim greedy L3)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from django_apps.asteroid_lab.layers.contracts.provisional_overlay import ProvisionalLayoutOverlay
from django_apps.asteroid_lab.services.dto import ReplayFrameAppendDTO

LAYER04_DISABLED_REASON = "SUPERSEDED_BY_LAYER_03_RIM_GREEDY_PLACEMENT"


@dataclass(frozen=True, slots=True)
class Layer04DisabledResult:
    status: Literal["DISABLED"]
    reason: str
    provisional_overlay: ProvisionalLayoutOverlay
    replay_frames: tuple[ReplayFrameAppendDTO, ...] = ()

    @classmethod
    def superseded(cls) -> Layer04DisabledResult:
        return cls(
            status="DISABLED",
            reason=LAYER04_DISABLED_REASON,
            provisional_overlay=ProvisionalLayoutOverlay.empty(),
            replay_frames=(),
        )


__all__ = [
    "LAYER04_DISABLED_REASON",
    "Layer04DisabledResult",
]
