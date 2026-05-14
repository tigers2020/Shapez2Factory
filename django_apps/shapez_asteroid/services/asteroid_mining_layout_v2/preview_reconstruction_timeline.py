"""
v2 copy-preview: ``map_timeline`` frames (display-only).

Reconstruction milestones (3) plus fixed placeholder rows for Pass1–final (not implemented yet).
Each frame is one **full** ``mining_map`` row list (no delta). Does not read NDJSON,
``solver_replay``, or ``solver_summary``. Domain modules must not import this package.
"""

from __future__ import annotations

import copy
import logging
import os
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
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction import (
    patch_interior as _patch_interior,
)
from django_apps.shapez_asteroid.services.blueprint_entry_parsing import int_or_none as _int_or_none
from django_apps.shapez_asteroid.services.style_classifier import (
    PlotStyle,
    classify_layout_type,
    is_extraction_style,
    mining_surface_from_layout,
)

logger = logging.getLogger(__name__)

# Synthetic ``T`` for preview-only cells where equipment was stripped back to bare field.
PREVIEW_ASTEROID_REPLACE_TILE_T = "AsteroidField_PreviewReplace"

_PREVIEW_EXTRACTOR_STYLES: frozenset[PlotStyle] = frozenset(
    {
        PlotStyle.fluid_miner,
        PlotStyle.miner,
        PlotStyle.extractor,
        PlotStyle.booster,
    }
)
_PREVIEW_EXTENSION_STYLES: frozenset[PlotStyle] = frozenset(
    {PlotStyle.extension, PlotStyle.fluid_extension}
)


def _preview_strip_targets_for_styles(
    rows: list[dict[str, Any]],
    candidate_coords: frozenset[BlueprintCell],
    entries: dict[BlueprintCell, dict[str, Any]],
    styles: frozenset[PlotStyle],
) -> frozenset[BlueprintCell]:
    """Strip/replace only coords **present** on the map whose last BP ``T`` matches ``styles``.

    ``reconstruction`` union sets can list the same coordinate as belt and extension; the
    timeline paints belt first, then drops the cell when stripping transport. Painting every
    ``extension_cells`` entry would re-add tiles inside voids ("filling").
    """

    present = frozenset((int(r["x"]), int(r["y"])) for r in rows)
    matched: set[BlueprintCell] = set()
    for xy in candidate_coords:
        if xy not in present:
            continue
        item = entries.get(xy)
        if not item:
            continue
        t_raw = item.get("T")
        t_str = t_raw if isinstance(t_raw, str) else (str(t_raw) if t_raw is not None else None)
        st = classify_layout_type(t_str)
        if st in styles:
            matched.add(xy)
    return frozenset(matched)


def _dev_log_v2_preview_frame(frame_id: str, *, entry_count: int | None = None) -> None:
    """``SHAPEZ_DEV_ASTEROID_STEP_REPORT`` ON일 때만 v2 프레임 경계를 debug 로그로 남긴다."""

    flag = os.environ.get("SHAPEZ_DEV_ASTEROID_STEP_REPORT", "").strip().lower()
    if flag not in ("1", "true", "yes", "on"):
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


def _dominant_surface_for_shell(
    decoded: dict[str, Any],
    recon: ReconstructionDTO,
) -> str:
    """Default ``surface`` when a cell has no explicit shape/fluid hint.

    E.g. bare ``AsteroidField*`` entries do not map to shape/fluid via
    ``mining_surface_from_layout``.

    Shell-only blueprints never yield ``mining_surface_from_layout`` on shell tiles, so we
    also scan **extractor and extension** coordinates from reconstruction; otherwise
    fluid-heavy layouts incorrectly fall back to ``shape`` (inner-patch inferred voids,
    belt tint, etc.).
    """

    hints: list[str] = []
    hint_coords = (
        frozenset(recon.extraction_shell_cells)
        | frozenset(recon.extractor_cells)
        | frozenset(recon.extension_cells)
    )
    for item in _ar.gather_bp_entries_recursive(decoded):
        x_val = _int_or_none(item.get("X"))
        if x_val is None or x_val == 0:
            continue
        y_val = _int_or_none(item.get("Y"))
        if y_val is None:
            y_val = 0
        if (x_val, y_val) not in hint_coords:
            continue
        t_raw = item.get("T")
        t_str = t_raw if isinstance(t_raw, str) else (str(t_raw) if t_raw is not None else None)
        h = mining_surface_from_layout(t_str)
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


def _occupied_cell_payload(
    x: int,
    y: int,
    entries: dict[BlueprintCell, dict[str, Any]],
    dominant: str,
) -> dict[str, Any]:
    """Mining-map row body for a blueprint-occupied cell (no ``phase``)."""

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
    surf = mining_surface_from_layout(t_str) or dominant
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
    return cell


def _filter_mining_map_rows(
    rows: list[dict[str, Any]],
    drop: frozenset[BlueprintCell],
) -> list[dict[str, Any]]:
    return [dict(r) for r in rows if (int(r["x"]), int(r["y"])) not in drop]


def _rephase_rows(
    rows: list[dict[str, Any]],
    frame_id: str,
    source_kind: str | None,
) -> list[dict[str, Any]]:
    return [_stamp_row(dict(r), frame_id=frame_id, source_kind=source_kind) for r in rows]


def _strip_rows_replace_coords_with_asteroid_field(
    rows: list[dict[str, Any]],
    removed_coords: frozenset[BlueprintCell],
    entries: dict[BlueprintCell, dict[str, Any]],
    dominant: str,
    frame_id: str,
    source_kind: str | None,
) -> list[dict[str, Any]]:
    """Drop rows at ``removed_coords``, then paint those cells as bare asteroid field."""

    base = _filter_mining_map_rows(rows, removed_coords)
    cells = _rows_to_cell_dict(base)
    for x, y in sorted(removed_coords, key=lambda c: (c[1], c[0])):
        item = entries.get((x, y))
        t_raw = item.get("T") if item else None
        t_str = t_raw if isinstance(t_raw, str) else (str(t_raw) if t_raw is not None else None)
        surf = mining_surface_from_layout(t_str) or dominant
        cells[(x, y)] = _stamp_row(
            {
                "x": x,
                "y": y,
                "role": "occupied",
                "surface": surf,
                "layout_kind": "asteroid_field",
                "t": PREVIEW_ASTEROID_REPLACE_TILE_T,
            },
            frame_id=frame_id,
            source_kind=source_kind,
        )
    return _dict_to_sorted_rows(cells)


def _inner_patch_surface_coords(
    recon: ReconstructionDTO,
    rows_post_strip: list[dict[str, Any]],
) -> frozenset[BlueprintCell]:
    """Shell-like surface for inner-patch view: blueprint shell plus preview-only field tiles.

    ``extraction_shell_cells`` lists only ``AsteroidField*`` blueprint entries. After strip,
    former extractor/extension cells are drawn as ``PREVIEW_ASTEROID_REPLACE_TILE_T`` and
    must stay visible in inner-patch / mineable frames.
    """

    s: set[BlueprintCell] = set(recon.extraction_shell_cells)
    for r in rows_post_strip:
        if r.get("t") == PREVIEW_ASTEROID_REPLACE_TILE_T:
            s.add((int(r["x"]), int(r["y"])))
            continue
        if r.get("layout_kind") == "asteroid_field" and r.get("role") == "occupied":
            s.add((int(r["x"]), int(r["y"])))
            continue
        t_raw = r.get("t")
        if isinstance(t_raw, str) and "asteroidfield" in t_raw.lower().replace("_", ""):
            s.add((int(r["x"]), int(r["y"])))
    return frozenset(s)


def _build_inner_patch_focus_rows(
    recon: ReconstructionDTO,
    interior_cells: tuple[BlueprintCell, ...],
    rows_post_strip: list[dict[str, Any]],
    dominant: str,
    entries: dict[BlueprintCell, dict[str, Any]],
    frame_id: str,
    source_kind: str | None,
) -> list[dict[str, Any]]:
    """Shell terrain + inferred interior void only (preview isolation)."""

    shell = _inner_patch_surface_coords(recon, rows_post_strip)
    interior = frozenset(interior_cells)
    strip_map = _rows_to_cell_dict(rows_post_strip)
    acc: dict[BlueprintCell, dict[str, Any]] = {k: dict(v) for k, v in strip_map.items()}
    coords = sorted(shell | interior, key=lambda c: (c[1], c[0]))
    out: list[dict[str, Any]] = []
    for x, y in coords:
        if (x, y) in interior:
            surf = _neighbor_majority_surface(acc, x, y, dominant)
            body = {
                "x": x,
                "y": y,
                "role": "inferred",
                "surface": surf,
                "layout_kind": "asteroid_field",
            }
            acc[(x, y)] = dict(body)
            out.append(_stamp_row(body, frame_id=frame_id, source_kind=source_kind))
        else:
            src = strip_map.get((x, y))
            if src is not None:
                row = _stamp_row(dict(src), frame_id=frame_id, source_kind=source_kind)
                acc[(x, y)] = dict(src)
            else:
                cell = _occupied_cell_payload(x, y, entries, dominant)
                row = _stamp_row(cell, frame_id=frame_id, source_kind=source_kind)
                acc[(x, y)] = dict(cell)
            out.append(row)
    return out


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
    extractor = frozenset(recon.extractor_cells)
    extension = frozenset(recon.extension_cells)
    full_b = frozenset(recon.full_barrier_cells)
    painted = belt | pipe | shell | extractor | extension
    other_barriers = full_b - painted
    # Match ``blueprint_map_summary._asteroid_envelope_coords``: shell ∪ enclosed interior
    # (including cells occupied by belt/pipe inside a hole — not only ``interior_patch_cells``).
    asteroid_envelope = shell | frozenset(
        _patch_interior.compute_patch_interior_cells(set(shell), perimeter_bridge_steps=1)
    )
    coords = sorted(painted | other_barriers, key=lambda c: (c[1], c[0]))
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
            cell = _occupied_cell_payload(x, y, entries, dominant)
            out.append(_stamp_row(cell, frame_id=frame_id, source_kind=source_kind))
    return out


def _rows_to_cell_dict(rows: list[dict[str, Any]]) -> dict[BlueprintCell, dict[str, Any]]:
    acc: dict[BlueprintCell, dict[str, Any]] = {}
    for r in rows:
        acc[(int(r["x"]), int(r["y"]))] = dict(r)
    return acc


def _dict_to_sorted_rows(cells: dict[BlueprintCell, dict[str, Any]]) -> list[dict[str, Any]]:
    return [dict(cells[k]) for k in sorted(cells.keys(), key=lambda c: (c[1], c[0]))]


def _neighbor_majority_surface(
    cell_map: dict[BlueprintCell, dict[str, Any]],
    x: int,
    y: int,
    fallback: str,
) -> str:
    """Pick ``shape`` / ``fluid`` from orthogonal neighbors; ties fall back to ``fallback``."""

    votes: list[str] = []
    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        r = cell_map.get((x + dx, y + dy))
        if not r:
            continue
        s = r.get("surface")
        if s in ("shape", "fluid"):
            votes.append(str(s))
    if not votes:
        return fallback
    shape_n = sum(1 for v in votes if v == "shape")
    fluid_n = sum(1 for v in votes if v == "fluid")
    if fluid_n > shape_n:
        return "fluid"
    if shape_n > fluid_n:
        return "shape"
    return fallback


def _merge_interior_void(
    base_rows: list[dict[str, Any]],
    interior: tuple[BlueprintCell, ...],
    dominant: str,
    frame_id: str,
    source_kind: str | None,
) -> list[dict[str, Any]]:
    cells = _rows_to_cell_dict(base_rows)
    for x, y in sorted(interior, key=lambda c: (c[1], c[0])):
        if (x, y) not in cells:
            surf = _neighbor_majority_surface(cells, x, y, dominant)
            cells[(x, y)] = _stamp_row(
                {
                    "x": x,
                    "y": y,
                    "role": "inferred",
                    "surface": surf,
                },
                frame_id=frame_id,
                source_kind=source_kind,
            )
    return _dict_to_sorted_rows(cells)


def _preview_interior_supplement(rows: list[dict[str, Any]]) -> frozenset[BlueprintCell]:
    """Void cells enclosed by the **current preview** solid hull (post-strip).

    ``ReconstructionDTO.interior_patch_cells`` uses blueprint asteroid shell only; after
    belt/equipment strip the preview silhouette can close gaps reconstruction did not use,
    leaving visual holes unless patch interior is recomputed on non-``inferred`` rows.
    """

    solid: set[BlueprintCell] = set()
    for r in rows:
        if r.get("role") == "inferred":
            continue
        solid.add((int(r["x"]), int(r["y"])))
    if len(solid) < 4:
        return frozenset()
    return frozenset(_patch_interior.compute_patch_interior_cells(solid, perimeter_bridge_steps=1))


def _combined_interior_tuple(
    recon: ReconstructionDTO,
    rows_post_strip: list[dict[str, Any]],
) -> tuple[BlueprintCell, ...]:
    supp = _preview_interior_supplement(rows_post_strip)
    merged = frozenset(recon.interior_patch_cells) | supp
    return tuple(sorted(merged, key=lambda c: (c[1], c[0])))


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

    Reconstruction preview order: full layout → strip belt/pipe → strip extractors →
    strip extensions → infer interior on stripped base → inner-patch focus (shell + void)
    → mineable highlights. Then placeholder frames for later solver milestones.

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
    belt_f = frozenset(recon.belt_cells)
    pipe_f = frozenset(recon.pipe_cells)
    ext_f = frozenset(recon.extractor_cells)
    exn_f = frozenset(recon.extension_cells)

    frames: list[dict[str, Any]] = []

    fid1 = "v2_recon_transport_shell"
    rows1 = _build_transport_shell_rows(recon, dominant, entries, fid1, source_kind)
    s1 = _summary_from_rows(rows1, frame_id=fid1, source_kind=source_kind)
    frames.append({"id": fid1, "summary": s1, "mining_map": copy.deepcopy(rows1)})
    _dev_log_v2_preview_frame(fid1, entry_count=int(s1["entry_count"]))

    fid_st = "v2_recon_strip_transport"
    rows_st = _rephase_rows(_filter_mining_map_rows(rows1, belt_f | pipe_f), fid_st, source_kind)
    s_st = _summary_from_rows(rows_st, frame_id=fid_st, source_kind=source_kind)
    frames.append({"id": fid_st, "summary": s_st, "mining_map": copy.deepcopy(rows_st)})
    _dev_log_v2_preview_frame(fid_st, entry_count=int(s_st["entry_count"]))

    fid_se = "v2_recon_strip_extractors"
    ext_targets = _preview_strip_targets_for_styles(
        rows_st, ext_f, entries, _PREVIEW_EXTRACTOR_STYLES
    )
    rows_se = _strip_rows_replace_coords_with_asteroid_field(
        rows_st, ext_targets, entries, dominant, fid_se, source_kind
    )
    s_se = _summary_from_rows(rows_se, frame_id=fid_se, source_kind=source_kind)
    frames.append({"id": fid_se, "summary": s_se, "mining_map": copy.deepcopy(rows_se)})
    _dev_log_v2_preview_frame(fid_se, entry_count=int(s_se["entry_count"]))

    fid_sx = "v2_recon_strip_extensions"
    exn_targets = _preview_strip_targets_for_styles(
        rows_se, exn_f, entries, _PREVIEW_EXTENSION_STYLES
    )
    rows_sx = _strip_rows_replace_coords_with_asteroid_field(
        rows_se, exn_targets, entries, dominant, fid_sx, source_kind
    )
    s_sx = _summary_from_rows(rows_sx, frame_id=fid_sx, source_kind=source_kind)
    frames.append({"id": fid_sx, "summary": s_sx, "mining_map": copy.deepcopy(rows_sx)})
    _dev_log_v2_preview_frame(fid_sx, entry_count=int(s_sx["entry_count"]))

    fid2 = "v2_recon_interior_void"
    combined_interior = _combined_interior_tuple(recon, rows_sx)
    rows2 = _merge_interior_void(rows_sx, combined_interior, dominant, fid2, source_kind)
    s2 = _summary_from_rows(rows2, frame_id=fid2, source_kind=source_kind)
    frames.append({"id": fid2, "summary": s2, "mining_map": copy.deepcopy(rows2)})
    _dev_log_v2_preview_frame(fid2, entry_count=int(s2["entry_count"]))

    fid_ip = "v2_recon_inner_patch"
    rows_ip = _build_inner_patch_focus_rows(
        recon,
        combined_interior,
        rows_sx,
        dominant,
        entries,
        fid_ip,
        source_kind,
    )
    s_ip = _summary_from_rows(rows_ip, frame_id=fid_ip, source_kind=source_kind)
    frames.append({"id": fid_ip, "summary": s_ip, "mining_map": copy.deepcopy(rows_ip)})
    _dev_log_v2_preview_frame(fid_ip, entry_count=int(s_ip["entry_count"]))

    fid3 = "v2_recon_mineable"
    mineable_f = frozenset(recon.mineable_placement_cells)
    rows3 = _apply_mineable_highlights(rows_ip, mineable_f, fid3, source_kind)
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

__all__ = [
    "PREVIEW_ASTEROID_REPLACE_TILE_T",
    "V2_PREVIEW_PLACEHOLDER_STEP_IDS",
    "build_v2_preview_map_frames",
]
