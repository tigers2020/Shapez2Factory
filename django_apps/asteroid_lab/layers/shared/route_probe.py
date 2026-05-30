"""Shim: relocated to shapez2_factory.application.asteroid_lab.layers.shared.route_probe."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.shared.route_probe import (
    LAYER03_ROUTE_PROBE_MAX_EXPANDED_NODES,
    LAYER03_ROUTE_PROBE_MAX_PATH_CELLS,
    LAYER03_ROUTE_PROBE_MAX_STEPS,
    immediate_route_probe,
    weighted_route_probe,
)

__all__ = [
    "LAYER03_ROUTE_PROBE_MAX_EXPANDED_NODES",
    "LAYER03_ROUTE_PROBE_MAX_PATH_CELLS",
    "LAYER03_ROUTE_PROBE_MAX_STEPS",
    "immediate_route_probe",
    "weighted_route_probe",
]
