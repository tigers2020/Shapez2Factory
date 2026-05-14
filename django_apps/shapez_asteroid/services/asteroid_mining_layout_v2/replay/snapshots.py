"""
Layout snapshots for replay (STEP 10).

``read_ndjson_replay_events`` exists only for **offline tooling / adapters** outside the
solver algorithm path; core placement/routing/validation must not import it.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class LayoutSnapshot:
    """Immutable snapshot payload (expand per §16)."""

    phase: str
    cells: frozenset[tuple[int, int]] = field(default_factory=frozenset)
    meta: dict[str, Any] = field(default_factory=dict)


def read_ndjson_replay_events(_path: str) -> Iterator[dict[str, Any]]:
    """
    NDJSON reader for debug/replay tooling — **not** an algorithm input.

    Solver steps must not call this function (enforced by import-boundary tests).
    """
    msg = "read_ndjson_replay_events is not implemented (skeleton only)"
    raise NotImplementedError(msg)
