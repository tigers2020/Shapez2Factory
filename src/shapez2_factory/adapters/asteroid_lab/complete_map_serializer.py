"""Deterministic ``ReconstructionCompleteMap`` <-> JSON dict serializer (pure, no Django).

Produces the body of ``output/complete_map.json`` for the CLI-first artifact contract (§2 of
``documents/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md``). Coordinate sets
are sorted so the payload is byte-stable; ``cells`` preserves the terrain SoT order produced by
``build_reconstruction_complete_map``. The artifact shell (PR-CLI-3a) owns file placement + hashing.
"""

from __future__ import annotations

from shapez2_factory.domain.asteroid_lab.coord_frames import CoordFrame
from shapez2_factory.domain.asteroid_lab.decoded_cell import DecodedCellDTO
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)
from shapez2_factory.domain.asteroid_lab.wire_coerce import (
    wire_dict,
    wire_int,
    wire_list,
    wire_str,
)

COMPLETE_MAP_SCHEMA_VERSION = "complete_map_v1"


def _cell_to_dict(cell: DecodedCellDTO) -> dict[str, object]:
    return {
        "x": cell.x,
        "y": cell.y,
        "layer": cell.layer,
        "rotation": cell.rotation,
        "tile_type": cell.tile_type,
        "cell_kind": cell.cell_kind,
        "transport_kind": cell.transport_kind,
        "has_nested_blueprint": cell.has_nested_blueprint,
        "nested_entry_count": cell.nested_entry_count,
        "nested_type_counts_json": dict(cell.nested_type_counts_json),
        "raw_entry_json": dict(cell.raw_entry_json),
    }


def _cell_from_dict(data: dict[str, object]) -> DecodedCellDTO:
    layer_raw = data.get("layer")
    layer: int | None = None if layer_raw is None else wire_int(layer_raw)
    nested_type_counts = wire_dict(data.get("nested_type_counts_json", {}))
    raw_entry = wire_dict(data.get("raw_entry_json", {}))
    return DecodedCellDTO(
        x=wire_int(data["x"]),
        y=wire_int(data["y"]),
        layer=layer,
        rotation=wire_int(data["rotation"]),
        tile_type=wire_str(data["tile_type"]),
        cell_kind=wire_str(data["cell_kind"]),
        transport_kind=wire_str(data["transport_kind"]),
        has_nested_blueprint=bool(data["has_nested_blueprint"]),
        nested_entry_count=wire_int(data["nested_entry_count"]),
        nested_type_counts_json={wire_str(k): wire_int(v) for k, v in nested_type_counts.items()},
        raw_entry_json=raw_entry,
    )


def _sorted_coords(coords: frozenset[Coord]) -> list[list[int]]:
    return [[x, y] for (x, y) in sorted(coords)]


def _coords_from_payload(items: object) -> frozenset[Coord]:
    rows = wire_list(items, field="coords")
    out: list[Coord] = []
    for pair in rows:
        if not isinstance(pair, (list, tuple)) or len(pair) < 2:
            continue
        out.append((wire_int(pair[0]), wire_int(pair[1])))
    return frozenset(out)


def serialize_complete_map(complete_map: ReconstructionCompleteMap) -> dict[str, object]:
    """Render a ``ReconstructionCompleteMap`` to a deterministic JSON-ready dict."""

    return {
        "schema_version": COMPLETE_MAP_SCHEMA_VERSION,
        "coord_frame": complete_map.coord_frame.value,
        "shape_field_cell_count": complete_map.shape_field_cell_count,
        "fluid_field_cell_count": complete_map.fluid_field_cell_count,
        "field_cells": _sorted_coords(complete_map.field_cells),
        "external_void_cells": _sorted_coords(complete_map.external_void_cells),
        "cells": [_cell_to_dict(cell) for cell in complete_map.cells],
    }


def parse_complete_map(payload: dict[str, object]) -> ReconstructionCompleteMap:
    """Parse a serialized payload back into a ``ReconstructionCompleteMap``."""

    schema = payload.get("schema_version")
    if schema != COMPLETE_MAP_SCHEMA_VERSION:
        msg = f"unexpected complete_map schema_version: {schema!r}"
        raise ValueError(msg)
    cells_raw = wire_list(payload["cells"], field="cells")
    return ReconstructionCompleteMap(
        cells=tuple(_cell_from_dict(wire_dict(cell, field="cell")) for cell in cells_raw),
        field_cells=_coords_from_payload(payload["field_cells"]),
        shape_field_cell_count=wire_int(payload["shape_field_cell_count"]),
        fluid_field_cell_count=wire_int(payload["fluid_field_cell_count"]),
        external_void_cells=_coords_from_payload(payload["external_void_cells"]),
        coord_frame=CoordFrame(wire_str(payload["coord_frame"])),
    )


__all__ = [
    "COMPLETE_MAP_SCHEMA_VERSION",
    "parse_complete_map",
    "serialize_complete_map",
]
