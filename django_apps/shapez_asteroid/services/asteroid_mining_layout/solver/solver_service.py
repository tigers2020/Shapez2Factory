"""Mining layout solver orchestration public entrypoint."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.existing_layout.existing_layout_analysis import (  # noqa: E501
    analyze_existing_layout_from_mining_map,
)
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
    build_final_solver_output,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.p4_reclaim import (
    run_p4_reclaim_stage,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.pass3 import (
    run_pass3_stage,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.pass12 import (
    run_pass12_stage,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.step4 import (
    run_step4_stage,
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
        "trunk_load": {"mode": "accumulate_only", "edges": {}},
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
        replay_events: list[dict[str, Any]] = []
        try:
            map_timeline = build_map_timeline(decoded)
            working_map = map_timeline[0]["mining_map"]
            final_map = map_timeline[-1]["mining_map"]
            is_external = external_predicate_for_mining_map(map_timeline[1]["mining_map"])
            existing_layout_analysis = analyze_existing_layout_from_mining_map(
                working_map,
                is_external=is_external,
            )
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

            pass12 = run_pass12_stage(
                working_map=working_map,
                final_map=final_map,
                is_external=is_external,
                existing_layout_analysis=existing_layout_analysis,
                replay_events=replay_events,
                map_timeline=map_timeline,
                debug_location=_DEBUG_LOC,
            )
            step4 = run_step4_stage(
                map_after_pass2=pass12.map_after_pass2,
                final_map=final_map,
                is_external=is_external,
                placement_records=pass12.placement_records,
                pass12_skipped=pass12.pass12_skipped,
                pass12_replay_txn_id=pass12.pass12_replay_txn_id,
                replay_events=replay_events,
                debug_location=_DEBUG_LOC,
            )
            pass3 = run_pass3_stage(
                map_after_routing=step4.map_after_routing,
                final_map=final_map,
                is_external=is_external,
                pass12_skipped=pass12.pass12_skipped,
                unfinalized_placement_count=step4.unfinalized_placement_count,
                report_step4=step4.report_step4,
                post_step4_counts=step4.post_step4_counts,
                routing_state_summary=step4.routing_state_summary,
                replay_events=replay_events,
                step4_replay_transaction_id=step4.step4_replay_transaction_id,
                debug_location=_DEBUG_LOC,
            )
            p4 = run_p4_reclaim_stage(
                map_after_routing=step4.map_after_routing,
                map_final=pass3.map_final,
                final_map=final_map,
                is_external=is_external,
                existing_layout_analysis=existing_layout_analysis,
                eligible_pass3=pass3.eligible_pass3,
                pass3_summary=pass3.pass3_summary,
                p3_trace=pass3.p3_trace,
                step4_result=step4.step4_result,
                step4_replay_transaction_id=step4.step4_replay_transaction_id,
                replay_events=replay_events,
                routing_state_summary=step4.routing_state_summary,
                debug_location=_DEBUG_LOC,
            )
            out, summary_fields = build_final_solver_output(
                run_id=run_id,
                map_timeline=map_timeline,
                map_after_pass1=pass12.map_after_pass1,
                map_after_pass2=pass12.map_after_pass2,
                map_after_routing=step4.map_after_routing,
                map_final=p4.map_final,
                pass12_status_fields=pass12.pass12_status_fields,
                pass12_stats=pass12.pass12_stats,
                pass12_phase=pass12.pass12_phase,
                pass12_skipped=pass12.pass12_skipped,
                pre_counts=pass12.pre_counts,
                post_pass2_counts=pass12.post_pass2_counts,
                step4_result=step4.step4_result,
                routing_state_summary=step4.routing_state_summary,
                post_step4_counts=step4.post_step4_counts,
                unfinalized_placement_count=step4.unfinalized_placement_count,
                pass3_summary=p4.pass3_summary,
                existing_layout_analysis=existing_layout_analysis,
                step_hash_step4=step4.step_hash_step4,
                step_hash_pass3=pass3.step_hash_pass3,
                step_hash_p4=p4.step_hash_p4,
                solver_state_hash=p4.solver_state_hash,
                replay_events=replay_events,
                debug_location=_DEBUG_LOC,
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
