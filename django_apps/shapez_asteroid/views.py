from __future__ import annotations

import json
import logging
from typing import Any

from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.utils.translation import gettext as _
from django.views.decorators.http import require_GET, require_POST

from django_apps.shapez_asteroid.services.asteroid_map_cells import (
    list_map_cells_json,
    parse_bbox,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.existing_layout import (
    existing_layout_analysis as existing_layout_analysis_mod,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_corridors import (  # noqa: E501
    protected_corridors_overlay_from_routing_state,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
    final_validation,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import (
    build_map_timeline,
    merge_with_transport_and_final_mining_map,
)
from django_apps.shapez_asteroid.services.copy_preview_debug_dump import (
    dump_copy_preview_debug,
)
from django_apps.shapez_asteroid.services.style_classifier import asteroid_map_style_catalog
from django_apps.shapez_core.services.shapez_copy_decode import decode_shapez2_copy_trace

logger = logging.getLogger(__name__)


def _truthy_query_param(raw: str | None) -> bool:
    if raw is None:
        return False
    v = raw.strip().lower()
    return v in ("1", "true", "yes", "on")


def _merge_p4_pass3_overlay_into_map_timeline(
    map_timeline: list[dict[str, Any]],
    solver_out: dict[str, Any],
) -> None:
    """Merge Pass3 P4 reclaim replay fields from ``build_solver_timeline`` into map summaries."""

    if not map_timeline:
        return
    frames = solver_out.get("solver_timeline") or []
    p3 = next(
        (f for f in frames if isinstance(f, dict) and f.get("id") == "solver_pass3_transport"),
        None,
    )
    if not isinstance(p3, dict):
        return
    summ = p3.get("summary")
    if not isinstance(summ, dict):
        return
    patch: dict[str, Any] = {
        "p4_reclaim_route_zone_excluded_cumulative_count": int(
            summ.get("p4_reclaim_route_zone_excluded_cumulative_count") or 0
        ),
        "p4_reclaim_last_commit_route_cells": summ.get("p4_reclaim_last_commit_route_cells") or [],
        "p4_reclaim_last_soft_protected_candidate_cells": summ.get(
            "p4_reclaim_last_soft_protected_candidate_cells"
        )
        or [],
    }
    for step in map_timeline:
        if not isinstance(step, dict):
            continue
        s = step.setdefault("summary", {})
        if isinstance(s, dict):
            s.update(patch)


def _merge_final_validation_optimization_into_last_map_summary(
    map_timeline: list[dict[str, Any]],
    solver_out: dict[str, Any],
) -> None:
    """Expose counterfactual / quality ratio on the last map step summary for copy-preview UI."""

    if not map_timeline:
        return
    fv = solver_out.get("final_validation")
    if not isinstance(fv, dict):
        return
    last = map_timeline[-1]
    s = last.setdefault("summary", {})
    if not isinstance(s, dict):
        return
    keys = (
        "optimization_final_internal_transport_count",
        "optimization_counterfactual_internal_transport_sequential_v1",
        "optimization_counterfactual_failure_reason",
        "optimization_counterfactual_aggregation",
        "optimization_internal_transport_quality_ratio",
        "optimization_warnings",
        "optimization_warning_count",
        "internal_transport_delta_vs_baseline",
        "original_extractor_count",
        "final_extractor_count",
        "extractor_drop_count",
        "after_preserve_recovery_extractor_count",
        "step4_surviving_extractor_count",
        "step4_routed_extractor_count",
        "preserve_source_loss_before_step4",
        "preserve_source_loss_reason_counts",
        "step4_route_success_on_surviving_placements",
        "step4_complete_routing_success",
        "protected_corridor_hard_by_reason",
        "hard_promotion_without_proof_count",
        "protected_corridor_soft_count",
        "protected_corridor_candidate_count",
        "soft_replace_attempt_count",
        "soft_replace_commit_count",
        "solver_quality_tier",
        "solver_result_tier",
        "solver_quality_summary",
        "solver_quality_subtier",
        "termination",
    )
    for k in keys:
        if k not in fv:
            continue
        val = fv[k]
        if val is None:
            continue
        if k == "optimization_warnings" and not val:
            continue
        if k == "optimization_warning_count" and int(val or 0) == 0:
            continue
        if k == "extractor_drop_count" and int(val or 0) == 0:
            continue
        s[k] = val


# Copy-preview: last map step ``summary`` fields merged from ``solver_summary`` for UI / NDJSON
# parity (display-only; not read by the solver during a run).
_COPY_PREVIEW_SOLVER_SUMMARY_UI_KEYS: tuple[str, ...] = (
    "step4_committed",
    "step4_partial_failure",
    "step4_skipped",
    "pass3_skipped",
    "pass3_skip_reason",
    "pass3_zero_gain_reason",
    "pass3_zero_gain_context",
    "pass2_probe_goal_count",
    "pass2_probe_last_goal_trace",
    "step4_trunk_seed_candidate_zero_reason",
    "all_transport_protected_trace",
    "replay_frame_source",
    "decoded_map_timeline_frame_count",
    "solver_milestone_frame_count",
    "replay_cycle_frame_count",
    "replay_event_count",
    "replay_frame_count",
    "map_timeline_frame_count",
    "solver_timeline_frame_count",
    "p4_reclaim_shadow_skip_reason",
    "post_reclaim_pass3_skip_reason",
    "preserve_quality_score",
    "preserve_quality_score_version",
    "preserve_quality",
    "preserve_missing_stub_summary",
    "step4_no_route_exhausted_breakdown",
    "step4_hard_protected_no_route_breakdown",
    "pass12_stub_route_recovery_enabled",
    "pass12_stub_route_recovery_disabled_by_flag",
    "pass12_stub_route_recovery_eligible_count",
    "pass12_stub_route_recovery_attempted_count",
    "pass12_stub_route_recovery_queue_rounds",
    "transport_connected",
    "final_extractor_count",
    "original_extractor_count",
    "extractor_drop_count",
    "after_preserve_recovery_extractor_count",
    "step4_surviving_extractor_count",
    "step4_routed_extractor_count",
    "preserve_source_loss_before_step4",
    "preserve_source_loss_reason_counts",
    "step4_route_success_on_surviving_placements",
    "step4_complete_routing_success",
    "protected_corridor_hard_by_reason",
    "hard_promotion_without_proof_count",
    "protected_corridor_soft_count",
    "protected_corridor_candidate_count",
    "soft_replace_attempt_count",
    "soft_replace_commit_count",
    "solver_termination",
    "optimization_warnings",
    "optimization_warning_count",
    "solver_quality_tier",
    "solver_result_tier",
    "solver_quality_summary",
    "solver_quality_subtier",
    # ``termination`` (``degradation_causes``, ``quality_tier`` 등) — ``solver_summary``와 동일.
    "termination",
    # map_timeline 길이 vs replay 이벤트 수 혼동 방지 (finalize ``trace_frame_counter_glossary``).
    "trace_frame_counter_glossary",
)


def _merge_solver_summary_ui_fields_into_last_map_summary(
    map_timeline: list[dict[str, Any]],
    solver_out: dict[str, Any],
) -> None:
    """Merge pipeline status from ``solver_summary`` onto the last map step (optimizer UI)."""

    if not map_timeline:
        return
    ss = solver_out.get("solver_summary")
    if not isinstance(ss, dict):
        return
    last = map_timeline[-1]
    s = last.setdefault("summary", {})
    if not isinstance(s, dict):
        return
    for k in _COPY_PREVIEW_SOLVER_SUMMARY_UI_KEYS:
        if k not in ss:
            continue
        s[k] = ss[k]


def _merge_replay_corridor_counts_into_last_map_summary(
    map_timeline: list[dict[str, Any]],
    solver_out: dict[str, Any],
) -> None:
    """Expose protected corridor pool counts on the last map summary (copy-preview UI)."""

    if not map_timeline:
        return
    ss = solver_out.get("solver_summary")
    if not isinstance(ss, dict):
        return
    rs = ss.get("routing_state")
    overlay = protected_corridors_overlay_from_routing_state(rs if isinstance(rs, dict) else None)
    counts = overlay.get("counts")
    if not isinstance(counts, dict):
        return
    last = map_timeline[-1]
    s = last.setdefault("summary", {})
    if isinstance(s, dict):
        s["replay_protected_corridor_counts"] = dict(counts)


def _map_cells_error_code(message: str) -> str:
    return {
        "missing x_min, x_max, y_min, or y_max": "bbox_missing_params",
        "bounds must be integers": "bbox_not_integers",
        "min must be <= max for each axis": "bbox_min_max_order",
        "bbox span too large": "bbox_span_too_large",
        "bbox must not include x=0": "bbox_includes_x_zero",
    }.get(message, "bbox_validation_error")


@require_GET
def health(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


@require_GET
def map_cells(request: HttpRequest) -> JsonResponse:
    err, bbox = parse_bbox(request.GET)
    if err is not None:
        raw = str(err.get("error", ""))
        return JsonResponse(
            {
                "ok": False,
                "error": _(raw),
                "error_code": _map_cells_error_code(raw),
            },
            status=400,
        )
    assert bbox is not None
    x_min, x_max, y_min, y_max = bbox
    return JsonResponse(list_map_cells_json(x_min, x_max, y_min, y_max))


@require_POST
def copy_preview(request: HttpRequest) -> JsonResponse:
    """Return map timeline from ``build_map_timeline`` only.

    Pass ``GET include_solver_overlay=1`` (or ``true``/``yes``/``on``) to merge Pass3 P4
    reclaim overlay fields via ``build_solver_timeline`` (extra solver cost).

    Pass ``GET include_solver_replay=1`` to include ``solver_replay`` (replay contract: frames,
    ``events``, ``computation_cycle``; v3 adds per-event cycle + Pass3 layout snapshots; v12 adds
    ``ui_frames`` and ``cycle_frames`` from ``replay_frame`` rows for STEP10 cycle streaming);
    shares one ``build_solver_timeline`` run with ``include_solver_overlay`` when both are set.

    Count semantics: ``len(map_timeline)`` (here and in debug ``map_timeline_built``) is the small
    **decoded map timeline** step count. ``solver_summary`` also exposes
    ``decoded_map_timeline_frame_count`` (same), ``solver_milestone_frame_count`` (pass milestones),
    ``replay_event_count`` (trace events), ``replay_cycle_frame_count`` (stride-based cycle frames,
    alias ``replay_frame_count``), and ``replay_frame_source`` (which source the replay player
    should prefer). See ``trace_frame_counter_glossary`` — do not compare map step count with trace
    event count or cycle frame count as the same quantity.
    """

    try:
        body = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"ok": False, "error": _("invalid json"), "error_code": "invalid_json"},
            status=400,
        )

    code = body.get("code")
    if not isinstance(code, str):
        return JsonResponse(
            {
                "ok": False,
                "error": _("code must be a string"),
                "error_code": "code_not_string",
            },
            status=400,
        )

    trace = decode_shapez2_copy_trace(code)
    if not trace.success:
        user_error = trace.error or _("decode failed")
        return JsonResponse(
            {
                "ok": False,
                "error": user_error,
                "error_code": "decode_trace_error" if trace.error else "decode_failed",
            },
            status=400,
        )
    decoded = trace.data
    assert decoded is not None

    debug_dir = getattr(settings, "SHAPEZ_COPY_DEBUG_DIR", "") or ""
    if debug_dir:
        dump_copy_preview_debug(code, decoded, debug_dir)

    map_timeline = build_map_timeline(decoded)
    include_solver_overlay = _truthy_query_param(request.GET.get("include_solver_overlay"))
    include_solver_replay = _truthy_query_param(request.GET.get("include_solver_replay"))

    solver_out: dict[str, Any] | None = None
    if include_solver_overlay or include_solver_replay:
        from django_apps.shapez_asteroid.services.asteroid_mining_layout import (
            build_solver_timeline,
        )

        try:
            solver_out = build_solver_timeline(decoded)
        except Exception as exc:
            logger.exception("copy_preview: build_solver_timeline failed")
            return JsonResponse(
                {
                    "ok": False,
                    "error": _("solver timeline failed"),
                    "error_code": "solver_timeline_failed",
                    "detail": str(exc),
                },
                status=500,
            )

    if include_solver_overlay and solver_out is not None:
        _merge_p4_pass3_overlay_into_map_timeline(map_timeline, solver_out)
    if solver_out is not None and (include_solver_overlay or include_solver_replay):
        _merge_final_validation_optimization_into_last_map_summary(map_timeline, solver_out)
        _merge_solver_summary_ui_fields_into_last_map_summary(map_timeline, solver_out)
        _merge_replay_corridor_counts_into_last_map_summary(map_timeline, solver_out)
    fin = map_timeline[-1]
    summary = fin["summary"]
    mining_map = fin["mining_map"]
    transport_map = map_timeline[0]["mining_map"]
    step05_baseline_map = merge_with_transport_and_final_mining_map(transport_map, mining_map)
    is_ext = final_validation.external_predicate_for_mining_map(map_timeline[1]["mining_map"])
    existing_layout_analysis = existing_layout_analysis_mod.analyze_existing_layout_from_mining_map(
        step05_baseline_map,
        is_external=is_ext,
    )
    payload: dict[str, Any] = {
        "ok": True,
        "summary": summary,
        "mining_map": mining_map,
        "map_timeline": map_timeline,
        "style_catalog": asteroid_map_style_catalog(),
        "existing_layout_analysis": existing_layout_analysis,
    }
    if solver_out is not None and (include_solver_overlay or include_solver_replay):
        payload["mining_layout_runtime_flags"] = {
            "shapez_mining_pass12_preserve_stub_route_recovery": bool(
                getattr(settings, "SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY", True)
            ),
            "shapez_mining_pass12_preserve_stub_recovery": bool(
                getattr(settings, "SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY", False)
            ),
        }
    if include_solver_replay and solver_out is not None:
        sr = solver_out.get("solver_replay")
        if isinstance(sr, dict):
            payload["solver_replay"] = sr
    if solver_out is not None and (include_solver_overlay or include_solver_replay):
        st = solver_out.get("solver_timeline")
        if isinstance(st, list):
            payload["solver_timeline"] = st
    return JsonResponse(payload)
