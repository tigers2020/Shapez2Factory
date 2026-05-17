"""Strict JSON contract for optimization **replay-track** golden fixtures (test-only).

``schema_version`` 1 (v0) matches files under ``tests/fixtures/shapez_asteroid/replay/``
and long-stitch files under ``tests/fixtures/shapez_asteroid/replay_long/``.
Validates envelope + frame shape + ``replay_event_sequence`` consistency with frames.
Optional ``truncation_reason`` (top-level) pairs with ``replay_summary.replay_truncated``.
Does **not** deserialize into domain ``OptimizationReplayFrame`` objects and is **not**
production Lab/runtime wiring.
"""

from __future__ import annotations

import copy
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

CURRENT_REPLAY_FIXTURE_SCHEMA_VERSION: int = 1

_ALLOWED_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
    {
        "schema_version",
        "replay_fixture_id",
        "replay_frames",
        "replay_summary",
        "replay_event_sequence",
        "truncation_reason",
        "metadata",
    }
)

_REQUIRED_TOP_LEVEL_KEYS: frozenset[str] = frozenset(
    {
        "schema_version",
        "replay_fixture_id",
        "replay_frames",
        "replay_summary",
        "replay_event_sequence",
    }
)

_REQUIRED_REPLAY_SUMMARY_KEYS: frozenset[str] = frozenset(
    {
        "frame_count",
        "event_type_counts",
        "replay_truncated",
    }
)

_FRAME_KEYS: frozenset[str] = frozenset(
    {
        "frame_index",
        "event_type",
        "title",
        "description",
        "visible_cells",
        "overlay_cells",
        "metrics",
    }
)


class ReplayFixtureJsonError(ValueError):
    """Golden replay-track fixture JSON violated the versioned contract."""


@dataclass(frozen=True)
class ReplayFixtureJson:
    """Parsed v0 replay-track fixture (JSON-safe tree)."""

    schema_version: int
    replay_fixture_id: str
    replay_frames: Sequence[Mapping[str, object]]
    replay_summary: Mapping[str, object]
    replay_event_sequence: Sequence[str]
    truncation_reason: str | None
    metadata: Mapping[str, object] | None


def load_replay_fixture_json(path: Path) -> ReplayFixtureJson:
    if not path.is_file():
        msg = f"fixture path is not a file: {path}"
        raise ReplayFixtureJsonError(msg)
    raw = json.loads(path.read_text(encoding="utf-8"))
    return parse_replay_fixture_json(raw)


def _require_schema_version(schema_raw: object) -> int:
    if type(schema_raw) is not int:
        msg = f"schema_version must be int, got {type(schema_raw).__name__}"
        raise ReplayFixtureJsonError(msg)
    if schema_raw != CURRENT_REPLAY_FIXTURE_SCHEMA_VERSION:
        msg = (
            f"unsupported schema_version {schema_raw!r}; "
            f"only {CURRENT_REPLAY_FIXTURE_SCHEMA_VERSION} is accepted"
        )
        raise ReplayFixtureJsonError(msg)
    return schema_raw


def _validate_top_level(data: dict[str, object]) -> None:
    keys = frozenset(data)
    unknown = keys - _ALLOWED_TOP_LEVEL_KEYS
    if unknown:
        msg = f"unknown top-level keys (policy: reject): {sorted(unknown)}"
        raise ReplayFixtureJsonError(msg)
    missing = _REQUIRED_TOP_LEVEL_KEYS - keys
    if missing:
        msg = f"missing required top-level keys: {sorted(missing)}"
        raise ReplayFixtureJsonError(msg)


def _event_type_counts_from_sequence(events: Sequence[str]) -> dict[str, int]:
    raw: dict[str, int] = {}
    for e in events:
        raw[e] = raw.get(e, 0) + 1
    return dict(sorted(raw.items()))


def _validate_truncation_reason_field(
    data: dict[str, object], *, replay_truncated: bool
) -> str | None:
    has_key = "truncation_reason" in data
    raw = data.get("truncation_reason")
    if not replay_truncated:
        if not has_key:
            return None
        msg = "truncation_reason must be absent when replay_summary.replay_truncated is false"
        raise ReplayFixtureJsonError(msg)
    if not has_key or raw is None:
        msg = "truncation_reason is required when replay_summary.replay_truncated is true"
        raise ReplayFixtureJsonError(msg)
    if not isinstance(raw, str) or not raw.strip():
        msg = f"truncation_reason must be a non-empty string, got {raw!r}"
        raise ReplayFixtureJsonError(msg)
    return raw.strip()


def _validate_replay_summary(summary: object, *, frame_count: int, events: Sequence[str]) -> bool:
    if not isinstance(summary, dict):
        msg = f"replay_summary must be object, got {type(summary).__name__}"
        raise ReplayFixtureJsonError(msg)
    sk = frozenset(summary)
    if _REQUIRED_REPLAY_SUMMARY_KEYS - sk:
        msg = f"replay_summary missing keys: {sorted(_REQUIRED_REPLAY_SUMMARY_KEYS - sk)}"
        raise ReplayFixtureJsonError(msg)
    extra = sk - _REQUIRED_REPLAY_SUMMARY_KEYS
    if extra:
        msg = f"replay_summary has unknown keys (policy: reject): {sorted(extra)}"
        raise ReplayFixtureJsonError(msg)

    fc = summary["frame_count"]
    if type(fc) is not int or fc != frame_count:
        msg = (
            f"replay_summary.frame_count must equal len(replay_frames) ({frame_count}), got {fc!r}"
        )
        raise ReplayFixtureJsonError(msg)

    etc = summary["event_type_counts"]
    if not isinstance(etc, dict):
        msg = "replay_summary.event_type_counts must be object"
        raise ReplayFixtureJsonError(msg)
    expected_counts = _event_type_counts_from_sequence(events)
    if etc != expected_counts:
        msg = "replay_summary.event_type_counts does not match replay_event_sequence"
        raise ReplayFixtureJsonError(msg)

    rt = summary["replay_truncated"]
    if not isinstance(rt, bool):
        msg = f"replay_summary.replay_truncated must be bool, got {type(rt).__name__}"
        raise ReplayFixtureJsonError(msg)
    return rt


def _validate_frame(obj: object, *, position: int) -> dict[str, object]:
    if not isinstance(obj, dict):
        msg = f"replay_frames[{position}] must be object, got {type(obj).__name__}"
        raise ReplayFixtureJsonError(msg)
    fk = frozenset(obj)
    if fk != _FRAME_KEYS:
        msg = (
            f"replay_frames[{position}] has wrong keys: "
            f"missing {sorted(_FRAME_KEYS - fk)} extra {sorted(fk - _FRAME_KEYS)}"
        )
        raise ReplayFixtureJsonError(msg)
    fi = obj["frame_index"]
    if type(fi) is not int or fi != position:
        msg = f"replay_frames[{position}].frame_index must be {position}, got {fi!r}"
        raise ReplayFixtureJsonError(msg)
    et = obj["event_type"]
    if not isinstance(et, str) or not et.strip():
        msg = f"replay_frames[{position}].event_type must be non-empty string"
        raise ReplayFixtureJsonError(msg)
    for key in ("title", "description"):
        v = obj[key]
        if not isinstance(v, str):
            msg = f"replay_frames[{position}].{key} must be string"
            raise ReplayFixtureJsonError(msg)
    for key in ("visible_cells", "overlay_cells"):
        v = obj[key]
        if not isinstance(v, list):
            msg = f"replay_frames[{position}].{key} must be array"
            raise ReplayFixtureJsonError(msg)
    m = obj["metrics"]
    if not isinstance(m, dict):
        msg = f"replay_frames[{position}].metrics must be object"
        raise ReplayFixtureJsonError(msg)
    return obj


def parse_replay_fixture_json(data: Mapping[str, object]) -> ReplayFixtureJson:
    if not isinstance(data, dict):
        msg = "root JSON value must be an object"
        raise ReplayFixtureJsonError(msg)

    _validate_top_level(data)
    schema_raw = _require_schema_version(data["schema_version"])

    rid = data["replay_fixture_id"]
    if not isinstance(rid, str) or not rid.strip():
        msg = "replay_fixture_id must be a non-empty string"
        raise ReplayFixtureJsonError(msg)

    frames_raw = data["replay_frames"]
    if not isinstance(frames_raw, list):
        msg = f"replay_frames must be array, got {type(frames_raw).__name__}"
        raise ReplayFixtureJsonError(msg)
    frames: list[dict[str, object]] = []
    for i, item in enumerate(frames_raw):
        frames.append(_validate_frame(item, position=i))

    seq_raw = data["replay_event_sequence"]
    if not isinstance(seq_raw, list):
        msg = f"replay_event_sequence must be array, got {type(seq_raw).__name__}"
        raise ReplayFixtureJsonError(msg)
    events: list[str] = []
    for i, x in enumerate(seq_raw):
        if not isinstance(x, str):
            msg = f"replay_event_sequence[{i}] must be string, got {type(x).__name__}"
            raise ReplayFixtureJsonError(msg)
        events.append(x)

    if len(events) != len(frames):
        msg = f"replay_event_sequence length {len(events)} != replay_frames length {len(frames)}"
        raise ReplayFixtureJsonError(msg)
    for i, fr in enumerate(frames):
        if fr["event_type"] != events[i]:
            msg = (
                f"replay_event_sequence[{i}] {events[i]!r} != "
                f"replay_frames[{i}].event_type {fr['event_type']!r}"
            )
            raise ReplayFixtureJsonError(msg)

    replay_truncated = _validate_replay_summary(
        data["replay_summary"], frame_count=len(frames), events=events
    )
    trunc_reason = _validate_truncation_reason_field(data, replay_truncated=replay_truncated)

    meta: dict[str, object] | None = None
    if "metadata" in data:
        mraw = data["metadata"]
        if not isinstance(mraw, dict):
            msg = f"metadata must be object, got {type(mraw).__name__}"
            raise ReplayFixtureJsonError(msg)
        meta = copy.deepcopy(mraw)

    return ReplayFixtureJson(
        schema_version=schema_raw,
        replay_fixture_id=rid,
        replay_frames=tuple(copy.deepcopy(f) for f in frames),
        replay_summary=copy.deepcopy(dict(data["replay_summary"])),
        replay_event_sequence=tuple(events),
        truncation_reason=trunc_reason,
        metadata=meta,
    )


def replay_fixture_json_to_safe_dict(fixture: ReplayFixtureJson) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema_version": fixture.schema_version,
        "replay_fixture_id": fixture.replay_fixture_id,
        "replay_frames": [copy.deepcopy(dict(f)) for f in fixture.replay_frames],
        "replay_summary": copy.deepcopy(dict(fixture.replay_summary)),
        "replay_event_sequence": list(fixture.replay_event_sequence),
    }
    if fixture.truncation_reason is not None:
        out["truncation_reason"] = fixture.truncation_reason
    if fixture.metadata is not None:
        out["metadata"] = copy.deepcopy(dict(fixture.metadata))
    return out
