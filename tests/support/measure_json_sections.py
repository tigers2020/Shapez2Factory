"""Sequence 13A/13B ??deterministic JSON size attribution for Lab POST payloads (tests only)."""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Mapping, Sequence
from typing import Any

_DEFAULT_LARGEST_FRAMES_N = 8


def _json_bytes(obj: object) -> int:
    return len(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    )


def _lab_frame_full_map_len(frame: object) -> int:
    if not isinstance(frame, dict):
        return 0
    fm = frame.get("full_map")
    return len(fm) if isinstance(fm, list) else 0


def _lab_frame_full_map_list(frame: object) -> list[Any]:
    if not isinstance(frame, dict):
        return []
    fm = frame.get("full_map")
    return list(fm) if isinstance(fm, list) else []


def _slot_key_from_row(row: object) -> tuple[int, int, int | None]:
    if not isinstance(row, dict):
        return (0, 0, None)
    ly = row.get("layer")
    ly_i: int | None = None if ly is None else int(ly)
    return (int(row.get("x", 0)), int(row.get("y", 0)), ly_i)


def _full_map_row_fingerprint(row: object) -> str:
    if not isinstance(row, dict):
        return json.dumps(row, sort_keys=True, separators=(",", ":"))
    return json.dumps(row, sort_keys=True, separators=(",", ":"))


def _full_map_fingerprint(fm: Sequence[object]) -> str:
    rows = [r for r in fm if isinstance(r, dict)]
    rows_sorted = sorted(rows, key=_slot_key_from_row)
    return json.dumps(rows_sorted, sort_keys=True, separators=(",", ":"))


def _diff_structure_stats(diff: object) -> dict[str, int]:
    if not isinstance(diff, dict):
        return {
            "added_len": 0,
            "removed_len": 0,
            "changed_len": 0,
            "diff_body_bytes": 0,
        }
    added = diff.get("added")
    removed = diff.get("removed")
    changed = diff.get("changed")
    an = len(added) if isinstance(added, list) else 0
    rn = len(removed) if isinstance(removed, list) else 0
    cn = len(changed) if isinstance(changed, list) else 0
    body = {k: diff[k] for k in ("added", "removed", "changed") if k in diff}
    return {
        "added_len": an,
        "removed_len": rn,
        "changed_len": cn,
        "diff_body_bytes": _json_bytes(body),
    }


def _lab_redundancy_and_sizes(lab_list: list[Any]) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Return (redundancy_stats, largest_frames_meta) for Lab replay frames only."""

    fps: list[str] = []
    total_row_instances = 0
    row_fp_set: set[str] = set()
    slot_counter: Counter[tuple[int, int, int | None]] = Counter()
    sum_full_map_bytes = 0
    sum_diff_body_bytes = 0
    sum_diff_added_lens = 0
    sum_diff_removed_lens = 0

    for fr in lab_list:
        fm = _lab_frame_full_map_list(fr)
        total_row_instances += len(fm)
        fps.append(_full_map_fingerprint(fm))
        sum_full_map_bytes += _json_bytes(fm)
        for row in fm:
            row_fp_set.add(_full_map_row_fingerprint(row))
            if isinstance(row, dict):
                slot_counter[_slot_key_from_row(row)] += 1
        diff_obj: object = {}
        if isinstance(fr, dict):
            diff_obj = fr.get("diff")
            if not isinstance(diff_obj, dict):
                pl = fr.get("frame_payload")
                if isinstance(pl, dict):
                    d = pl.get("diff")
                    diff_obj = d if isinstance(d, dict) else {}
        ds = _diff_structure_stats(diff_obj)
        sum_diff_body_bytes += int(ds["diff_body_bytes"])
        sum_diff_added_lens += int(ds["added_len"])
        sum_diff_removed_lens += int(ds["removed_len"])

    adjacent_identical = 0
    for i in range(1, len(fps)):
        if fps[i] == fps[i - 1]:
            adjacent_identical += 1

    unique_row_identities = len(row_fp_set)
    duplicate_row_instance_estimate = max(0, total_row_instances - unique_row_identities)
    slots_with_multiplicity_gt_1 = sum(1 for _k, c in slot_counter.items() if c > 1)

    meta: list[dict[str, Any]] = []
    for i, fr in enumerate(lab_list):
        if not isinstance(fr, dict):
            meta.append({"list_index": i, "frame_index": None, "frame_key": None, "bytes": 0})
            continue
        fi = fr.get("frame_index")
        fk = fr.get("frame_key")
        meta.append(
            {
                "list_index": i,
                "frame_index": int(fi) if isinstance(fi, int) else None,
                "frame_key": str(fk) if fk is not None else None,
                "bytes": _json_bytes(fr),
            },
        )
    meta_sorted = sorted(meta, key=lambda m: (-int(m["bytes"]), int(m["list_index"])))

    redundancy: dict[str, Any] = {
        "adjacent_identical_full_map_count": adjacent_identical,
        "cell_row_total_instances": total_row_instances,
        "cell_row_unique_identity_count": unique_row_identities,
        "cell_row_duplicate_instance_estimate": duplicate_row_instance_estimate,
        "coordinate_slots_with_multiple_instances": slots_with_multiplicity_gt_1,
        "sum_full_map_json_bytes": sum_full_map_bytes,
        "sum_diff_body_json_bytes": sum_diff_body_bytes,
        "sum_diff_added_len": sum_diff_added_lens,
        "sum_diff_removed_len": sum_diff_removed_lens,
    }
    return redundancy, meta_sorted


def measure_json_sections(
    root: Mapping[str, Any],
    *,
    largest_lab_frames_n: int = _DEFAULT_LARGEST_FRAMES_N,
) -> dict[str, Any]:
    """Attribute serialized size of a JSON-compatible mapping (e.g. POST JsonResponse body).

    * ``top_level_key_bytes[k]`` ??UTF-8 length of ``json.dumps(value)`` for that key only
      (not including the key string or outer object punctuation; for contribution estimates).
    * Lab subsection stats use the same JSON encoding as ``total_bytes`` slices where noted.
    * Sequence 13B: Lab replay redundancy (adjacent identical ``full_map``, row-identity
      duplication estimates, diff vs ``full_map`` byte sums) and largest-frame index metadata
      ??tests and diagnostics only; does not change runtime payloads.
    """

    total_bytes = _json_bytes(root)
    top_level_key_bytes = {
        str(k): _json_bytes(v) for k, v in sorted(root.items(), key=lambda kv: str(kv[0]))
    }

    lab_frames = root.get("lab_replay_frames_json")
    lab_list = lab_frames if isinstance(lab_frames, list) else []
    lab_frame_bytes = [_json_bytes(f) for f in lab_list]
    lab_fm_lens = [_lab_frame_full_map_len(f) for f in lab_list]
    redundancy, largest_meta = _lab_redundancy_and_sizes(lab_list)
    lab_key = "lab_replay_frames_json"
    lab_top_level_value_bytes = int(top_level_key_bytes.get(lab_key, 0))

    n_lab = len(lab_frame_bytes)
    sum_lab_fb = sum(lab_frame_bytes)
    max_lab_fb = max(lab_frame_bytes) if lab_frame_bytes else 0
    avg_lab = (sum_lab_fb / n_lab) if n_lab else 0.0
    fm_max = max(lab_fm_lens) if lab_fm_lens else 0
    fm_sum = sum(lab_fm_lens)

    cap_n = max(0, int(largest_lab_frames_n))
    largest_cut = largest_meta[:cap_n] if cap_n else []

    return {
        "total_bytes": total_bytes,
        "top_level_key_bytes": top_level_key_bytes,
        "lab_replay": {
            "frame_count": n_lab,
            "sum_frame_bytes": sum_lab_fb,
            "max_frame_bytes": max_lab_fb,
            "avg_frame_bytes": avg_lab,
            "full_map_len_max": fm_max,
            "full_map_len_sum": fm_sum,
            # --- Sequence 13B explicit names (for docs / regression contracts) ---
            "lab_frame_count": n_lab,
            "lab_total_bytes": lab_top_level_value_bytes,
            "lab_replay_frames_json_value_bytes": lab_top_level_value_bytes,
            "max_lab_frame_bytes": max_lab_fb,
            "average_lab_frame_bytes": avg_lab,
            "lab_full_map_cell_count_sum": fm_sum,
            "lab_full_map_cell_count_max": fm_max,
            "lab_full_map_cell_count_avg": (fm_sum / n_lab) if n_lab else 0.0,
            "largest_lab_frames": largest_cut,
            "redundancy": redundancy,
        },
    }


def assert_lab_replay_not_capped_by_optimization_constants(root: Mapping[str, Any]) -> int:
    """Return lab frame count (informational).

    Lab replay uses a separate pipeline without ``MAX_REPLAY_*`` optimization caps.
    Callers document/assert that lab frames may exceed optimization cell/frame caps.
    """

    lab_frames = root.get("lab_replay_frames_json")
    if not isinstance(lab_frames, list):
        return 0
    return len(lab_frames)
