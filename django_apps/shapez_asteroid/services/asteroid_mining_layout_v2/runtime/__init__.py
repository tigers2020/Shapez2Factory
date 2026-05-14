"""Runtime observation: replay rows, trace events, diagnostics.

Algorithm modules (placement, routing, validation, reconstruction) must not take
replay frames or NDJSON as input; migrate call-by-call into this package when splitting
``domain/dto.py`` mixed concerns (Phase 7+).
"""

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.trace_events import (
    TraceEvent,
)

__all__ = ["TraceEvent"]
