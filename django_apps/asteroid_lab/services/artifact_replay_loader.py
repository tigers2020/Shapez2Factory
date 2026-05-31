"""Streaming loader for artifact ``replay_core.jsonl`` files."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path
from typing import Any


class ArtifactReplayLoadError(Exception):
    """Raised when an artifact replay JSONL stream is malformed."""


def iter_replay_core_frames(path: Path) -> Iterator[dict[str, Any]]:
    """Yield replay frame records line-by-line without materializing the JSONL file."""

    previous_frame_index: int | None = None
    with Path(path).open("r", encoding="utf-8") as stream:
        for line_number, raw_line in enumerate(stream, start=1):
            line = raw_line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                raise ArtifactReplayLoadError(
                    f"invalid replay_core JSON at line {line_number}"
                ) from exc
            if not isinstance(record, dict):
                raise ArtifactReplayLoadError(
                    f"replay_core record must be object at line {line_number}"
                )
            if record.get("record_type") == "header":
                continue
            frame_index = record.get("frame_index")
            if not isinstance(frame_index, int):
                raise ArtifactReplayLoadError(
                    f"replay_core frame_index must be int at line {line_number}"
                )
            if previous_frame_index is not None and frame_index <= previous_frame_index:
                raise ArtifactReplayLoadError("replay_core frame_index must increase")
            previous_frame_index = frame_index
            yield dict(record)


__all__ = ["ArtifactReplayLoadError", "iter_replay_core_frames"]
