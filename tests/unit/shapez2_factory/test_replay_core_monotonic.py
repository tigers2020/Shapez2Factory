"""PR-CLI-3b Guard B: core replay JSONL frames are monotonic and streaming-friendly."""

from __future__ import annotations

import json
from io import StringIO

import pytest

from shapez2_factory.application.asteroid_lab.replay_core import (
    ReplayCoreFrameOrderError,
    write_replay_core_jsonl,
)


def test_replay_core_writes_header_and_monotonic_frames() -> None:
    stream = StringIO()

    write_replay_core_jsonl(
        stream,
        [
            {"frame_index": 0, "event": "start"},
            {"frame_index": 1, "event": "layer_done", "layer_slug": "layer_01_reconstruction"},
        ],
        run_key="run-1",
    )

    lines = stream.getvalue().splitlines()
    assert len(lines) == 3
    assert json.loads(lines[0]) == {
        "record_type": "header",
        "schema_version": 1,
        "run_key": "run-1",
    }
    assert json.loads(lines[1])["frame_index"] == 0
    assert json.loads(lines[2])["frame_index"] == 1


def test_replay_core_rejects_non_monotonic_frame_index() -> None:
    stream = StringIO()

    with pytest.raises(ReplayCoreFrameOrderError, match="strictly increasing"):
        write_replay_core_jsonl(
            stream,
            [
                {"frame_index": 2, "event": "late"},
                {"frame_index": 2, "event": "duplicate"},
            ],
            run_key="run-1",
        )


def test_replay_core_rejects_missing_frame_index() -> None:
    stream = StringIO()

    with pytest.raises(ReplayCoreFrameOrderError, match="frame_index"):
        write_replay_core_jsonl(stream, [{"event": "missing"}], run_key="run-1")
