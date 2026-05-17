"""Sequence 9 — optimization replay track as JSON-safe Lab payload (output-only).

This module does not wire into Django views or templates by itself. Callers that
build Lab page context (e.g. ``django_apps.web.services.asteroid_lab_page_context``)
may merge :func:`merge_optimization_track_into_lab_payload` once an optimization
runner supplies
:class:`~django_apps.shapez_asteroid.optimization.dto.OptimizationReplayFrame`
tuples from
:class:`~django_apps.shapez_asteroid.optimization.optimization_replay.OptimizationReplayRecorder`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, TypedDict, cast

from django_apps.shapez_asteroid.optimization.coords import Coord
from django_apps.shapez_asteroid.optimization.dto import OptimizationReplayFrame
from django_apps.shapez_asteroid.optimization.enums import OptimizationReplayEventType
from django_apps.shapez_asteroid.optimization.optimization_replay import (
    optimization_replay_frame_to_json_dict,
)

TRACK_ID = "optimization"
TRACK_LABEL = "Optimization"

# Lab / API flat field (Option B — smallest change vs existing ``lab_*`` keys).
OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY = "optimization_replay"

# ``django_apps.asteroid_lab.models.SolverRun.config_json`` output-only list of frame dicts
# (same shape as :func:`optimization_replay_frame_to_json_dict`, written by future runners).
SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY = "optimization_replay_frames"

# Read-only UI metadata when persisted ``optimization_replay_frames`` cannot be deserialized.
# Must not affect ordering, solver, or replay semantics (Sequence 12G).
OPTIMIZATION_REPLAY_DIAGNOSTIC_REASON_METRIC_KEY = "optimization_replay_diagnostic_reason"


class OptimizationReplayTrackPayload(TypedDict):
    """v0 track envelope merged under :data:`OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY`."""

    track_id: str
    track_label: str
    frame_count: int
    frames: list[dict[str, Any]]
    metrics: dict[str, Any]


def _event_type_counts_sorted(frames: Sequence[OptimizationReplayFrame]) -> dict[str, int]:
    raw: dict[str, int] = {}
    for f in frames:
        key = f.event_type.value
        raw[key] = raw.get(key, 0) + 1
    return dict(sorted(raw.items()))


def _aggregate_replay_truncated(frames: Sequence[OptimizationReplayFrame]) -> bool:
    return any(bool(f.metrics.get("replay_truncated")) for f in frames)


def _first_truncation_reason_from_frames(
    frames: Sequence[OptimizationReplayFrame],
) -> str | None:
    """First non-empty ``truncation_reason`` on a frame with ``replay_truncated``."""

    for f in frames:
        if not bool(f.metrics.get("replay_truncated")):
            continue
        tr = f.metrics.get("truncation_reason")
        if isinstance(tr, str) and tr.strip():
            return tr.strip()
    return None


def _frame_metrics_truncation_pair_ok(metrics: Mapping[str, Any]) -> bool:
    if not bool(metrics.get("replay_truncated")):
        return True
    tr = metrics.get("truncation_reason")
    return isinstance(tr, str) and bool(tr.strip())


def validate_optimization_replay_frame_list_payload(raw: object) -> bool:
    """Return True if ``raw`` is a list that passes the v0 persisted replay guard.

    * ``raw`` must be a ``list`` (including empty; empty is valid).
    * Non-empty lists must deserialize via
      :func:`deserialize_optimization_replay_frames_from_json` (shape, indices,
      known ``event_type``, metrics dict, truncation pair).
    """

    if not isinstance(raw, list):
        return False
    if len(raw) == 0:
        return True
    return deserialize_optimization_replay_frames_from_json(raw) is not None


def _cell_sequence_from_json(val: object) -> tuple[Any, ...] | None:
    if not isinstance(val, list):
        return None
    out: list[Any] = []
    for item in val:
        if not isinstance(item, dict):
            return None
        try:
            x = int(item["x"])
            y = int(item["y"])
        except (KeyError, TypeError, ValueError):
            return None
        out.append(Coord(x, y))
    return tuple(out)


def deserialize_optimization_replay_frames_from_json(
    raw: object,
) -> tuple[OptimizationReplayFrame, ...] | None:
    """Parse persisted frame dicts into :class:`OptimizationReplayFrame` (read-only UI path).

    Returns ``None`` if ``raw`` is not a non-empty list of well-formed frame objects.
    """

    if not isinstance(raw, list) or len(raw) == 0:
        return None
    frames: list[OptimizationReplayFrame] = []
    for pos, item in enumerate(raw):
        if not isinstance(item, dict):
            return None
        try:
            frame_index = int(item["frame_index"])
            et_raw = item["event_type"]
            title = str(item["title"])
            description = str(item.get("description") or "")
        except (KeyError, TypeError, ValueError):
            return None
        try:
            event_type = OptimizationReplayEventType(str(et_raw))
        except ValueError:
            return None
        vis = _cell_sequence_from_json(item.get("visible_cells", []))
        ovl = _cell_sequence_from_json(item.get("overlay_cells", []))
        if vis is None or ovl is None:
            return None
        metrics_raw = item.get("metrics", {})
        if metrics_raw is None:
            metrics: dict[str, Any] = {}
        elif isinstance(metrics_raw, dict):
            metrics = dict(metrics_raw)
        else:
            return None
        if not _frame_metrics_truncation_pair_ok(metrics):
            return None
        if frame_index != pos:
            return None
        frames.append(
            OptimizationReplayFrame(
                frame_index=frame_index,
                event_type=event_type,
                title=title,
                description=description,
                visible_cells=vis,
                overlay_cells=ovl,
                metrics=metrics,
            )
        )
    return tuple(frames)


def empty_optimization_replay_track_payload() -> dict[str, object]:
    """Empty optimization track (no frames, no truncation)."""

    return {
        "track_id": TRACK_ID,
        "track_label": TRACK_LABEL,
        "frame_count": 0,
        "frames": [],
        "metrics": {
            "frame_count": 0,
            "event_type_counts": {},
            "replay_truncated": False,
        },
    }


def empty_optimization_replay_track_payload_with_diagnostic(reason: str) -> dict[str, object]:
    """Same as :func:`empty_optimization_replay_track_payload` plus a read-only failure reason."""

    base = empty_optimization_replay_track_payload()
    metrics = dict(cast(dict[str, Any], base["metrics"]))
    metrics[OPTIMIZATION_REPLAY_DIAGNOSTIC_REASON_METRIC_KEY] = str(reason)
    return {
        **base,
        "metrics": metrics,
    }


def _diagnose_non_empty_optimization_replay_frame_list(raw: list[object]) -> str:
    """First deserialize failure class (non-empty list only)."""

    for pos, item in enumerate(raw):
        if not isinstance(item, dict):
            return "invalid_optimization_replay_payload"
        try:
            frame_index = int(item["frame_index"])
            et_raw = item["event_type"]
            str(item["title"])
            str(item.get("description") or "")
        except (KeyError, TypeError, ValueError):
            return "invalid_optimization_replay_payload"
        try:
            OptimizationReplayEventType(str(et_raw))
        except ValueError:
            return "unsupported_or_unknown_event_type"
        vis = _cell_sequence_from_json(item.get("visible_cells", []))
        ovl = _cell_sequence_from_json(item.get("overlay_cells", []))
        if vis is None or ovl is None:
            return "invalid_optimization_replay_payload"
        metrics_raw = item.get("metrics", {})
        if metrics_raw is None:
            metrics: dict[str, Any] = {}
        elif isinstance(metrics_raw, dict):
            metrics = dict(metrics_raw)
        else:
            return "invalid_optimization_replay_payload"
        if not _frame_metrics_truncation_pair_ok(metrics):
            return "invalid_truncation_contract"
        if frame_index != pos:
            return "invalid_optimization_replay_payload"
    return "invalid_optimization_replay_payload"


def classify_persisted_optimization_replay_frames_value(raw: object) -> str:
    """Reason string for a stored ``optimization_replay_frames`` value that does not deserialize."""

    if not isinstance(raw, list):
        return "invalid_optimization_replay_payload"
    if len(raw) == 0:
        return "empty_optimization_replay_frames"
    return _diagnose_non_empty_optimization_replay_frame_list(raw)


def diagnostic_reason_after_failed_optimization_replay_scan(
    configs_ordered_newest_first: Sequence[Mapping[str, Any]],
) -> str:
    """Classify read failure from the newest config that sets ``optimization_replay_frames``."""

    key = SOLVER_RUN_CONFIG_OPTIMIZATION_REPLAY_FRAMES_KEY
    for cfg in configs_ordered_newest_first:
        if key in cfg:
            return classify_persisted_optimization_replay_frames_value(cfg[key])
    return "missing_optimization_replay"


def build_optimization_replay_track_payload(
    frames: Sequence[OptimizationReplayFrame],
) -> dict[str, object]:
    """Serialize frames via :func:`optimization_replay_frame_to_json_dict` only (read-only)."""

    if not frames:
        return empty_optimization_replay_track_payload()

    serialized = [optimization_replay_frame_to_json_dict(f) for f in frames]
    truncated = _aggregate_replay_truncated(frames)
    track_metrics: dict[str, Any] = {
        "frame_count": len(serialized),
        "event_type_counts": _event_type_counts_sorted(frames),
        "replay_truncated": truncated,
    }
    if truncated:
        first_reason = _first_truncation_reason_from_frames(frames)
        if first_reason is not None:
            track_metrics["truncation_reason"] = first_reason
        else:
            track_metrics["truncation_reason"] = "unknown"
    return {
        "track_id": TRACK_ID,
        "track_label": TRACK_LABEL,
        "frame_count": len(serialized),
        "frames": serialized,
        "metrics": track_metrics,
    }


def merge_optimization_track_into_lab_payload(
    base_payload: Mapping[str, object],
    frames: Sequence[OptimizationReplayFrame],
) -> dict[str, object]:
    """Shallow-copy ``base_payload`` and attach the optimization track (does not mutate input)."""

    merged: dict[str, object] = dict(base_payload)
    merged[OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY] = build_optimization_replay_track_payload(frames)
    return merged
