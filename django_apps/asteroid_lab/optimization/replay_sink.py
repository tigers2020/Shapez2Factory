"""RTTP replay sink port (output-only; never algorithm input)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol

from django_apps.asteroid_lab.services.dto import SnapshotEventDTO
from django_apps.asteroid_lab.services.replay_recorder import ReplayRecorder


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


@dataclass(slots=True)
class DbRttpReplaySink:
    """Persist RTTP milestone events via ``ReplayRecorder`` (UI artifact only)."""

    track_id: int
    _recorder: ReplayRecorder = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._recorder = ReplayRecorder(int(self.track_id))

    def record(self, event: SnapshotEventDTO) -> Any:
        return self._recorder.record_event(event)


def resolve_replay_sink(sink: RttpReplaySink | None) -> RttpReplaySink:
    if sink is None:
        return NullRttpReplaySink()
    return sink


__all__ = [
    "DbRttpReplaySink",
    "InMemoryRttpReplaySink",
    "NullRttpReplaySink",
    "RttpReplaySink",
    "resolve_replay_sink",
]
