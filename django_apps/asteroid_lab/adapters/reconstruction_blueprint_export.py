"""Reconstructed island: ``asteroid_*_field`` ↔ ``Layout_*MinerExtension`` blueprint I/O."""

from __future__ import annotations

import copy
from dataclasses import replace
from typing import Any

from django_apps.asteroid_lab.adapters.blueprint_canonical_export import (
    OFFICIAL_BINARY_VERSION,
    OFFICIAL_ISLAND_ICON,
)
from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string, encode_copy_string
from django_apps.asteroid_lab.adapters.normalization import normalize_decoded_blueprint
from django_apps.asteroid_lab.reconstruction.evidence import ASTEROID_FIELD_KINDS
from django_apps.asteroid_lab.services.dto import (
    DecodedCellDTO,
    NormalizedBlueprintDTO,
    RawDecodedBlueprintDTO,
)
from django_apps.asteroid_lab.snapshots.cell_classifier import classify_blueprint_entry
from django_apps.asteroid_lab.snapshots.copy_json_coords import entry_island_raw_coord
from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import (
    _as_int,
    _extract_layer,
    _nested_b_summary,
)
from django_apps.asteroid_lab.snapshots.server_coords import (
    attach_server_coords_to_decoded_json,
    map_bbox_dense_and_y,
    server_xy_for_raw_xy,
)
from django_apps.asteroid_lab.snapshots.transport_components import (
    is_transport_tile,
    sort_key_xy_layer,
)

T_SHAPE_FIELD = "Layout_ShapeMinerExtension"
T_FLUID_FIELD = "Layout_FluidMinerExtension"

_RECON_META_KEY = "_asteroid_lab_reconstruction"
_RECON_META_SCHEMA = 1

_KIND_TO_T: dict[str, str] = {
    "asteroid_shape_field": T_SHAPE_FIELD,
    "asteroid_fluid_field": T_FLUID_FIELD,
}

_T_TO_KIND: dict[str, str] = {
    T_SHAPE_FIELD: "asteroid_shape_field",
    T_FLUID_FIELD: "asteroid_fluid_field",
}


def tile_type_for_reconstruction_export(cell: DecodedCellDTO) -> str:
    """Map reconstruction cell to game ``T`` for persisted copy/json (fields → Extension only)."""

    if cell.cell_kind in ASTEROID_FIELD_KINDS:
        mapped = _KIND_TO_T.get(cell.cell_kind)
        if mapped is not None:
            return mapped
    if cell.cell_kind in ("fluid_miner", "fluid_miner_extension"):
        return T_FLUID_FIELD
    if cell.cell_kind in ("shape_miner", "shape_miner_extension"):
        return T_SHAPE_FIELD
    if cell.tile_type in (T_FLUID_FIELD, T_SHAPE_FIELD):
        return cell.tile_type
    if cell.tile_type:
        return cell.tile_type
    return ""


def _remap_cell_to_asteroid_field(cell: DecodedCellDTO) -> DecodedCellDTO | None:
    """Normalize strippable/building tiles to ``asteroid_*_field`` for game field export."""

    if is_transport_tile(cell):
        return None
    if cell.cell_kind in ASTEROID_FIELD_KINDS:
        tt = tile_type_for_reconstruction_export(cell)
        return replace(cell, tile_type=tt)
    if cell.cell_kind in ("fluid_miner", "fluid_miner_extension"):
        return replace(
            cell,
            cell_kind="asteroid_fluid_field",
            tile_type=T_FLUID_FIELD,
            transport_kind="none",
        )
    if cell.cell_kind in ("shape_miner", "shape_miner_extension"):
        return replace(
            cell,
            cell_kind="asteroid_shape_field",
            tile_type=T_SHAPE_FIELD,
            transport_kind="none",
        )
    return None


def cells_for_field_export(cells: tuple[DecodedCellDTO, ...]) -> tuple[DecodedCellDTO, ...]:
    """Field-only cells for ``rebuilt_copy_code`` (Extension ``T``, no belts/pipes/miners)."""

    out: list[DecodedCellDTO] = []
    for cell in cells:
        mapped = _remap_cell_to_asteroid_field(cell)
        if mapped is not None:
            out.append(mapped)
    return tuple(sorted(out, key=sort_key_xy_layer))


def cells_for_field_export_from_decoded_json(
    decoded_json: dict[str, Any],
) -> tuple[DecodedCellDTO, ...]:
    """Import decoded blueprint then keep only asteroid field cells for game paste."""

    return cells_for_field_export(load_reconstruction_cells_from_decoded_json(decoded_json))


def cell_kind_for_reconstruction_import(tile_type: str) -> tuple[str, str]:
    """Return ``(cell_kind, transport_kind)``; Extension ``T`` → asteroid field kinds."""

    if tile_type == T_SHAPE_FIELD:
        return ("asteroid_shape_field", "none")
    if tile_type == T_FLUID_FIELD:
        return ("asteroid_fluid_field", "none")
    return classify_blueprint_entry(tile_type if tile_type else None)


def _entry_dict_from_cell(cell: DecodedCellDTO) -> dict[str, Any]:
    t = tile_type_for_reconstruction_export(cell)
    if not t and cell.raw_entry_json:
        raw_t = cell.raw_entry_json.get("T")
        if isinstance(raw_t, str) and raw_t:
            t = raw_t
    row: dict[str, Any] = {"X": cell.x, "Y": cell.y, "T": t}
    if cell.rotation:
        row["R"] = cell.rotation
    if cell.server_x is not None and cell.server_y is not None:
        row["server_x"] = cell.server_x
        row["server_y"] = cell.server_y
    return row


def _shell_from_source(source_decoded_json: dict[str, Any] | None) -> dict[str, Any]:
    if not source_decoded_json:
        return {
            "V": OFFICIAL_BINARY_VERSION,
            "BP": {
                "$type": "Island",
                "Icon": copy.deepcopy(OFFICIAL_ISLAND_ICON),
                "BinaryVersion": OFFICIAL_BINARY_VERSION,
                "Entries": [],
            },
        }
    root = copy.deepcopy(source_decoded_json)
    bp = root.get("BP")
    if not isinstance(bp, dict):
        bp = {}
        root["BP"] = bp
    if not bp.get("$type"):
        bp["$type"] = "Island"
    if "Icon" not in bp:
        bp["Icon"] = copy.deepcopy(OFFICIAL_ISLAND_ICON)
    if root.get("V") is None:
        root["V"] = OFFICIAL_BINARY_VERSION
    if bp.get("BinaryVersion") is None:
        bp["BinaryVersion"] = _as_int(root.get("V")) or OFFICIAL_BINARY_VERSION
    return root


def build_reconstructed_blueprint_root(
    cells: tuple[DecodedCellDTO, ...],
    *,
    source_decoded_json: dict[str, Any] | None = None,
    map_input_id: int | None = None,
    run_key: str = "",
    summary_json: dict[str, Any] | None = None,
    full_map_server_bbox: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Build lab blueprint root with Extension ``T`` for asteroid field cells."""

    root = _shell_from_source(source_decoded_json)
    bp = root["BP"]
    assert isinstance(bp, dict)
    entries = [_entry_dict_from_cell(c) for c in sorted(cells, key=sort_key_xy_layer)]
    bp["Entries"] = entries
    recon_meta: dict[str, Any] = {
        "schema_version": _RECON_META_SCHEMA,
        "map_input_id": map_input_id,
        "run_key": run_key,
        "field_tile_mapping": "Layout_*MinerExtension",
        "summary_json": dict(summary_json or {}),
    }
    if full_map_server_bbox:
        recon_meta["full_map_server_bbox"] = dict(full_map_server_bbox)
    root[_RECON_META_KEY] = recon_meta
    return root


def build_reconstructed_normalized_dto(
    cells: tuple[DecodedCellDTO, ...],
    *,
    source_decoded_json: dict[str, Any] | None = None,
    map_input_id: int | None = None,
    run_key: str = "",
    summary_json: dict[str, Any] | None = None,
    full_map_server_bbox: dict[str, int] | None = None,
) -> NormalizedBlueprintDTO:
    """Root with summary + server coords attached (persist ``decoded_json``)."""

    root = build_reconstructed_blueprint_root(
        cells,
        source_decoded_json=source_decoded_json,
        map_input_id=map_input_id,
        run_key=run_key,
        summary_json=summary_json,
        full_map_server_bbox=full_map_server_bbox,
    )
    dto = normalize_decoded_blueprint(RawDecodedBlueprintDTO(root=root))
    merged = dict(dto.decoded_json)
    attach_server_coords_to_decoded_json(merged)
    return NormalizedBlueprintDTO(decoded_json=merged)


def encode_reconstructed_copy_string(root: dict[str, Any]) -> str:
    """``SHAPEZ2-4-…`` with trailing ``$`` (game paste convention)."""

    return f"{encode_copy_string(root)}$"


def entries_to_reconstruction_cells(
    entries: list[dict[str, Any]],
) -> tuple[DecodedCellDTO, ...]:
    """Import ``BP.Entries`` with Extension → ``asteroid_*_field`` (not miner_extension)."""

    entry_dicts = [e for e in entries if isinstance(e, dict)]
    bbox_params = map_bbox_dense_and_y(entry_dicts)
    cells: list[DecodedCellDTO] = []

    for item in entries:
        if not isinstance(item, dict):
            continue
        island = entry_island_raw_coord(item)
        x, y = island.x, island.y
        t_raw = item.get("T")
        tile_type = str(t_raw) if isinstance(t_raw, str) else ""
        cell_kind, transport_kind = cell_kind_for_reconstruction_import(tile_type)

        b = item.get("B")
        nested_count, nested_type_counts, has_nested = _nested_b_summary(b)
        rot = _as_int(item.get("R"))
        layer = _extract_layer(item)
        raw_entry: dict[str, Any] = dict(item)

        sx_obj = item.get("server_x")
        sy_obj = item.get("server_y")
        sx: int | None = None
        sy: int | None = None
        if bbox_params is not None:
            sx, sy = server_xy_for_raw_xy(
                x,
                y,
                min_dense_x=bbox_params[0],
                min_raw_y=bbox_params[1],
                has_explicit_raw_x_zero=bbox_params[2],
            )
            if isinstance(sx_obj, int) and isinstance(sy_obj, int):
                sx, sy = sx_obj, sy_obj
        else:
            sx = sx_obj if isinstance(sx_obj, int) else None
            sy = sy_obj if isinstance(sy_obj, int) else None

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
                server_x=sx,
                server_y=sy,
            )
        )

    return tuple(sorted(cells, key=sort_key_xy_layer))


def load_reconstruction_cells_from_decoded_json(
    decoded_json: dict[str, Any],
) -> tuple[DecodedCellDTO, ...]:
    """Load reconstructed island cells from persisted ``decoded_json``."""

    bp = decoded_json.get("BP")
    if not isinstance(bp, dict):
        return ()
    entries_raw = bp.get("Entries")
    entries: list[Any] = entries_raw if isinstance(entries_raw, list) else []
    return entries_to_reconstruction_cells(entries)


def load_reconstruction_cells_from_copy_code(copy_code: str) -> tuple[DecodedCellDTO, ...]:
    """Decode copy string (optional trailing ``$``) and import reconstruction cells."""

    normalized = copy_code.strip().removesuffix("$")
    raw = decode_copy_string(normalized)
    return load_reconstruction_cells_from_decoded_json(raw.root)


def reconstruction_cell_keys(
    cells: tuple[DecodedCellDTO, ...],
) -> frozenset[tuple[int, int, int | None, str]]:
    """Stable set for roundtrip tests: ``(x, y, layer, cell_kind)``."""

    return frozenset((c.x, c.y, c.layer, c.cell_kind) for c in cells)


__all__ = [
    "T_FLUID_FIELD",
    "T_SHAPE_FIELD",
    "cells_for_field_export",
    "cells_for_field_export_from_decoded_json",
    "build_reconstructed_blueprint_root",
    "build_reconstructed_normalized_dto",
    "cell_kind_for_reconstruction_import",
    "encode_reconstructed_copy_string",
    "entries_to_reconstruction_cells",
    "load_reconstruction_cells_from_copy_code",
    "load_reconstruction_cells_from_decoded_json",
    "reconstruction_cell_keys",
    "tile_type_for_reconstruction_export",
]
