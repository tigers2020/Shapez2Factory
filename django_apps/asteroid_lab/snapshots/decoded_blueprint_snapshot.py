"""Build :class:`DecodedBlueprintSnapshotDTO` from persisted ``decoded_json`` (pure, ORM-free)."""

from __future__ import annotations

from collections import Counter
from typing import Any

from django_apps.asteroid_lab.observability.boundary_jsonl import emit_boundary_jsonl
from django_apps.asteroid_lab.services.dto import DecodedBlueprintSnapshotDTO, DecodedCellDTO
from django_apps.asteroid_lab.snapshots.cell_classifier import classify_blueprint_entry
from django_apps.asteroid_lab.snapshots.copy_json_coords import entry_island_raw_coord


def _as_int(val: Any) -> int:
    """Coerce blueprint scalars; ``None`` ??``0`` (same as entry ``get('X', 0)`` style).

    **Caveat:** missing ``X`` on a blueprint dict row becomes ``raw_x == 0`` on
    :class:`~django_apps.asteroid_lab.services.dto.DecodedCellDTO`, which is **not** a valid
    asteroid world column (there is no ``x == 0``). Prefer explicit ``X`` in JSON or treat
    ``raw_x == 0`` as a decode/validation signal.
    """

    if val is None:
        return 0
    if isinstance(val, bool):
        return int(val)
    if isinstance(val, int):
        return val
    try:
        return int(val)
    except (TypeError, ValueError):
        return 0


def _nested_b_summary(b: Any) -> tuple[int, dict[str, int], bool]:
    """Summarize ``B.Entries`` only; do not unfold into world cells."""

    if not isinstance(b, dict):
        return (0, {}, False)
    entries = b.get("Entries")
    nested_list: list[Any] = entries if isinstance(entries, list) else []
    counts: Counter[str] = Counter()
    for item in nested_list:
        if not isinstance(item, dict):
            continue
        tt = item.get("T")
        if isinstance(tt, str):
            counts[tt] += 1
        else:
            counts["<non_string_T>"] += 1
    nested_count = len(nested_list)
    type_str = b.get("$type")
    has_nested = nested_count > 0 or (isinstance(type_str, str) and type_str.strip() != "")
    return (nested_count, dict(counts), has_nested)


def _extract_layer(entry: dict[str, Any]) -> int | None:
    if "L" in entry:
        v = entry.get("L")
        if v is None:
            return None
        return _as_int(v)
    if "Layer" in entry:
        v = entry.get("Layer")
        if v is None:
            return None
        return _as_int(v)
    return None


def build_decoded_blueprint_snapshot(
    decoded_json: dict[str, Any],
    *,
    project_id: int | None = None,
    map_input_id: int | None = None,
    boundary_run_id: str | None = None,
) -> DecodedBlueprintSnapshotDTO:
    """Parse top-level ``BP.Entries`` into cell DTOs and aggregate metadata.

    Does not call decode, reconstruction, or solver code. Does not read replay rows.
    Cell ``x``/``y`` are island-local copy JSON coordinates.
    """

    bp = decoded_json.get("BP")
    if not isinstance(bp, dict):
        bp = {}
    entries_raw = bp.get("Entries")
    entries: list[Any] = entries_raw if isinstance(entries_raw, list) else []

    blueprint_type = str(bp.get("$type", "")) if bp.get("$type") is not None else ""
    binary_version = _as_int(decoded_json.get("V"))

    entry_dicts = [e for e in entries if isinstance(e, dict)]

    cells: list[DecodedCellDTO] = []
    xs: list[int] = []
    ys: list[int] = []

    for item in entries:
        if not isinstance(item, dict):
            continue
        island = entry_island_raw_coord(item)
        x, y = island.x, island.y
        xs.append(x)
        ys.append(y)

        t_raw = item.get("T")
        tile_type = str(t_raw) if isinstance(t_raw, str) else ""
        cell_kind, transport_kind = classify_blueprint_entry(tile_type if tile_type else None)

        b = item.get("B")
        nested_count, nested_type_counts, has_nested = _nested_b_summary(b)

        rot = _as_int(item.get("R"))
        layer = _extract_layer(item)

        raw_entry: dict[str, Any] = dict(item)

        cells.append(
            DecodedCellDTO(
                x=x,
                y=y,
                layer=layer,
                rotation=rot,
                tile_type=tile_type,
                cell_kind=cell_kind,
                transport_kind=transport_kind,
                has_nested_blueprint=has_nested,
                nested_entry_count=nested_count,
                nested_type_counts_json=nested_type_counts,
                raw_entry_json=raw_entry,
            )
        )

    if xs and ys:
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        bbox: dict[str, Any] = {
            "min_x": min_x,
            "max_x": max_x,
            "min_y": min_y,
            "max_y": max_y,
            "width": max_x - min_x + 1,
            "height": max_y - min_y + 1,
        }
    else:
        bbox = {
            "min_x": 0,
            "max_x": 0,
            "min_y": 0,
            "max_y": 0,
            "width": 0,
            "height": 0,
        }

    cell_kind_counts: dict[str, int] = {}
    transport_kind_counts: dict[str, int] = {}
    for c in cells:
        cell_kind_counts[c.cell_kind] = cell_kind_counts.get(c.cell_kind, 0) + 1
        transport_kind_counts[c.transport_kind] = transport_kind_counts.get(c.transport_kind, 0) + 1

    summary_src = decoded_json.get("_asteroid_lab_summary")
    summary_json: dict[str, Any] = dict(summary_src) if isinstance(summary_src, dict) else {}

    dto = DecodedBlueprintSnapshotDTO(
        project_id=project_id,
        map_input_id=map_input_id,
        binary_version=binary_version,
        blueprint_type=blueprint_type,
        entry_count=len(entries),
        bbox_json=bbox,
        cell_kind_counts_json=cell_kind_counts,
        transport_kind_counts_json=transport_kind_counts,
        cells=tuple(cells),
        summary_json=summary_json,
    )

    if boundary_run_id:
        emit_boundary_jsonl(
            run_id=boundary_run_id,
            stage="decode",
            boundary="decode.island_raw_cell_resolve",
            data={
                "map_input_id": map_input_id,
                "project_id": project_id,
                "parent_bp_dict_entries": len(entry_dicts),
                "island_xy_cells": len(cells),
                "has_raw_x_zero": any(c.x == 0 for c in cells),
                "cell_kind_counts": dict(cell_kind_counts),
            },
        )

    return dto
