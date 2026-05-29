"""Layer 03 rim bundle scan runtime replay segment (projection only)."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.layer03_observability import Layer03Observability
from django_apps.asteroid_lab.layers.contracts.layer_slugs import LAYER_03_RIM_MINING_BUNDLES
from django_apps.asteroid_lab.replay.event_types import assert_registered_event_type
from django_apps.asteroid_lab.replay.layer03_overlay_cells import (
    OVERLAY_KIND_CANDIDATE_MINER,
    OVERLAY_KIND_CANDIDATE_ROUTE_PATH,
    OVERLAY_KIND_CANDIDATE_TRANSPORT_STUB,
    overlay_for_probed,
)
from django_apps.asteroid_lab.replay.layer03_pool_windowing import (
    PoolProbeWindowPlan,
    build_pool_probe_window_plans,
)
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType, ReplayPhase
from django_apps.asteroid_lab.replay.timeline_dtos import (
    ReplayMapView,
    ReplayOverlayCell,
    ReplayTimelineFrame,
    replay_map_view_is_renderable,
)
from django_apps.asteroid_lab.replay.timeline_serialization import (
    replay_map_view_from_json_dict,
    replay_map_view_to_json_dict,
)

LAYER03_PHASE = LAYER_03_RIM_MINING_BUNDLES
LAYER03_INSPECTOR_STEP = LAYER_03_RIM_MINING_BUNDLES


def _copy_map_view(base_map_view: ReplayMapView) -> ReplayMapView:
    return replay_map_view_from_json_dict(replay_map_view_to_json_dict(base_map_view))


def _timeline_frame(
    *,
    base_map_view: ReplayMapView,
    event_type: ReplayEventType,
    title: str,
    description: str,
    metrics: dict[str, object],
    overlay_cells: tuple[ReplayOverlayCell, ...] = (),
) -> ReplayTimelineFrame:
    assert_registered_event_type(event_type.value)
    copied = _copy_map_view(base_map_view)
    map_view = ReplayMapView(
        bbox=copied.bbox,
        base_ref=copied.base_ref,
        full_cells=copied.full_cells,
        cell_delta=copied.cell_delta,
        overlay_cells=overlay_cells,
        annotations=copied.annotations,
    )
    if not replay_map_view_is_renderable(map_view):
        msg = "layer03 segment frame must be renderable"
        raise ValueError(msg)
    return ReplayTimelineFrame(
        frame_index=0,
        phase=ReplayPhase.CANDIDATE_GENERATION,
        event_type=event_type,
        title=title,
        description=description,
        map_view=map_view,
        inspector={
            "lab_phase": "candidate_generation",
            "lab_phase_step": LAYER03_INSPECTOR_STEP,
            "lab_event_type": event_type.value,
        },
        metrics=metrics,
    )


def _complete_metrics(observability: Layer03Observability) -> dict[str, object]:
    return {
        "layer": LAYER03_PHASE,
        "layer03_skip_reason": observability.skip_reason.value,
        "rim_anchor_count": observability.rim_anchor_count,
        "route_probe_attempt_count": observability.route_probe_attempt_count,
        "route_probe_succeeded_count": observability.route_probe_succeeded_count,
        "normal_candidate_count": observability.normal_candidate_count,
        "diagnostic_rejected_count": observability.diagnostic_rejected_count,
        "reject_reason_counts": list(observability.reject_reason_counts),
    }


def _pool_summary_metrics(
    observability: Layer03Observability,
    plans: tuple[PoolProbeWindowPlan, ...],
) -> dict[str, object]:
    shown_ids = tuple(cid for plan in plans for cid in plan.candidate_ids)
    expected_ids = tuple(
        entry.candidate.candidate_id for entry in observability.replay_pool_candidates
    )
    logical_window_count = plans[0].logical_window_count if plans else 0
    return {
        "layer": LAYER03_PHASE,
        "normal_candidate_count": observability.normal_candidate_count,
        "route_probe_succeeded_count": observability.route_probe_succeeded_count,
        "logical_window_count": logical_window_count,
        "physical_probe_window_frame_count": len(plans),
        "shows_all_candidates": shown_ids == expected_ids,
        "pool_preview_overlay_mode": "candidate_observation",
        "cell_budget_subsplit_count": max(0, len(plans) - logical_window_count),
    }


def _probe_window_metrics(
    observability: Layer03Observability,
    plan: PoolProbeWindowPlan,
) -> dict[str, object]:
    return {
        "layer": LAYER03_PHASE,
        "probe_succeeded_count": observability.route_probe_succeeded_count,
        "normal_candidate_count": observability.normal_candidate_count,
        "logical_window_index": plan.logical_window_index,
        "logical_window_count": plan.logical_window_count,
        "physical_subwindow_index": plan.physical_subwindow_index,
        "physical_subwindow_count": plan.physical_subwindow_count,
        "candidate_start_index": plan.candidate_start_index,
        "candidate_end_index": plan.candidate_end_index,
        "chunk_size": plan.chunk_size,
        "candidate_ids": list(plan.candidate_ids),
        "candidate_count_in_window": len(plan.candidates),
        "shows_all_candidates": True,
    }


def _overlay_for_plan(plan: PoolProbeWindowPlan) -> tuple[ReplayOverlayCell, ...]:
    cells: list[ReplayOverlayCell] = []
    for entry in plan.candidates:
        cells.extend(overlay_for_probed(entry))
    return tuple(cells)


def build_layer03_runtime_segment_frames(
    *,
    observability: Layer03Observability,
    base_map_view: ReplayMapView,
) -> tuple[ReplayTimelineFrame, ...]:
    """Build L3 runtime segment; ``base_map_view`` is assembler-owned structural base only."""

    begin = _timeline_frame(
        base_map_view=base_map_view,
        event_type=ReplayEventType.LAYER03_RIM_BUNDLE_SCAN_BEGIN,
        title="Layer 03 rim bundle scan begin",
        description="Layer 03 rim mining bundle candidate expansion",
        metrics={"layer": LAYER03_PHASE},
    )
    complete = _timeline_frame(
        base_map_view=base_map_view,
        event_type=ReplayEventType.LAYER03_RIM_BUNDLE_SCAN_COMPLETE,
        title="Layer 03 rim bundle scan complete",
        description=(
            f"Normal pool {observability.normal_candidate_count}; "
            f"skip={observability.skip_reason.value}"
        ),
        metrics=_complete_metrics(observability),
    )

    plans = build_pool_probe_window_plans(
        replay_pool_candidates=observability.replay_pool_candidates,
    )
    logical_count = plans[0].logical_window_count if plans else 0
    summary = _timeline_frame(
        base_map_view=base_map_view,
        event_type=ReplayEventType.LAYER03_RIM_BUNDLE_POOL_SUMMARY,
        title="Layer 03 rim bundle pool summary",
        description=(
            f"Replay pool {observability.normal_candidate_count} candidate(s) · "
            f"{logical_count} logical window(s) · {len(plans)} preview frame(s)"
        ),
        metrics=_pool_summary_metrics(observability, plans),
        overlay_cells=(),
    )

    probe_windows: list[ReplayTimelineFrame] = []
    for plan in plans:
        title = (
            f"Layer 03 rim bundle pool · window {plan.logical_window_index} / "
            f"{plan.logical_window_count}"
        )
        description = (
            f"Probe succeeded candidates {plan.candidate_start_index}–"
            f"{plan.candidate_end_index} / {observability.normal_candidate_count}"
        )
        if plan.physical_subwindow_count > 1:
            description += (
                f" · part {plan.physical_subwindow_index}/" f"{plan.physical_subwindow_count}"
            )
        probe_windows.append(
            _timeline_frame(
                base_map_view=base_map_view,
                event_type=ReplayEventType.LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW,
                title=title,
                description=description,
                metrics=_probe_window_metrics(observability, plan),
                overlay_cells=_overlay_for_plan(plan),
            )
        )

    return (begin, complete, summary, *probe_windows)


__all__ = [
    "LAYER03_INSPECTOR_STEP",
    "LAYER03_PHASE",
    "OVERLAY_KIND_CANDIDATE_MINER",
    "OVERLAY_KIND_CANDIDATE_ROUTE_PATH",
    "OVERLAY_KIND_CANDIDATE_TRANSPORT_STUB",
    "build_layer03_runtime_segment_frames",
]
