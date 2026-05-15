"""Runtime observation: replay rows, trace events, diagnostics.

Algorithm modules (placement, routing, validation, reconstruction) must not take
replay frames or NDJSON as input; migrate call-by-call into this package when splitting
``domain/dto.py`` mixed concerns (Phase 7+).
"""

from .event_builders import runtime_phase_boundary_event
from .logging_helpers import solver_phase_log_extra
from .step_instrumentation import run_instrumented_step
from .trace_collector import TraceCollector
from .trace_events import TraceEvent

__all__ = [
    "TraceEvent",
    "TraceCollector",
    "runtime_phase_boundary_event",
    "run_instrumented_step",
    "solver_phase_log_extra",
]
