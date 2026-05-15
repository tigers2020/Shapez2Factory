"""Phase wrapper: lifecycle ``TraceEvent`` rows + module logger (no global logging setup)."""

from __future__ import annotations

import logging
from collections.abc import Callable

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.event_builders import (
    runtime_phase_boundary_event,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.logging_helpers import (
    solver_phase_log_extra,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.trace_collector import (
    TraceCollector,
)

logger = logging.getLogger(__name__)


def run_instrumented_step[ResultT](
    *,
    phase: str,
    trace: TraceCollector,
    step_index: int,
    fn: Callable[[], ResultT],
) -> ResultT:
    """Emit ``phase_started``, run ``fn``, emit ``phase_finished`` or ``phase_failed``."""

    run_id = trace.run_id
    trace.emit(
        runtime_phase_boundary_event(
            run_id=run_id,
            phase=phase,
            step_index=step_index,
            event_type="phase_started",
        )
    )
    logger.info(
        "solver phase started",
        extra=solver_phase_log_extra(run_id=run_id, phase=phase),
    )
    try:
        result = fn()
    except Exception:
        trace.emit(
            runtime_phase_boundary_event(
                run_id=run_id,
                phase=phase,
                step_index=step_index,
                event_type="phase_failed",
            )
        )
        logger.exception(
            "solver phase failed",
            extra=solver_phase_log_extra(run_id=run_id, phase=phase),
        )
        raise

    trace.emit(
        runtime_phase_boundary_event(
            run_id=run_id,
            phase=phase,
            step_index=step_index,
            event_type="phase_finished",
        )
    )
    logger.info(
        "solver phase finished",
        extra=solver_phase_log_extra(run_id=run_id, phase=phase),
    )
    return result


__all__ = ["run_instrumented_step"]
