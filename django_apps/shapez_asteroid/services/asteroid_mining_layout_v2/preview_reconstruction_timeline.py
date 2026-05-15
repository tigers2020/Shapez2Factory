"""
v2 copy-preview: ``map_timeline`` frames (display-only).

Reconstruction milestones plus STEP 2 Pass1 replay (one frame per placement event).
When Pass1 seals the perimeter, an extra ``v2_pass1_corridor_gate`` frame may run the
same ``maybe_open_corridors_before_pass2`` gate as Pass2 (display-only).
Each frame is one **full** ``mining_map`` row list (no delta). Does not read NDJSON,
``solver_replay``, or ``solver_summary``. Domain modules must not import this package.
"""

from __future__ import annotations

import copy
import logging
import os
from dataclasses import dataclass
from typing import Any, cast

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import (
    rotation_r_for_output_direction,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.coord import (
    BlueprintCell,
    is_physical_x,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.dto import (
    Pass1Result,
    ReconstructionDTO,
    SolverRunContext,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.enums import (
    TransportKind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.domain.grid import (
    step_blueprint_cell,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement import (
    corridor_opening,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement.pass1_outer import (
    run_pass1_outer_placement,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction import (
    asteroid_reconstruction as _ar,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.reconstruction import (
    patch_interior as _patch_interior,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.runtime.trace_collector import (
    TraceCollector,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.serialization import to_jsonable
from django_apps.shapez_asteroid.services.blueprint_entry_parsing import int_or_none as _int_or_none
from django_apps.shapez_asteroid.services.style_classifier import (
    PlotStyle,
    classify_layout_type,
    is_extraction_style,
    mining_surface_from_layout,
)

logger = logging.getLogger(__name__)


def _type_field_to_str(t_raw: Any) -> str | None:
    """Normalize blueprint ``T``: keep ``str``, else ``str()`` if not ``None``, else ``None``."""

    if isinstance(t_raw, str):
        return t_raw
    if t_raw is not None:
        return str(t_raw)
    return None


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
        t_str = _type_field_to_str(t_raw)
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
# Pass1 replay frames are inserted dynamically after ``v2_recon_mineable`` (STEP 2).
_V2_PREVIEW_PLACEHOLDER_FRAME_IDS: tuple[str, ...] = (
    "v2_pass2_candidates",
    "v2_pass2_provisional",
    "v2_step4_trunk_seed",
    "v2_step4_routing",
    "v2_final_validation",
    "v2_final_layout",
)


def _blueprint_cell_xy_from_entry(item: dict[str, Any]) -> BlueprintCell | None:
    x_val = _int_or_none(item.get("X"))
    if x_val is None or x_val == 0:
        return None
    y_val = _int_or_none(item.get("Y"))
    if y_val is None:
        y_val = 0
    return (x_val, y_val)


def _recon_shell_surface_hint_coords(recon: ReconstructionDTO) -> frozenset[BlueprintCell]:
    return (
        frozenset(recon.extraction_shell_cells)
        | frozenset(recon.extractor_cells)
        | frozenset(recon.extension_cells)
    )


def _dominant_surface_from_layout_hints(hints: list[str]) -> str:
    if "fluid" in hints:
        return "fluid"
    if "shape" in hints:
        return "shape"
    return "shape"


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

    hint_coords = _recon_shell_surface_hint_coords(recon)
    hints: list[str] = []
    for item in _ar.gather_bp_entries_recursive(decoded):
        xy = _blueprint_cell_xy_from_entry(item)
        if xy is None or xy not in hint_coords:
            continue
        t_str = _type_field_to_str(item.get("T"))
        h = mining_surface_from_layout(t_str)
        if h:
            hints.append(h)
    return _dominant_surface_from_layout_hints(hints)


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
        t_str = _type_field_to_str(item.get("T"))
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
        t_str = _type_field_to_str(t_raw)
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
    for d in ((0, 1), (0, -1), (1, 0), (-1, 0)):
        nx, ny = step_blueprint_cell((x, y), d)
        r = cell_map.get((nx, ny))
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

    STEP 1 now infers interiors from the same transport-stripped hull as this preview;
    this pass remains a defensive merge so timeline frames never show inferred voids
    absent from ``ReconstructionDTO.interior_patch_cells``.
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
    """Stamp mineable phase; promote inferred rows in ``mineable`` to confirmed field."""

    cells = _rows_to_cell_dict(rows)
    for x, y in mineable:
        key = (x, y)
        if key not in cells:
            continue
        r = dict(cells[key])
        if r.get("role") == "inferred":
            r["role"] = "mineable"
            r["layout_kind"] = "asteroid_field"
            surf = r.get("surface")
            if surf not in ("shape", "fluid"):
                r["surface"] = "shape"
        r["phase"] = frame_id
        if source_kind:
            r["source_kind"] = source_kind
        cells[key] = r
    return _dict_to_sorted_rows(cells)


def _pass1_overlay_cell_row(
    x: int,
    y: int,
    *,
    pass1_role: str,
    frame_id: str,
    source_kind: str | None,
    dominant: str,
    base_row: dict[str, Any] | None,
) -> dict[str, Any]:
    if base_row is not None:
        body = dict(base_row)
    else:
        body = {"x": x, "y": y, "role": "occupied", "surface": dominant}
    body["pass1_replay_role"] = pass1_role
    return _stamp_row(body, frame_id=frame_id, source_kind=source_kind)


def _coord_from_jsonish(t: object) -> BlueprintCell:
    if isinstance(t, (list, tuple)) and len(t) == 2:
        return (int(t[0]), int(t[1]))
    msg = f"expected [x,y] pair, got {type(t).__name__}"
    raise TypeError(msg)


def _output_direction_from_bundle(b: dict[str, Any]) -> tuple[int, int]:
    od = b.get("output_direction")
    if isinstance(od, (list, tuple)) and len(od) == 2:
        return (int(od[0]), int(od[1]))
    extr = _coord_from_jsonish(b["extractor_cell"])
    stub = _coord_from_jsonish(b["output_stub_cell"])
    return (stub[0] - extr[0], stub[1] - extr[1])


def _transport_kind_from_bundle_dict(b: dict[str, Any]) -> TransportKind:
    if b.get("transport_kind") == TransportKind.FLUID_PIPE.value:
        return TransportKind.FLUID_PIPE
    return TransportKind.SHAPE_BELT


def _pass1_committed_output_stub_transport_row(
    stub: BlueprintCell,
    *,
    bundle: dict[str, Any],
    frame_id: str,
    source_kind: str | None,
    dominant: str,
    base_row: dict[str, Any] | None,
) -> dict[str, Any] | None:
    """mining_map row for the extractor output stub (belt or pipe) before extension bodies.

    Preview-only: paints ``output_stub_cell`` as transport so the UI can connect the
    miner head to belt/pipe before extension sprites on the other sides.
    """

    if not is_physical_x(stub[0]):
        return None
    tk = _transport_kind_from_bundle_dict(bundle)
    out_dir = _output_direction_from_bundle(bundle)
    try:
        r_val = rotation_r_for_output_direction(out_dir[0], out_dir[1])
    except ValueError:
        r_val = 0
    if tk is TransportKind.FLUID_PIPE:
        role = "pipe"
        surface = "fluid"
    else:
        role = "belt"
        surface = dominant if dominant in ("shape", "fluid") else "shape"
    if base_row is not None:
        body = dict(base_row)
    else:
        body = {"x": stub[0], "y": stub[1], "role": role, "surface": surface}
    body["x"] = stub[0]
    body["y"] = stub[1]
    body["role"] = role
    body["surface"] = surface
    body["r"] = r_val
    body.pop("pass1_replay_role", None)
    body.pop("layout_kind", None)
    body.pop("t", None)
    return _stamp_row(body, frame_id=frame_id, source_kind=source_kind)


def _pass1_extension_orientation_dirs(
    extractor: BlueprintCell,
    extension_cells_json: Any,
) -> tuple[tuple[int, int], ...]:
    """Replay lists extensions in commit order; parent is always in ``{extractor} ∪ prior``.

    Matches Pass1 ``grow_pass1_straight_extension_chain`` / Pass2 branching emission order
    (``PlacementBundle.extensions`` list order).
    """

    from django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.placement import (
        bundle_candidate as _bc,
    )

    seq = tuple(_coord_from_jsonish(x) for x in extension_cells_json or ())
    placed: set[BlueprintCell] = {extractor}
    out_dirs: list[tuple[int, int]] = []
    for eco in seq:
        parents = [p for p in placed if any(_bc.step_cell(p, d) == eco for d in _bc.CARDINAL_DIRS)]
        if not parents:
            logger.warning("pass1 replay extension has no parent in placed set eco=%s", eco)
            out_dirs.append((0, -1))
            placed.add(eco)
            continue
        if len(parents) != 1:
            logger.warning(
                "pass1 replay extension parent ambiguous eco=%s parents=%s",
                eco,
                parents,
            )
            par = min(parents, key=lambda c: (c[1], c[0]))
        else:
            par = parents[0]
        out_dirs.append(_bc.orientation_toward_parent(eco, par))
        placed.add(eco)
    return tuple(out_dirs)


def _pass1_committed_extension_mining_row(
    eco: BlueprintCell,
    *,
    bundle: dict[str, Any],
    orientation_toward_parent_dir: tuple[int, int],
    pass1_role: str,
    frame_id: str,
    source_kind: str | None,
    base_row: dict[str, Any] | None,
) -> dict[str, Any]:
    """mining_map row for Pass1 extension body (decoded-map compatible for UI ``renderPlot``)."""

    tk = _transport_kind_from_bundle_dict(bundle)
    if tk is TransportKind.FLUID_PIPE:
        surface = "fluid"
        layout_kind = "fluid_extension"
        t_str = "Layout_FluidMinerExtension"
    else:
        surface = "shape"
        layout_kind = "extension"
        t_str = "Layout_ShapeMinerExtension"
    try:
        r_val = rotation_r_for_output_direction(
            orientation_toward_parent_dir[0],
            orientation_toward_parent_dir[1],
        )
    except ValueError:
        r_val = 0
    if base_row is not None:
        body = dict(base_row)
    else:
        body = {"x": eco[0], "y": eco[1], "role": "occupied", "surface": surface}
    body["x"] = eco[0]
    body["y"] = eco[1]
    body["role"] = "occupied"
    body["surface"] = surface
    body["layout_kind"] = layout_kind
    body["r"] = r_val
    body["t"] = t_str
    body["pass1_replay_role"] = pass1_role
    return _stamp_row(body, frame_id=frame_id, source_kind=source_kind)


def _pass1_committed_extractor_mining_row(
    extr: BlueprintCell,
    *,
    bundle: dict[str, Any],
    pass1_role: str,
    frame_id: str,
    source_kind: str | None,
    base_row: dict[str, Any] | None,
) -> dict[str, Any]:
    """mining_map row for Pass1 extractor body (decoded-map compatible for UI ``renderPlot``)."""

    tk = _transport_kind_from_bundle_dict(bundle)
    if tk is TransportKind.FLUID_PIPE:
        surface = "fluid"
        layout_kind = "fluid_miner"
        t_str = "Layout_FluidMiner"
    else:
        surface = "shape"
        layout_kind = "miner"
        t_str = "Layout_ShapeMiner"
    out_dir = _output_direction_from_bundle(bundle)
    try:
        r_val = rotation_r_for_output_direction(out_dir[0], out_dir[1])
    except ValueError:
        r_val = 0
    if base_row is not None:
        body = dict(base_row)
    else:
        body = {"x": extr[0], "y": extr[1], "role": "occupied", "surface": surface}
    body["x"] = extr[0]
    body["y"] = extr[1]
    body["role"] = "occupied"
    body["surface"] = surface
    body["layout_kind"] = layout_kind
    body["r"] = r_val
    body["t"] = t_str
    body["pass1_replay_role"] = pass1_role
    return _stamp_row(body, frame_id=frame_id, source_kind=source_kind)


def _mining_map_with_pass1_replay_overlay(
    mineable_rows: list[dict[str, Any]],
    *,
    frame_id: str,
    source_kind: str | None,
    dominant: str,
    committed_bundles: list[dict[str, Any]],
    highlight_event: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    cells = _rows_to_cell_dict(copy.deepcopy(mineable_rows))

    for bi, b in enumerate(committed_bundles):
        extr = _coord_from_jsonish(b["extractor_cell"])
        prev_e = cells.get(extr)
        cells[extr] = _pass1_committed_extractor_mining_row(
            extr,
            bundle=b,
            pass1_role=f"pass1_extractor_{bi}",
            frame_id=frame_id,
            source_kind=source_kind,
            base_row=prev_e,
        )
        stub = _coord_from_jsonish(b["output_stub_cell"])
        prev_stub = cells.get(stub)
        stub_row = _pass1_committed_output_stub_transport_row(
            stub,
            bundle=b,
            frame_id=frame_id,
            source_kind=source_kind,
            dominant=dominant,
            base_row=prev_stub,
        )
        if stub_row is not None:
            cells[stub] = stub_row
        orient_dirs = _pass1_extension_orientation_dirs(extr, b.get("extension_cells", ()))
        for j, ex in enumerate(b.get("extension_cells", ())):
            eco = _coord_from_jsonish(ex)
            prev = cells.get(eco)
            odir = orient_dirs[j] if j < len(orient_dirs) else (0, -1)
            cells[eco] = _pass1_committed_extension_mining_row(
                eco,
                bundle=b,
                orientation_toward_parent_dir=odir,
                pass1_role=f"pass1_extension_{bi}_{j}",
                frame_id=frame_id,
                source_kind=source_kind,
                base_row=prev,
            )

    if highlight_event is not None:
        kind = highlight_event.get("kind")
        if kind == "consider_extract":
            c = _coord_from_jsonish(highlight_event["extractor_cell"])
            prev = cells.get(c)
            cells[c] = _pass1_overlay_cell_row(
                c[0],
                c[1],
                pass1_role="pass1_scan_cursor",
                frame_id=frame_id,
                source_kind=source_kind,
                dominant=dominant,
                base_row=prev,
            )
        elif kind == "probe_output":
            c = _coord_from_jsonish(highlight_event["output_stub_cell"])
            prev = cells.get(c)
            role = (
                "pass1_probe_stub_ok"
                if highlight_event.get("reject_reason") is None
                else "pass1_probe_stub_reject"
            )
            cells[c] = _pass1_overlay_cell_row(
                c[0],
                c[1],
                pass1_role=role,
                frame_id=frame_id,
                source_kind=source_kind,
                dominant=dominant,
                base_row=prev,
            )

    return _dict_to_sorted_rows(cells)


# Above this count, each timeline frame triggers a browser ``loadCellsForSummary`` round-trip
# (map-cells fetch storm + UI jank). Keep full probe/consider animation only for small runs.
_PASS1_PREVIEW_FULL_EVENT_BUDGET = 72


def _committed_bundle_dicts_from_pass1(p1: Pass1Result) -> list[dict[str, Any]]:
    """Replay-overlay dicts aligned with ``commit_bundle`` replay rows."""

    out: list[dict[str, Any]] = []
    for b in p1.placements:
        extr = b.extractor.cell
        stub = b.output_stub.cell
        out_dir = (stub[0] - extr[0], stub[1] - extr[1])
        out.append(
            {
                "extractor_cell": [extr[0], extr[1]],
                "output_stub_cell": [stub[0], stub[1]],
                "extension_cells": [[e.cell[0], e.cell[1]] for e in b.extensions],
                "transport_kind": str(b.extractor.transport_kind.value),
                "output_direction": [out_dir[0], out_dir[1]],
            }
        )
    return out


def _pass1_events_for_preview_timeline(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if len(events) <= _PASS1_PREVIEW_FULL_EVENT_BUDGET:
        return list(events)
    return [e for e in events if e.get("kind") in ("pass1_begin", "commit_bundle")]


@dataclass(frozen=True, slots=True)
class Pass1PreviewArtifacts:
    """UI ``mining_map`` frames plus full Pass1 replay events from one Pass1 run."""

    frames: list[dict[str, Any]]
    pass1_replay_events: tuple[dict[str, Any], ...]
    pass1_result: Pass1Result


@dataclass(frozen=True, slots=True)
class V2PreviewTimelineResult:
    """JSON-safe preview frames for ``map_timeline`` and uncapped Pass1 replay events."""

    frames: list[dict[str, Any]]
    pass1_replay_events: tuple[dict[str, Any], ...]


def expand_pass1_replay_mining_map_frames(
    recon: ReconstructionDTO,
    mineable_rows: list[dict[str, Any]],
    *,
    dominant: str,
    source_kind: str | None,
    trace: TraceCollector,
) -> Pass1PreviewArtifacts:
    """STEP 2 Pass1: ``mining_map`` frames for copy-preview ``map_timeline``.

    One frame per replay event for small runs; for larger event streams only ``pass1_begin``
    and ``commit_bundle`` rows are expanded so the UI does not issue hundreds of identical
    ``/api/asteroid/map-cells/`` requests during playback.

    When ``reconstruction.mineable_placement_cells`` is empty, Pass1 emits no replay rows; a
    single ``v2_pass1_skipped_no_mineable`` frame is returned so the timeline length matches
    expectations (reconstruction + explicit Pass1 outcome + placeholders).

    ``pass1_replay_events`` is the uncapped list from the same single Pass1 run (for
    development-only behavior artifacts); UI frames may be thinned.
    """

    events: list[dict[str, Any]] = []
    ctx = SolverRunContext(run_id="v2_preview_recon_timeline", reconstruction=recon)
    pass1_result = run_pass1_outer_placement(
        ctx,
        recon,
        replay_events=events,
        replay_event_cap=None,
        trace=trace,
    )

    timeline_events = _pass1_events_for_preview_timeline(events)
    preview_thinned = len(events) > _PASS1_PREVIEW_FULL_EVENT_BUDGET

    if not timeline_events:
        # ``run_pass1_outer_placement`` records nothing when ``mineable_placement_cells`` is
        # empty (early return before ``pass1_begin``). Still emit one UI frame so copy-preview
        # does not look like a broken ``map_timeline`` wire (7 recon + 6 placeholders only).
        fid = "v2_pass1_skipped_no_mineable"
        rows = _mining_map_with_pass1_replay_overlay(
            mineable_rows,
            frame_id=fid,
            source_kind=source_kind,
            dominant=dominant,
            committed_bundles=[],
            highlight_event=None,
        )
        summ = _summary_from_rows(rows, frame_id=fid, source_kind=source_kind)
        summ["pass1_replay"] = True
        summ["pass1_event_kind"] = "skipped_no_mineable"
        summ["pass1_preview_thinned"] = preview_thinned
        summ["preview_placeholder"] = False
        summ["pass1_skip_reason"] = "no_mineable_placement_cells"
        out0: list[dict[str, Any]] = [{"id": fid, "summary": summ, "mining_map": rows}]
        _dev_log_v2_preview_frame(fid, entry_count=int(summ["entry_count"]))
        return Pass1PreviewArtifacts(out0, tuple(dict(e) for e in events), Pass1Result())

    committed: list[dict[str, Any]] = []
    out: list[dict[str, Any]] = []
    for step_i, ev in enumerate(timeline_events):
        kind = ev.get("kind")
        highlight = ev if kind in ("consider_extract", "probe_output") else None

        bundles_for_paint = list(committed)
        if kind == "commit_bundle":
            bundles_for_paint.append(
                {
                    "extractor_cell": ev["extractor_cell"],
                    "output_stub_cell": ev["output_stub_cell"],
                    "extension_cells": list(ev.get("extension_cells", ())),
                    "transport_kind": ev.get("transport_kind"),
                    "output_direction": ev.get("output_direction"),
                }
            )

        fid = f"v2_pass1_replay_{step_i:04d}_{kind or 'ev'}"
        if kind == "pass1_begin":
            fid = "v2_pass1_candidates"

        rows = _mining_map_with_pass1_replay_overlay(
            mineable_rows,
            frame_id=fid,
            source_kind=source_kind,
            dominant=dominant,
            committed_bundles=bundles_for_paint,
            highlight_event=highlight,
        )
        summ = _summary_from_rows(rows, frame_id=fid, source_kind=source_kind)
        summ["pass1_replay"] = True
        summ["pass1_event_kind"] = str(kind)
        summ["pass1_preview_thinned"] = preview_thinned
        summ["preview_placeholder"] = False
        out.append({"id": fid, "summary": summ, "mining_map": rows})
        _dev_log_v2_preview_frame(fid, entry_count=int(summ["entry_count"]))

        if kind == "commit_bundle":
            committed.append(
                {
                    "extractor_cell": ev["extractor_cell"],
                    "output_stub_cell": ev["output_stub_cell"],
                    "extension_cells": list(ev.get("extension_cells", ())),
                    "transport_kind": ev.get("transport_kind"),
                    "output_direction": ev.get("output_direction"),
                }
            )

    if committed:
        fid = "v2_pass1_provisional"
        rows = _mining_map_with_pass1_replay_overlay(
            mineable_rows,
            frame_id=fid,
            source_kind=source_kind,
            dominant=dominant,
            committed_bundles=committed,
            highlight_event=None,
        )
        summ = _summary_from_rows(rows, frame_id=fid, source_kind=source_kind)
        summ["pass1_replay"] = True
        summ["pass1_event_kind"] = "pass1_provisional_final"
        summ["pass1_preview_thinned"] = preview_thinned
        summ["preview_placeholder"] = False
        out.append({"id": fid, "summary": summ, "mining_map": rows})
        _dev_log_v2_preview_frame(fid, entry_count=int(summ["entry_count"]))

    return Pass1PreviewArtifacts(out, tuple(dict(e) for e in events), pass1_result)


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


def _v2_preview_timeline_when_empty_barrier(*, source_kind: str | None) -> V2PreviewTimelineResult:
    _ = source_kind
    return V2PreviewTimelineResult(
        [],
        (),
    )


def _v2_preview_build_pre_pass1_reconstruction_frames(
    decoded: dict[str, Any],
    recon: ReconstructionDTO,
    *,
    source_kind: str | None,
) -> tuple[list[dict[str, Any]], str, list[dict[str, Any]]]:
    """Reconstruction through mineable highlights; returns ``(frames, dominant, rows3)``."""

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

    return frames, dominant, rows3


def _v2_preview_append_tail_placeholder_frames(
    frames: list[dict[str, Any]],
    *,
    source_kind: str | None,
    baseline_mining_map: list[dict[str, Any]] | None = None,
) -> None:
    last_rows_raw = (
        baseline_mining_map if baseline_mining_map is not None else frames[-1]["mining_map"]
    )
    last_rows: list[dict[str, Any]] = last_rows_raw if isinstance(last_rows_raw, list) else []
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


def build_v2_preview_map_frames(
    decoded: dict[str, Any],
    recon: ReconstructionDTO,
    *,
    source_kind: str | None = None,
    trace: TraceCollector,
) -> V2PreviewTimelineResult:
    """
    Return JSON-safe ``map_timeline`` frames (variable length) and uncapped Pass1 replay
    events from a **single** Pass1 execution.

    After Pass1 provisional, may append ``v2_pass1_corridor_gate`` when the Pass2
    pre-gate removes bundles (same logic as ``maybe_open_corridors_before_pass2``).

    Reconstruction preview order: full layout → strip belt/pipe → strip extractors →
    strip extensions → infer interior on stripped base → inner-patch focus (shell + void)
    → mineable highlights. Then STEP 2 Pass1 replay frames (variable count), then
    placeholder frames for later solver milestones.

    Appends one row per ``_V2_PREVIEW_PLACEHOLDER_FRAME_IDS`` (display-only; each uses the
    same ``mining_map`` raster as the last Pass1 frame, or after ``v2_pass1_corridor_gate``
    when that frame was emitted).

    When reconstruction is empty (no barrier cells), returns **only** those placeholder
    frames (empty ``mining_map`` each).
    """

    if not recon.full_barrier_cells:
        _ = trace
        return _v2_preview_timeline_when_empty_barrier(source_kind=source_kind)

    frames, dominant, rows3 = _v2_preview_build_pre_pass1_reconstruction_frames(
        decoded, recon, source_kind=source_kind
    )

    pass1_art = expand_pass1_replay_mining_map_frames(
        recon,
        rows3,
        dominant=dominant,
        source_kind=source_kind,
        trace=trace,
    )
    frames.extend(pass1_art.frames)
    pass1_replay_events = pass1_art.pass1_replay_events

    placeholder_baseline: list[dict[str, Any]] | None = None
    p1_res = pass1_art.pass1_result
    if p1_res.placements:
        ctx_gate = SolverRunContext(
            run_id="v2_preview_corridor_gate",
            reconstruction=recon,
            placement_commit_by_id=dict(p1_res.placement_commit_entries),
        )
        p1_after, _ctx_after, corridor_trace = corridor_opening.maybe_open_corridors_before_pass2(
            ctx=ctx_gate, pass1=p1_res
        )
        if corridor_trace:
            gate_rows = _mining_map_with_pass1_replay_overlay(
                copy.deepcopy(rows3),
                frame_id="v2_pass1_corridor_gate",
                source_kind=source_kind,
                dominant=dominant,
                committed_bundles=_committed_bundle_dicts_from_pass1(p1_after),
                highlight_event=None,
            )
            summ_gate = _summary_from_rows(
                gate_rows, frame_id="v2_pass1_corridor_gate", source_kind=source_kind
            )
            summ_gate["pass1_replay"] = True
            summ_gate["pass1_event_kind"] = "corridor_gate"
            summ_gate["preview_placeholder"] = False
            summ_gate["corridor_opening_trace"] = to_jsonable(list(corridor_trace))
            frames.append(
                {"id": "v2_pass1_corridor_gate", "summary": summ_gate, "mining_map": gate_rows}
            )
            placeholder_baseline = gate_rows

    _ = placeholder_baseline

    return V2PreviewTimelineResult(
        cast(list[dict[str, Any]], to_jsonable(frames)),
        pass1_replay_events,
    )


V2_PREVIEW_PLACEHOLDER_STEP_IDS: tuple[str, ...] = _V2_PREVIEW_PLACEHOLDER_FRAME_IDS

__all__ = [
    "PREVIEW_ASTEROID_REPLACE_TILE_T",
    "V2_PREVIEW_PLACEHOLDER_STEP_IDS",
    "Pass1PreviewArtifacts",
    "V2PreviewTimelineResult",
    "build_v2_preview_map_frames",
    "expand_pass1_replay_mining_map_frames",
]
