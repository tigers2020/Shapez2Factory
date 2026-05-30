"""Shim: relocated to core layers.layer_02_exterior_transport.slots."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.slots import (
    VOID_DEPTH_MIN,
    VoidDepthEntry,
    build_candidate_slots_by_edge,
    compute_void_depth_entries,
)

__all__ = [
    "VOID_DEPTH_MIN",
    "VoidDepthEntry",
    "build_candidate_slots_by_edge",
    "compute_void_depth_entries",
]
