"""ORM / snapshot → ``SpaceTransportTileCatalog`` payload builders."""

from __future__ import annotations

import hashlib
import json

from django_apps.game_data.models.space_transport_layout import SpaceTransportLayoutRegistry
from shapez2_factory.adapters.asteroid_lab.space_transport_catalog_snapshot import (
    CURRENT_SCHEMA_VERSION,
)

EXPECTED_SPACE_TRANSPORT_LAYOUT_COUNT = 54
_SOURCE_JSON_PATH = (
    "research_unlocks.json→Mode.Islands.DefinitionsById;"
    "simulation_systems.json→SpecializedIslandTenantSystemsByType"
)


def eswn_string_to_bool_mask(value: str) -> tuple[bool, bool, bool, bool]:
    text = (value or "").strip()
    if len(text) != 4 or any(ch not in "01" for ch in text):
        msg = f"invalid ESWN mask {value!r}"
        raise ValueError(msg)
    return tuple(ch == "1" for ch in text)


def _allowed_rotations_list(raw: str) -> list[int]:
    parts = [part.strip() for part in (raw or "").split(",") if part.strip()]
    if not parts:
        return [0, 1, 2, 3]
    return [int(part) for part in parts]


def _layout_row_to_catalog_entry(row: dict[str, object]) -> dict[str, object]:
    tile_id = str(row.get("tile_id", "")).strip()
    if not tile_id:
        msg = "space_transport_layout row missing tile_id"
        raise ValueError(msg)
    entry: dict[str, object] = {
        "tile_id": tile_id,
        "transport_kind": str(row.get("transport_kind", "")),
        "group_id": str(row.get("group_id", "")),
        "layout_suffix": str(row.get("layout_suffix", "")),
        "canonical_rotation": int(row.get("canonical_rotation", 0)),
        "allowed_rotations": _allowed_rotations_list(str(row.get("allowed_rotations", "0,1,2,3"))),
        "source_json_path": str(row.get("source_json_path", _SOURCE_JSON_PATH)),
        "routing_allowed": bool(row.get("routing_allowed", True)),
    }
    sim_key = row.get("simulation_system_key")
    if isinstance(sim_key, str) and sim_key:
        entry["simulation_system_key"] = sim_key
    if bool(row.get("has_io_signature")):
        input_mask = row.get("input_mask_eswn")
        output_mask = row.get("output_mask_eswn")
        if isinstance(input_mask, str):
            entry["input_mask_eswn"] = list(eswn_string_to_bool_mask(input_mask))
        elif isinstance(input_mask, list):
            entry["input_mask_eswn"] = [bool(v) for v in input_mask]
        if isinstance(output_mask, str):
            entry["output_mask_eswn"] = list(eswn_string_to_bool_mask(output_mask))
        elif isinstance(output_mask, list):
            entry["output_mask_eswn"] = [bool(v) for v in output_mask]
    return entry


def _finalize_catalog_payload(
    *,
    entries: list[dict[str, object]],
    source_batch_id: str,
    game_version: str = "",
) -> dict[str, object]:
    provenance = hashlib.sha256(json.dumps(entries, sort_keys=True).encode()).hexdigest()[:16]
    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "game_version": game_version,
        "generated_at": "",
        "provenance_hash": provenance,
        "source_batch_id": source_batch_id,
        "entries": entries,
    }


def build_space_transport_catalog_payload_from_orm() -> dict[str, object] | None:
    """Return catalog payload from ``SpaceTransportLayoutRegistry``, or None when empty."""

    rows = list(SpaceTransportLayoutRegistry.objects.order_by("source_row_index", "tile_id"))
    if not rows:
        return None
    entries = [_orm_row_to_catalog_entry(row) for row in rows]
    batch_id = f"orm:import_batch:{rows[0].import_batch_id}"
    return _finalize_catalog_payload(entries=entries, source_batch_id=batch_id)


def build_space_transport_catalog_payload_from_snapshot_layouts(
    layouts: list[dict[str, object]],
) -> dict[str, object]:
    if len(layouts) != EXPECTED_SPACE_TRANSPORT_LAYOUT_COUNT:
        msg = (
            f"expected {EXPECTED_SPACE_TRANSPORT_LAYOUT_COUNT} space_transport_layouts, "
            f"got {len(layouts)}"
        )
        raise ValueError(msg)
    entries = [_layout_row_to_catalog_entry(row) for row in layouts]
    return _finalize_catalog_payload(
        entries=entries,
        source_batch_id="snapshot:space_transport_layouts",
    )


def space_transport_layout_snapshot_rows() -> list[dict[str, object]]:
    """ORM rows for ``game_data_snapshot`` export."""

    rows: list[dict[str, object]] = []
    for row in SpaceTransportLayoutRegistry.objects.order_by("source_row_index", "tile_id"):
        item: dict[str, object] = {
            "tile_id": row.tile_id,
            "transport_kind": row.transport_kind,
            "layout_suffix": row.layout_suffix,
            "group_id": row.group_id,
            "simulation_system_key": row.simulation_system_key,
            "simulation_family": row.simulation_family,
            "routing_allowed": row.routing_allowed,
            "has_io_signature": row.has_io_signature,
            "input_mask_eswn": row.input_mask_eswn,
            "output_mask_eswn": row.output_mask_eswn,
            "allowed_rotations": row.allowed_rotations,
        }
        rows.append(item)
    return rows


def _orm_row_to_catalog_entry(row: SpaceTransportLayoutRegistry) -> dict[str, object]:
    return _layout_row_to_catalog_entry(
        {
            "tile_id": row.tile_id,
            "transport_kind": row.transport_kind,
            "group_id": row.group_id,
            "layout_suffix": row.layout_suffix,
            "canonical_rotation": row.canonical_rotation,
            "allowed_rotations": row.allowed_rotations,
            "source_json_path": _SOURCE_JSON_PATH,
            "routing_allowed": row.routing_allowed,
            "simulation_system_key": row.simulation_system_key,
            "has_io_signature": row.has_io_signature,
            "input_mask_eswn": row.input_mask_eswn,
            "output_mask_eswn": row.output_mask_eswn,
        }
    )


__all__ = [
    "EXPECTED_SPACE_TRANSPORT_LAYOUT_COUNT",
    "build_space_transport_catalog_payload_from_orm",
    "build_space_transport_catalog_payload_from_snapshot_layouts",
    "eswn_string_to_bool_mask",
    "space_transport_layout_snapshot_rows",
]
