"""Frozen EVTC per-connector capacity row (resolver output, not a new literal).

The ``per_connector_capacity_per_min`` carries the value produced by the game_data EVTC resolver
(``space_belt_connector_capacity_per_min_from_row`` / ``space_pipe_max_per_min_from_row``). The core
never recomputes the formula; it only reads the resolver output that the snapshot carries (BA-8).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class ExteriorCapacityRow:
    resource_kind: str
    speed_tier: int
    per_connector_capacity_per_min: Decimal


__all__ = ["ExteriorCapacityRow"]
