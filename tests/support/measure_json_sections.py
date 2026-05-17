"""Sequence 13A — deterministic JSON size attribution for Lab POST payloads (tests only)."""

from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from django_apps.shapez_asteroid.optimization.optimization_ui_payload import (
    OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY,
)


def _json_bytes(obj: object) -> int:
    return len(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    )


def _lab_frame_full_map_len(frame: object) -> int:
    if not isinstance(frame, dict):
        return 0
    fm = frame.get("full_map")
    return len(fm) if isinstance(fm, list) else 0


def _optimization_cell_totals(frame: object) -> tuple[int, int, int]:
    """Return (visible_len, overlay_len, total) for one optimization frame dict."""

    if not isinstance(frame, dict):
        return 0, 0, 0
    vis = frame.get("visible_cells")
    ovl = frame.get("overlay_cells")
    vn = len(vis) if isinstance(vis, list) else 0
    on = len(ovl) if isinstance(ovl, list) else 0
    return vn, on, vn + on


def measure_json_sections(root: Mapping[str, Any]) -> dict[str, Any]:
    """Attribute serialized size of a JSON-compatible mapping (e.g. POST JsonResponse body).

    * ``top_level_key_bytes[k]`` — UTF-8 length of ``json.dumps(value)`` for that key only
      (not including the key string or outer object punctuation; for contribution estimates).
    * Lab / optimization subsection stats use the same JSON encoding as ``total_bytes`` slices
      where noted.
    """

    total_bytes = _json_bytes(root)
    top_level_key_bytes = {
        str(k): _json_bytes(v) for k, v in sorted(root.items(), key=lambda kv: str(kv[0]))
    }

    lab_frames = root.get("lab_replay_frames_json")
    lab_list = lab_frames if isinstance(lab_frames, list) else []
    lab_frame_bytes = [_json_bytes(f) for f in lab_list]
    lab_fm_lens = [_lab_frame_full_map_len(f) for f in lab_list]

    opt_root = root.get(OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY)
    opt_frames: list[Any] = []
    if isinstance(opt_root, dict):
        raw_frames = opt_root.get("frames")
        if isinstance(raw_frames, list):
            opt_frames = list(raw_frames)
    opt_frame_bytes = [_json_bytes(f) for f in opt_frames]
    opt_cell_totals = [_optimization_cell_totals(f)[2] for f in opt_frames]
    opt_vis = [_optimization_cell_totals(f)[0] for f in opt_frames]
    opt_ovl = [_optimization_cell_totals(f)[1] for f in opt_frames]

    n_lab = len(lab_frame_bytes)
    n_opt = len(opt_frame_bytes)

    return {
        "total_bytes": total_bytes,
        "top_level_key_bytes": top_level_key_bytes,
        "lab_replay": {
            "frame_count": n_lab,
            "sum_frame_bytes": sum(lab_frame_bytes),
            "max_frame_bytes": max(lab_frame_bytes) if lab_frame_bytes else 0,
            "avg_frame_bytes": (sum(lab_frame_bytes) / n_lab) if n_lab else 0.0,
            "full_map_len_max": max(lab_fm_lens) if lab_fm_lens else 0,
            "full_map_len_sum": sum(lab_fm_lens),
        },
        "optimization_replay": {
            "frame_count": n_opt,
            "sum_frame_bytes": sum(opt_frame_bytes),
            "max_frame_bytes": max(opt_frame_bytes) if opt_frame_bytes else 0,
            "avg_frame_bytes": (sum(opt_frame_bytes) / n_opt) if n_opt else 0.0,
            "visible_len_max": max(opt_vis) if opt_vis else 0,
            "overlay_len_max": max(opt_ovl) if opt_ovl else 0,
            "visible_plus_overlay_max": max(opt_cell_totals) if opt_cell_totals else 0,
        },
    }


def assert_optimization_replay_hard_caps(
    root: Mapping[str, Any],
    *,
    max_frames: int = 500,
    max_cells_per_frame: int = 128,
) -> None:
    """Assert v0 optimization replay caps on a decoded POST-style dict (raises AssertionError)."""

    opt_root = root.get(OPTIMIZATION_REPLAY_LAB_PAYLOAD_KEY)
    assert isinstance(opt_root, dict), "optimization_replay missing or not a dict"
    raw_frames = opt_root.get("frames")
    assert isinstance(raw_frames, list), "optimization_replay.frames must be a list"
    assert (
        len(raw_frames) <= max_frames
    ), f"optimization frame_count {len(raw_frames)} exceeds max_frames {max_frames}"
    for i, fr in enumerate(raw_frames):
        vn, on, total = _optimization_cell_totals(fr)
        assert (
            total <= max_cells_per_frame
        ), f"optimization frame {i}: visible+overlay={total} exceeds {max_cells_per_frame}"


def assert_lab_replay_not_capped_by_optimization_constants(root: Mapping[str, Any]) -> int:
    """Return lab frame count (informational).

    Lab replay uses a separate pipeline without ``MAX_REPLAY_*`` optimization caps.
    Callers document/assert that lab frames may exceed optimization cell/frame caps.
    """

    lab_frames = root.get("lab_replay_frames_json")
    if not isinstance(lab_frames, list):
        return 0
    return len(lab_frames)
