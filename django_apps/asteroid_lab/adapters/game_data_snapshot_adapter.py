"""Map game_data consumer DTO fields to solver enums (no ``game_data`` import)."""

from __future__ import annotations

from django_apps.asteroid_lab.snapshots.transport_kind import TransportKind

# Observed ``IOType`` / ``io_channel_type`` values from imported game_data (see
# documents/game_data_analysis/building_variants/02_domain_classification.md).
_IO_CHANNEL_TO_TRANSPORT_KIND: dict[str, TransportKind] = {
    "": TransportKind.NONE,
    "Building": TransportKind.NONE,
    "ElevatedBorder": TransportKind.SPACE_BELT,
    "None": TransportKind.NONE,
    "Pipe": TransportKind.SPACE_PIPE,
    "Regular": TransportKind.SPACE_BELT,
    "Wire": TransportKind.NONE,
}


def map_io_channel_to_transport_kind(channel: str) -> TransportKind:
    """Map a game ``io_channel_type`` string to ``TransportKind`` (exhaustive; no default)."""

    try:
        return _IO_CHANNEL_TO_TRANSPORT_KIND[channel]
    except KeyError as exc:
        raise ValueError(f"unknown io_channel_type: {channel!r}") from exc


__all__ = ["map_io_channel_to_transport_kind"]
