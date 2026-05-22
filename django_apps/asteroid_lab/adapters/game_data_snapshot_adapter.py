"""Map game_data snapshot strings to optimization enums (no Django / ORM)."""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.enums import TransportKind

# Calibrated from ``BuildingConnectorTemplate.io_channel_type`` (game_data import IOType).
_IO_CHANNEL_TO_TRANSPORT: dict[str, TransportKind] = {
    "Shape": TransportKind.SHAPE_BELT,
    "Fluid": TransportKind.FLUID_PIPE,
}


def map_io_channel_to_transport_kind(io_channel_type: str) -> TransportKind:
    """Explicit mapping only — unknown channels fail fast (no default NONE)."""
    key = (io_channel_type or "").strip()
    try:
        return _IO_CHANNEL_TO_TRANSPORT[key]
    except KeyError as exc:
        raise ValueError(f"unknown io_channel_type: {io_channel_type!r}") from exc
