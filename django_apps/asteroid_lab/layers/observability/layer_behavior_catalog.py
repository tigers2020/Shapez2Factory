"""Re-export shim: behavior catalog moved to Django-free core (PR-CLI-2d Task D)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.observability.layer_behavior_catalog import (
    LAYER_BEHAVIOR_BY_SLUG,
    format_layer_summary_line,
    layer_behavior_for_slug,
)

__all__ = [
    "LAYER_BEHAVIOR_BY_SLUG",
    "format_layer_summary_line",
    "layer_behavior_for_slug",
]
