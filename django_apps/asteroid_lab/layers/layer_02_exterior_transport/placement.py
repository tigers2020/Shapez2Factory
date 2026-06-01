"""Shim: relocated to core layers.layer_02_exterior_transport.placement."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.placement import (
    InsufficientConnectorSlotsError,
    NoConnectorSlotsError,
    choose_even_slots,
    choose_spare_slots,
    distribute_connector_counts,
    even_slot_index,
    nearest_unused_index,
    remaining_slots_after_selection,
)

__all__ = [
    "InsufficientConnectorSlotsError",
    "NoConnectorSlotsError",
    "choose_even_slots",
    "choose_spare_slots",
    "distribute_connector_counts",
    "even_slot_index",
    "nearest_unused_index",
    "remaining_slots_after_selection",
]
