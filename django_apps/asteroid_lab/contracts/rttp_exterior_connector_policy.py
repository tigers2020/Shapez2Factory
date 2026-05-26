"""EVTC exterior connector count policy."""

from __future__ import annotations

from enum import StrEnum


class ConnectorCountPolicy(StrEnum):
    SATURATED_TRANSPORT = "saturated_transport"


__all__ = ["ConnectorCountPolicy"]
