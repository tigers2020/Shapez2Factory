"""Factories for well-formed ``TraceEvent`` rows (delegates validation to ``TraceEvent``)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.trace_events import (
    TraceEvent,
)


def runtime_phase_boundary_event(
    *,
    run_id: str,
    phase: str,
    step_index: int,
    event_type: str,
) -> TraceEvent:
    """Observation-only lifecycle row: not a placement/route commit.

    Uses ``committed=false`` with no commit/reject/rollback reasons, which matches
    current ``validate_trace_decision_semantics`` contracts for non-commit events.
    """

    return TraceEvent(
        run_id=run_id,
        phase=phase,
        step_index=step_index,
        event_type=event_type,
        committed=False,
        commit_reason=None,
        rejected_reason=None,
        rollback_reason=None,
        recovery_trigger=None,
        computation_cycle=None,
        route_level=False,
        transport_kind=None,
    )


__all__ = ["runtime_phase_boundary_event"]
