"""Optimization replay UI payload validation and track building (12F v0, PR7)."""

from __future__ import annotations

from collections import Counter
from typing import Any

from django_apps.asteroid_lab.optimization.enums import OptimizationReplayEventType
from django_apps.asteroid_lab.optimization.replay_frame import OptimizationReplayFrame

SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY = "optimization_replay_frames"
SOLVER_RUN_CONFIG_SOLVER_SUMMARY_KEY = "solver_summary"
SOLVER_RUN_CONFIG_SERVER_XY_PARAMS_KEY = "server_xy_params"
SOLVER_RUN_CONFIG_GENE_TEMPLATE_SOURCE_KEY = "gene_template_source"
OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY = "optimization_replay"
OPTIMIZATION_REPLAY_DIAGNOSTIC_REASON_METRIC_KEY = "optimization_replay_diagnostic_reason"

_KNOWN_EVENT_TYPES = frozenset(e.value for e in OptimizationReplayEventType)


def _frame_metrics_pair_ok(metrics: dict[str, Any]) -> bool:
    truncated = metrics.get("replay_truncated") is True
    reason = metrics.get("truncation_reason")
    if not truncated:
        return True
    return isinstance(reason, str) and bool(reason.strip())


def validate_optimization_replay_frame_list_payload(raw: object) -> str | None:
    """Return None if valid; otherwise a short rejection reason."""

    if not isinstance(raw, list):
        return "not_a_list"
    for idx, item in enumerate(raw):
        if not isinstance(item, dict):
            return "frame_not_object"
        if item.get("frame_index") != idx:
            return "frame_index_not_contiguous"
        event_type = item.get("event_type")
        if not isinstance(event_type, str) or event_type not in _KNOWN_EVENT_TYPES:
            return "invalid_event_type"
        metrics = item.get("metrics")
        if metrics is not None and not isinstance(metrics, dict):
            return "metrics_not_object"
        if isinstance(metrics, dict) and not _frame_metrics_pair_ok(metrics):
            return "truncation_pair_invalid"
    return None


def optimization_replay_frames_to_json_list(
    frames: tuple[OptimizationReplayFrame, ...],
) -> list[dict[str, Any]]:
    return [f.to_json_dict() for f in frames]


def frame_from_json_dict(data: dict[str, Any]) -> OptimizationReplayFrame:
    event_raw = str(data.get("event_type") or "")
    event_type = OptimizationReplayEventType(event_raw)
    visible = data.get("visible_cells")
    overlay = data.get("overlay_cells")
    metrics = data.get("metrics")
    return OptimizationReplayFrame(
        frame_index=int(data.get("frame_index", 0)),
        event_type=event_type,
        title=str(data.get("title") or ""),
        description=str(data.get("description") or ""),
        visible_cells=tuple(dict(c) for c in visible) if isinstance(visible, list) else (),
        overlay_cells=tuple(dict(c) for c in overlay) if isinstance(overlay, list) else (),
        metrics=dict(metrics) if isinstance(metrics, dict) else {},
    )


def deserialize_optimization_replay_frames_from_json(
    raw: object,
) -> tuple[OptimizationReplayFrame, ...] | None:
    reason = validate_optimization_replay_frame_list_payload(raw)
    if reason is not None:
        return None
    assert isinstance(raw, list)
    return tuple(frame_from_json_dict(dict(item)) for item in raw)


def deserialize_optimization_replay_frames_lenient(
    raw: object,
) -> tuple[tuple[OptimizationReplayFrame, ...], int]:
    """Lenient read-path deserialize: skip frames with unknown/invalid event_type.

    Returns ``(frames, omitted_count)``.  Valid frames are re-indexed contiguously
    starting at 0.  Frames whose ``event_type`` is not in ``_KNOWN_EVENT_TYPES``,
    or whose shape is malformed, are counted in ``omitted_count`` but never raise.

    The strict ``validate_*`` / ``deserialize_*`` functions remain unchanged for
    the write (persist) path; this function is for the read (replay display) path.
    """
    if not isinstance(raw, list):
        return (), 0
    frames: list[OptimizationReplayFrame] = []
    omitted = 0
    for item in raw:
        if not isinstance(item, dict):
            omitted += 1
            continue
        event_type = item.get("event_type")
        if not isinstance(event_type, str) or event_type not in _KNOWN_EVENT_TYPES:
            omitted += 1
            continue
        metrics = item.get("metrics")
        if metrics is not None and not isinstance(metrics, dict):
            omitted += 1
            continue
        patched = dict(item)
        patched["frame_index"] = len(frames)
        frames.append(frame_from_json_dict(patched))
    return tuple(frames), omitted


def _aggregate_replay_truncated(
    frames: tuple[OptimizationReplayFrame, ...],
) -> tuple[bool, str | None]:
    for frame in frames:
        metrics = frame.metrics
        if metrics.get("replay_truncated") is True:
            reason = metrics.get("truncation_reason")
            if isinstance(reason, str) and reason.strip():
                return True, reason.strip()
            return True, "unknown"
    return False, None


def build_optimization_replay_track_payload(
    frames: tuple[OptimizationReplayFrame, ...],
) -> dict[str, Any]:
    """Read-model track for Lab UI (metadata only)."""

    serialized = optimization_replay_frames_to_json_list(frames)
    counts = Counter(f.event_type.value for f in frames)
    truncated, truncation_reason = _aggregate_replay_truncated(frames)
    metrics: dict[str, Any] = {
        "frame_count": len(frames),
        "event_type_counts": dict(sorted(counts.items())),
        "replay_truncated": truncated,
    }
    if truncated:
        metrics["truncation_reason"] = truncation_reason
    return {
        "frames": serialized,
        "metrics": metrics,
    }


def empty_optimization_replay_track_payload() -> dict[str, Any]:
    return build_optimization_replay_track_payload(())
