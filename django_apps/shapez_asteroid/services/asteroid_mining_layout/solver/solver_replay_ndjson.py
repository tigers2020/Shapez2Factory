"""Parse STEP10 replay NDJSON lines (output-only audit / UI helpers).

Wire shape per ``solver_trace.trace_event``: ``{"location","message","data"}``.
Debug NDJSON uses ``kind: action`` — treat as ``debug_log_invalid`` for replay classification.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

FrameSource = Literal["replay_trace", "pass_snapshot_fallback", "debug_log_invalid", "empty"]


def _is_trace_event_row(obj: dict[str, Any]) -> bool:
    return (
        isinstance(obj.get("location"), str)
        and isinstance(obj.get("message"), str)
        and isinstance(obj.get("data"), dict)
    )


def parse_replay_ndjson_text(text: str) -> dict[str, Any]:
    """Parse NDJSON text; return counts and ``frame_source`` classification."""

    replay_frame_count = 0
    candidate_reject_count = 0
    trace_event_like = 0
    has_computation_cycle = False
    debug_like = 0
    lines = 0
    for raw in text.splitlines():
        s = raw.strip()
        if not s:
            continue
        lines += 1
        try:
            obj = json.loads(s)
        except json.JSONDecodeError:
            continue
        if not isinstance(obj, dict):
            continue
        if obj.get("kind") == "action":
            debug_like += 1
            continue
        if not _is_trace_event_row(obj):
            if "kind" in obj:
                debug_like += 1
            continue
        trace_event_like += 1
        msg = str(obj["message"])
        data = obj["data"]
        if isinstance(data.get("computation_cycle"), int):
            has_computation_cycle = True
        if msg == "replay_frame" or data.get("event_type") == "replay_frame":
            replay_frame_count += 1
        et = data.get("event_type")
        if et == "candidate_reject" or msg in (
            "bundle_reject_invalid_stub",
            "bundle_reject_no_route",
        ):
            candidate_reject_count += 1

    if debug_like and trace_event_like == 0 and replay_frame_count == 0:
        frame_source: FrameSource = "debug_log_invalid"
    elif replay_frame_count > 0:
        frame_source = "replay_trace"
    elif trace_event_like > 0:
        frame_source = "pass_snapshot_fallback"
    elif lines == 0:
        frame_source = "empty"
    else:
        frame_source = "debug_log_invalid"

    fallback_reason: str | None = None
    if frame_source == "pass_snapshot_fallback" and replay_frame_count == 0:
        fallback_reason = "no_replay_frames"

    return {
        "line_count": lines,
        "trace_event_like_count": trace_event_like,
        "replay_frame_count": replay_frame_count,
        "candidate_reject_count": candidate_reject_count,
        "has_computation_cycle": has_computation_cycle,
        "frame_source": frame_source,
        "fallback_reason": fallback_reason,
        "debug_like_count": debug_like,
    }


def parse_replay_ndjson_file(path: Path) -> dict[str, Any]:
    """Read UTF-8 NDJSON file and return :func:`parse_replay_ndjson_text` results."""

    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {
            "line_count": 0,
            "trace_event_like_count": 0,
            "replay_frame_count": 0,
            "candidate_reject_count": 0,
            "has_computation_cycle": False,
            "frame_source": "empty",
            "fallback_reason": None,
            "debug_like_count": 0,
            "read_error": True,
        }
    out = parse_replay_ndjson_text(text)
    out["read_error"] = False
    return out


__all__ = ["parse_replay_ndjson_file", "parse_replay_ndjson_text"]
