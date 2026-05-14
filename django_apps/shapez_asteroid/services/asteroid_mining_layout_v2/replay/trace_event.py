"""
Trace event schema for NDJSON / UI (§16.3 subset).

Serialization-only in the solver core: no filesystem reads in this module.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class TraceEvent:
    """One replay/trace row (mutable for adapter population)."""

    run_id: str
    phase: str
    step_index: int
    event_type: str
    data: dict[str, Any] = field(default_factory=dict)
