"""RTTP replay sink port (output-only; never algorithm input)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from django_apps.asteroid_lab.services.dto import SnapshotEventDTO


class RttpReplaySink(Protocol):
    def record(self, event: SnapshotEventDTO) -> Any: ...


class NullRttpReplaySink:
    def record(self, event: SnapshotEventDTO) -> None:
        del event
        return None


@dataclass
class InMemoryRttpReplaySink:
    events: list[SnapshotEventDTO] = field(default_factory=list)

    def record(self, event: SnapshotEventDTO) -> None:
        self.events.append(event)
        return None


def resolve_replay_sink(sink: RttpReplaySink | None) -> RttpReplaySink:
    if sink is None:
        return NullRttpReplaySink()
    return sink


__all__ = [
    "InMemoryRttpReplaySink",
    "NullRttpReplaySink",
    "RttpReplaySink",
    "resolve_replay_sink",
]
