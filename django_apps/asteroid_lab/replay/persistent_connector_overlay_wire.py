"""Persistent L2 exterior connector overlay wire rows (replay projection only)."""

from __future__ import annotations

from typing import Literal, TypedDict

ConnectorRoleWire = Literal["required", "spare"]


class PersistentConnectorOverlayWire(TypedDict):
    """One planned exterior connector overlay row derived from exterior_connector_plan wire."""

    x: int
    y: int
    overlay_role: str
    connector_role: ConnectorRoleWire
    tile_type: str
    rotation: int
    connector_id: str


__all__ = [
    "ConnectorRoleWire",
    "PersistentConnectorOverlayWire",
]
