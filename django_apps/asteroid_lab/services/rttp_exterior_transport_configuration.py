"""EVTC configuration errors (missing game_data CANON rows)."""

from __future__ import annotations


class ExteriorTransportCapacityConfigurationError(LookupError):
    """Active exterior transport capacity row missing for the requested tier."""


__all__ = ["ExteriorTransportCapacityConfigurationError"]
