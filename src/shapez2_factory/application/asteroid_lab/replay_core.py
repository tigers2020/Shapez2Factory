"""Core replay JSONL emitter for PR-CLI-3b artifacts.

The emitter is intentionally small and streaming-oriented: callers pass an iterable of frame
dictionaries, and each record is written directly to the target text stream as one JSON line.
"""

from __future__ import annotations

import json
from collections.abc import Iterable
from typing import Any, TextIO

REPLAY_CORE_SCHEMA_VERSION = 1


class ReplayCoreFrameOrderError(ValueError):
    """Raised when replay frames are missing or violate monotonic frame order."""


def _frame_index(frame: dict[str, Any]) -> int:
    try:
        raw_value = frame["frame_index"]
    except KeyError as exc:
        raise ReplayCoreFrameOrderError("replay frame is missing frame_index") from exc
    if not isinstance(raw_value, int):
        raise ReplayCoreFrameOrderError(f"frame_index must be int, got {type(raw_value).__name__}")
    return raw_value


def _write_json_line(stream: TextIO, payload: dict[str, Any]) -> None:
    stream.write(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False))
    stream.write("\n")


def write_replay_core_jsonl(
    stream: TextIO,
    frames: Iterable[dict[str, Any]],
    *,
    run_key: str,
) -> None:
    """Write a deterministic replay-core JSONL stream.

    The first line is a header. Every following frame must carry a strictly increasing
    ``frame_index`` so downstream artifact readers can stream without sorting or buffering.
    """

    _write_json_line(
        stream,
        {
            "record_type": "header",
            "schema_version": REPLAY_CORE_SCHEMA_VERSION,
            "run_key": run_key,
        },
    )
    previous_frame_index: int | None = None
    for frame in frames:
        current_frame_index = _frame_index(frame)
        if previous_frame_index is not None and current_frame_index <= previous_frame_index:
            raise ReplayCoreFrameOrderError("replay frame_index values must be strictly increasing")
        previous_frame_index = current_frame_index
        record = dict(frame)
        record.setdefault("record_type", "frame")
        _write_json_line(stream, record)


__all__ = [
    "REPLAY_CORE_SCHEMA_VERSION",
    "ReplayCoreFrameOrderError",
    "write_replay_core_jsonl",
]
