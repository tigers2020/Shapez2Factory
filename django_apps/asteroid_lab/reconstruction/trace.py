"""Output-only reconstruction trace (never algorithm input)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django_apps.asteroid_lab.reconstruction.grid import Coord


@dataclass(frozen=True, slots=True)
class ReconstructionTraceEvent:
    """One logical trace step for replay assembly."""

    phase: str
    trace_event_type: str
    coords: frozenset[Coord]
    summary_json: dict[str, Any]


class ReconstructionTraceCollector:
    """Append-only collector; optional on ``reconstruct_after_cleanup``."""

    __slots__ = ("_events",)

    def __init__(self) -> None:
        self._events: list[ReconstructionTraceEvent] = []

    def append(self, event: ReconstructionTraceEvent) -> None:
        self._events.append(event)

    @property
    def events(self) -> tuple[ReconstructionTraceEvent, ...]:
        return tuple(self._events)
