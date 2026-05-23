"""Test contract for RTTP Section B — production is source of truth for event set."""

from __future__ import annotations

from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    RTTP_MILESTONE_EVENT_TYPES,
)

FORBIDDEN_MILESTONE_MAP_KEYS: frozenset[str] = frozenset(
    {"map_view", "full_map", "cell_overlay_json"}
)

__all__ = ["FORBIDDEN_MILESTONE_MAP_KEYS", "RTTP_MILESTONE_EVENT_TYPES"]
