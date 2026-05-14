"""
v2 copy-preview: ``map_timeline`` frames (display-only).

Reconstruction milestones (3) plus fixed placeholder rows for Pass1–final (not implemented yet).
Each frame is one **full** ``mining_map`` row list (no delta). Does not read NDJSON,
``solver_replay``, or ``solver_summary``. Domain modules must not import this package.
"""

from __future__ import annotations

import copy
import logging
from typing import Any, cast

from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BlueprintCell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    ReconstructionDTO,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.preview_json import to_jsonable
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction import (
    asteroid_reconstruction as _ar,
)
from django_apps.shapez_asteroid.services.asteroid_patch_interior import (
    compute_patch_interior_cells,
)
from django_apps.shapez_asteroid.services.blueprint_entry_parsing import int_or_none as _int_or_none
from django_apps.shapez_asteroid.services.style_classifier import (
    classify_layout_type,
    is_extraction_style,
)

logger = logging.getLogger(__name__)


def _dev_log_v2_preview_frame(frame_id: str, *, entry_count: int | None = None) -> None:
    """``SHAPEZ_DEV_ASTEROID_STEP_REPORT`` ON일 때만 v2 프레임 경계를 debug 로그로 남긴다."""

    try:
        from django.conf import settings

        if not getattr(settings, "SHAPEZ_DEV_ASTEROID_STEP_REPORT", False):
            return
    except Exception:
        return
    if entry_count is None:
        logger.debug("v2_preview_map_timeline_frame frame_id=%s", frame_id)
    else:
        logger.debug(
            "v2_preview_map_timeline_frame frame_id=%s entry_count=%s",
            frame_id,
            entry_count,
        )


# UI ``data-map-step-*`` slugs in ``asteroid_optimizer.html``.
# Pass1 … final — not wired yet.
_V2_PREVIEW_PLACEHOLDER_FRAME_IDS: tuple[str, ...] = (
    "v2_pass1_candidates",
    "v2_pass1_provisional",
    "v2_pass2_candidates",
    "v2_pass2_provisional",
    "v2_step4_trunk_seed",
    "v2_step4_routing",
    "v2_final_validation",
    "v2_final_layout",
)


def _surface_hint_from_layout_type(t_str: str | None) -> str | None:
    if not t_str:
        return None
    low = str(t_str).lower()
    if "fluid" in low or "pump" in low:
        return "fluid"
    if "shape" in low:
        return "shape"
    return None


def _dominant_surface_for_shell(
    decoded: dict[str, Any],
    recon: ReconstructionDTO,
) -> str:
    hints: list[str] = []
    shell = frozenset(recon.extraction_shell_cells)
    for item in _ar.gather_bp_entries_recursive(decoded):
        x_val = _int_or_none(item.get("X"))
        if x_val is None or x_val == 0:
            continue
        y_val = _int_or_none(item.get("Y"))
        if y_val is None:
            y_val = 0
        if (x_val, y_val) not in shell:
            continue
        t_raw = item.get("T")
        t_str = t_raw if isinstance(t_raw, str) else (str(t_raw) if t_raw is not None else None)
        h = _surface_hint_from_layout_type(t_str)
        if h:
            hints.append(h)
    if "fluid" in hints:
        return "fluid"
    if "shape" in hints:
        return "shape"
    return "shape"


def _last_write_entries_by_cell(
    decoded: dict[str, Any],
) -> dict[BlueprintCell, dict[str, Any]]:
    """Last BP entry dict per (x, y), scanning order compatible with timeline code."""

    by_coord: dict[BlueprintCell, dict[str, Any]] = {}
    for item in _ar.gather_bp_entries_recursive(decoded):
        if not isinstance(item, dict):
            continue
        x_val = _int_or_none(item.get("X"))
        if x_val is None or x_val == 0:
            continue
        y_val = _int_or_none(item.get("Y"))
        if y_val is None:
            y_val = 0
        by_coord[(x_val, y_val)] = item
    return by_coord


def _attach_layout_kind(cell: dict[str, Any], t_str: str | None) -> None:
    if t_str is None:
        return
    st = classify_layout_type(t_str)
    if st is not None and is_extraction_style(st):
        cell["layout_kind"] = st.value


def _summary_from_rows(
    rows: list[dict[str, Any]],
    *,
    frame_id: str,
    source_kind: str | None,
) -> dict[str, Any]:
    if not rows:
        return {
            "entry_count": 0,
            "x_min": 0,
            "x_max": 0,
            "y_min": 0,
            "y_max": 0,
            "phase": frame_id,
        }
    xs = [int(r["x"]) for r in rows]
    ys = [int(r["y"]) for r in rows]
    out: dict[str, Any] = {
        "entry_count": len(rows),
        "x_min": min(xs),
        "x_max": max(xs),
        "y_min": min(ys),
        "y_max": max(ys),
        "phase": frame_id,
    }
    if source_kind:
        out["source_kind"] = source_kind
    return out


def _stamp_row(
    row: dict[str, Any],
    *,
    frame_id: str,
    source_kind: str | None,
) -> dict[str, Any]:
    r = dict(row)
    r["phase"] = frame_id
    if source_kind:
        r["source_kind"] = source_kind
    return r


def _build_transport_shell_rows(
    recon: ReconstructionDTO,
    dominant: str,
    entries: dict[BlueprintCell, dict[str, Any]],
    frame_id: str,
    source_kind: str | None,
) -> list[dict[str, Any]]:
    belt = frozenset(recon.belt_cells)
    pipe = frozenset(recon.pipe_cells)
    shell = frozenset(recon.extraction_shell_cells)
    # Match ``blueprint_map_summary._asteroid_envelope_coords``: shell ∪ enclosed interior
    # (including cells occupied by belt/pipe inside a hole — not only ``interior_patch_cells``).
    asteroid_envelope = shell | frozenset(
        compute_patch_interior_cells(set(shell), perimeter_bridge_steps=1)
    )
    coords = sorted(belt | pipe | shell, key=lambda c: (c[1], c[0]))
    out: list[dict[str, Any]] = []
    for x, y in coords:
        if (x, y) in belt:
            out.append(
                _stamp_row(
                    {
                        "x": x,
                        "y": y,
                        "role": "belt",
                        "surface": dominant,
                        "transport_over_void": (x, y) not in asteroid_envelope,
                    },
                    frame_id=frame_id,
                    source_kind=source_kind,
                )
            )
        elif (x, y) in pipe:
            out.append(
                _stamp_row(
                    {
                        "x": x,
                        "y": y,
                        "role": "pipe",
                        "surface": dominant,
                        "transport_over_void": (x, y) not in asteroid_envelope,
                    },
                    frame_id=frame_id,
                    source_kind=source_kind,
                )
            )
        else:
            item = entries.get((x, y))
            t_str: str | None = None
            r_val: int | None = None
            if item:
                t_raw = item.get("T")
                if isinstance(t_raw, str):
                    t_str = t_raw
                elif t_raw is not None:
                    t_str = str(t_raw)
                else:
                    t_str = None
                r_val = _int_or_none(item.get("R"))
            surf = _surface_hint_from_layout_type(t_str) or dominant
            cell: dict[str, Any] = {
                "x": x,
                "y": y,
                "role": "occupied",
                "surface": surf,
            }
            if t_str is not None:
                cell["t"] = t_str
            if r_val is not None:
                cell["r"] = r_val
            _attach_layout_kind(cell, t_str)
            out.append(_stamp_row(cell, frame_id=frame_id, source_kind=source_kind))
    return out


def _rows_to_cell_dict(rows: list[dict[str, Any]]) -> dict[BlueprintCell, dict[str, Any]]:
    acc: dict[BlueprintCell, dict[str, Any]] = {}
    for r in rows:
        acc[(int(r["x"]), int(r["y"]))] = dict(r)
    return acc


def _dict_to_sorted_rows(cells: dict[BlueprintCell, dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(cells[k]) for k in sorted(cells.keys(), key=lambda c: (c[1], c[0]))]


def _merge_interior_void(
    base_rows: list[dict[str, Any]],
    interior: tuple[BlueprintCell, ...],
    dominant: str,
    frame_id: str,
    source_kind: str | None,
) -> list[dict[str, Any]]:
    cells = _rows_to_cell_dict(base_rows)
    for x, y in interior:
        if (x, y) not in cells:
            cells[(x, y)] = _stamp_row(
                {
                    "x": x,
                    "y": y,
                    "role": "inferred",
                    "surface": dominant,
                },
                frame_id=frame_id,
                source_kind=source_kind,
            )
    return _dict_to_sorted_rows(cells)


def _apply_mineable_highlights(
    rows: list[dict[str, Any]],
    mineable: frozenset[BlueprintCell],
    frame_id: str,
    source_kind: str | None,
) -> list[dict[str, Any]]:
    cells = _rows_to_cell_dict(rows)
    for x, y in mineable:
        key = (x, y)
        if key not in cells:
            continue
        r = dict(cells[key])
        if r.get("role") == "inferred":
            r["layout_kind"] = "asteroid_field"
        r["phase"] = frame_id
        if source_kind:
            r["source_kind"] = source_kind
        cells[key] = r
    return _dict_to_sorted_rows(cells)


def _placeholder_milestone_frame(
    *,
    frame_id: str,
    mining_map_rows: list[dict[str, Any]],
    source_kind: str | None,
) -> dict[str, Any]:
    rows = copy.deepcopy(mining_map_rows)
    summary = _summary_from_rows(rows, frame_id=frame_id, source_kind=source_kind)
    summary["preview_placeholder"] = True
    return {"id": frame_id, "summary": summary, "mining_map": rows}


def build_v2_preview_map_frames(
    decoded: dict[str, Any],
    recon: ReconstructionDTO,
    *,
    source_kind: str | None = None,
) -> list[dict[str, Any]]:
    """
    Return ``map_timeline``-compatible frames (variable length).

    Always appends one row per ``_V2_PREVIEW_PLACEHOLDER_FRAME_IDS`` (display-only; same
    ``mining_map`` as the last reconstruction frame until those milestones exist).

    When reconstruction is empty (no barrier cells), returns **only** those placeholder
    frames (empty ``mining_map`` each).
    """

    if not recon.full_barrier_cells:
        only_placeholders = [
            _placeholder_milestone_frame(
                frame_id=fid,
                mining_map_rows=[],
                source_kind=source_kind,
            )
            for fid in _V2_PREVIEW_PLACEHOLDER_FRAME_IDS
        ]
        for fr in only_placeholders:
            if isinstance(fr, dict) and isinstance(fr.get("id"), str):
                summ_raw = fr.get("summary")
                summ: dict[str, Any] = summ_raw if isinstance(summ_raw, dict) else {}
                ec = summ.get("entry_count") if isinstance(summ.get("entry_count"), int) else 0
                _dev_log_v2_preview_frame(fr["id"], entry_count=ec)
        return cast(list[dict[str, Any]], to_jsonable(only_placeholders))

    dominant = _dominant_surface_for_shell(decoded, recon)
    entries = _last_write_entries_by_cell(decoded)

    frames: list[dict[str, Any]] = []

    fid1 = "v2_recon_transport_shell"
    rows1 = _build_transport_shell_rows(recon, dominant, entries, fid1, source_kind)
    s1 = _summary_from_rows(rows1, frame_id=fid1, source_kind=source_kind)
    frames.append({"id": fid1, "summary": s1, "mining_map": copy.deepcopy(rows1)})
    _dev_log_v2_preview_frame(fid1, entry_count=int(s1["entry_count"]))

    fid2 = "v2_recon_interior_void"
    rows2 = _merge_interior_void(rows1, recon.interior_patch_cells, dominant, fid2, source_kind)
    s2 = _summary_from_rows(rows2, frame_id=fid2, source_kind=source_kind)
    frames.append({"id": fid2, "summary": s2, "mining_map": copy.deepcopy(rows2)})
    _dev_log_v2_preview_frame(fid2, entry_count=int(s2["entry_count"]))

    fid3 = "v2_recon_mineable"
    mineable_f = frozenset(recon.mineable_placement_cells)
    rows3 = _apply_mineable_highlights(rows2, mineable_f, fid3, source_kind)
    s3 = _summary_from_rows(rows3, frame_id=fid3, source_kind=source_kind)
    frames.append({"id": fid3, "summary": s3, "mining_map": copy.deepcopy(rows3)})
    _dev_log_v2_preview_frame(fid3, entry_count=int(s3["entry_count"]))

    last_rows = frames[-1]["mining_map"]
    if not isinstance(last_rows, list):
        last_rows = []
    for fid in _V2_PREVIEW_PLACEHOLDER_FRAME_IDS:
        ph = _placeholder_milestone_frame(
            frame_id=fid,
            mining_map_rows=last_rows,
            source_kind=source_kind,
        )
        frames.append(ph)
        summ_ph_raw = ph.get("summary")
        summ_ph: dict[str, Any] = summ_ph_raw if isinstance(summ_ph_raw, dict) else {}
        ec_ph = summ_ph.get("entry_count") if isinstance(summ_ph.get("entry_count"), int) else None
        _dev_log_v2_preview_frame(fid, entry_count=ec_ph)

    return cast(list[dict[str, Any]], to_jsonable(frames))


V2_PREVIEW_PLACEHOLDER_STEP_IDS: tuple[str, ...] = _V2_PREVIEW_PLACEHOLDER_FRAME_IDS

__all__ = ["V2_PREVIEW_PLACEHOLDER_STEP_IDS", "build_v2_preview_map_frames"]
