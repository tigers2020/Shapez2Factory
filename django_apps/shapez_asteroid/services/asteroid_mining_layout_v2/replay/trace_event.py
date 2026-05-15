"""
Trace event schema for NDJSON / UI (§16.3 subset).

Serialization-only in the solver core: no filesystem reads in this module.

When NDJSON rows carry a ``decision`` payload, map its fields to arguments of
``django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.trace_semantics.validate_trace_decision_semantics``
or construct ``runtime.trace_events.TraceEvent`` so the same in-memory rules apply.
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
