"""In-memory collector for validated ``TraceEvent`` rows (output-side evidence).

No disk read/write; semantics are delegated to ``TraceEvent`` construction only.
"""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.trace_events import (
    TraceEvent,
)


class TraceCollector:
    """Append-only store. Semantics are enforced by ``TraceEvent`` construction only."""

    __slots__ = ("_events", "run_id")

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self._events: list[TraceEvent] = []

    @property
    def events(self) -> tuple[TraceEvent, ...]:
        return tuple(self._events)

    def emit(self, event: TraceEvent) -> None:
        self._events.append(event)

    def has_event(self, event_type: str) -> bool:
        return any(e.event_type == event_type for e in self._events)

    def events_for_phase(self, phase: str) -> tuple[TraceEvent, ...]:
        return tuple(e for e in self._events if e.phase == phase)

    def count(self, event_type: str) -> int:
        return sum(1 for e in self._events if e.event_type == event_type)


__all__ = ["TraceCollector"]
