"""Tests for streaming artifact replay JSONL loading."""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

import pytest

from django_apps.asteroid_lab.services.artifact_replay_loader import (
    ArtifactReplayLoadError,
    iter_replay_core_frames,
)


def _write_jsonl(path: Path, records: list[object]) -> None:
    path.write_text(
        "".join(f"{json.dumps(record, sort_keys=True)}\n" for record in records),
        encoding="utf-8",
    )


def test_artifact_replay_loader_returns_iterator(tmp_path: Path) -> None:
    replay_path = tmp_path / "replay_core.jsonl"
    _write_jsonl(
        replay_path,
        [
            {"record_type": "header", "schema_version": 1},
            {"frame_index": 0, "phase": "decode"},
            {"frame_index": 1, "phase": "solve"},
        ],
    )

    frames = iter_replay_core_frames(replay_path)

    assert isinstance(frames, Iterator)
    assert not isinstance(frames, list | tuple)
    assert next(frames) == {"frame_index": 0, "phase": "decode"}
    assert next(frames) == {"frame_index": 1, "phase": "solve"}
    with pytest.raises(StopIteration):
        next(frames)


def test_artifact_replay_loader_rejects_non_object_record(tmp_path: Path) -> None:
    replay_path = tmp_path / "replay_core.jsonl"
    _write_jsonl(replay_path, [{"frame_index": 0}, ["bad"]])

    with pytest.raises(ArtifactReplayLoadError, match="must be object"):
        list(iter_replay_core_frames(replay_path))


def test_artifact_replay_loader_rejects_non_monotonic_frame_index(tmp_path: Path) -> None:
    replay_path = tmp_path / "replay_core.jsonl"
    _write_jsonl(replay_path, [{"frame_index": 0}, {"frame_index": 0}])

    with pytest.raises(ArtifactReplayLoadError, match="must increase"):
        list(iter_replay_core_frames(replay_path))


def test_artifact_replay_loader_rejects_missing_frame_index(tmp_path: Path) -> None:
    replay_path = tmp_path / "replay_core.jsonl"
    _write_jsonl(replay_path, [{"phase": "decode"}])

    with pytest.raises(ArtifactReplayLoadError, match="frame_index must be int"):
        list(iter_replay_core_frames(replay_path))
