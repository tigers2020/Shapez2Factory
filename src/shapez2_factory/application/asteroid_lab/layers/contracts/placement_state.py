"""Placement commit lifecycle states (L4-L6)."""

from __future__ import annotations

from enum import StrEnum


class PlacementCommitState(StrEnum):
    PROVISIONAL_PLACED = "PROVISIONAL_PLACED"
    ROUTED_CONFIRMED = "ROUTED_CONFIRMED"
    QUARANTINED_UNROUTED = "QUARANTINED_UNROUTED"
    ROLLED_BACK = "ROLLED_BACK"


__all__ = ["PlacementCommitState"]
