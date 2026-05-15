"""STEP4 routing failure hook: minimum-cost egress corridor opening (MVP)."""

from __future__ import annotations

from ..placement.corridor_opening import (
    step4_corridor_opening_recovery,
)

__all__ = ["step4_corridor_opening_recovery"]
