"""Mining layout solver orchestration public entrypoint."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    SOLVER_SERVICE_BUILD_SOLVER_TIMELINE_LOCATION,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_transport import (
    run_pass3_transport_minimization_from_maps,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_permission import (
    post_reclaim_pass3_gate as _post_reclaim_pass3_gate,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_timeline import (
    count_layout_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    debug_log_event,
    emit_solver_summary_once,
    trace_run_id_current,
    trace_run_scope,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize import (
    apply_exception_summary_defaults,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.recovery_orchestrator import (  # noqa: E501
    run_solver_timeline_pipeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_trunk_load import (
    build_step4_trunk_load_pipeline_exception_stub,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    external_predicate_for_mining_map,
    validate_final_mining_layout,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import build_map_timeline

_SOLVER_SUMMARY_LOC = SOLVER_SERVICE_BUILD_SOLVER_TIMELINE_LOCATION
_DEBUG_LOC = _SOLVER_SUMMARY_LOC


def _initial_summary_fields(run_id: str) -> dict[str, Any]:
    """예외 경로에서도 emit할 최소 summary field를 만든다."""

    return {
        "run_id": run_id,
        "return_reason": "exception",
        "capacity_mode": "accumulate_only",
        "trunk_load": build_step4_trunk_load_pipeline_exception_stub(),
        "existing_layout_analysis": None,
        "before_return_validate": None,
        "solver_state_hash": None,
        "step_hash_step4": None,
        "step_hash_pass3": None,
        "step_hash_p4": None,
    }


def build_solver_timeline(decoded: dict[str, Any]) -> dict[str, Any]:
    """Run solver pipeline scaffold: map timeline → validation → single ``solver_summary``."""

    with trace_run_scope():
        run_id = trace_run_id_current() or ""
        debug_log_event(_DEBUG_LOC, "pipeline_start", {"run_id": run_id})
        summary_fields = _initial_summary_fields(run_id)
        out: dict[str, Any] = {}
        try:
            map_timeline = build_map_timeline(decoded)
            working_map = map_timeline[0]["mining_map"]
            final_map = map_timeline[-1]["mining_map"]
            debug_log_event(
                _DEBUG_LOC,
                "map_timeline_built",
                {
                    "timeline_frame_count": len(map_timeline),
                    "working_row_count": len(working_map),
                    "final_row_count": len(final_map),
                    "working_counts": count_layout_cells(working_map),
                    "final_counts": count_layout_cells(final_map),
                },
            )
            out, summary_fields = run_solver_timeline_pipeline(
                decoded=decoded,
                debug_location=_DEBUG_LOC,
                run_id=run_id,
            )
        except Exception:
            debug_log_event(
                _DEBUG_LOC,
                "pipeline_exception",
                {"return_reason": "exception"},
                level="error",
            )
            apply_exception_summary_defaults(summary_fields)
            raise
        finally:
            emit_solver_summary_once(_SOLVER_SUMMARY_LOC, summary_fields)
        return out


def external_predicate_for_decoded(decoded: dict[str, Any]) -> Callable[[Coord], bool]:
    """Build ``is_external`` from blueprint mining shell (proxy for placement pipeline)."""

    map_timeline = build_map_timeline(decoded)
    return external_predicate_for_mining_map(map_timeline[1]["mining_map"])


__all__ = [
    "_post_reclaim_pass3_gate",
    "build_solver_timeline",
    "external_predicate_for_decoded",
    "run_pass3_transport_minimization_from_maps",
    "validate_final_mining_layout",
]
