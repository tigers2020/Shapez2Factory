"""Deterministic ``ReconstructionCompleteMap`` <-> JSON dict serializer (pure, no Django).

Produces the body of ``output/complete_map.json`` for the CLI-first artifact contract (§2 of
``docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md``). Coordinate sets
are sorted so the payload is byte-stable; ``cells`` preserves the terrain SoT order produced by
``build_reconstruction_complete_map``. The artifact shell (PR-CLI-3a) owns file placement + hashing.
"""

from __future__ import annotations

from collections.abc import Sequence

from shapez2_factory.domain.asteroid_lab.coord_frames import CoordFrame
from shapez2_factory.domain.asteroid_lab.decoded_cell import DecodedCellDTO
from shapez2_factory.domain.asteroid_lab.grid_contract import Coord
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)

COMPLETE_MAP_SCHEMA_VERSION = "complete_map_v1"


def _cell_to_dict(cell: DecodedCellDTO) -> dict[str]:
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


def _cell_from_dict(data: dict[str]) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=int(data["x"]),
        y=int(data["y"]),
        layer=data["layer"],
        rotation=int(data["rotation"]),
        tile_type=str(data["tile_type"]),
        cell_kind=str(data["cell_kind"]),
        transport_kind=str(data["transport_kind"]),
        has_nested_blueprint=bool(data["has_nested_blueprint"]),
        nested_entry_count=int(data["nested_entry_count"]),
        nested_type_counts_json=dict(data["nested_type_counts_json"]),
        raw_entry_json=dict(data["raw_entry_json"]),
    )


def _sorted_coords(coords: frozenset[Coord]) -> list[list[int]]:
    return [[x, y] for (x, y) in sorted(coords)]


def _coords_from_payload(items: Sequence[Sequence[int]]) -> frozenset[Coord]:
    return frozenset((int(pair[0]), int(pair[1])) for pair in items)


def serialize_complete_map(complete_map: ReconstructionCompleteMap) -> dict[str]:
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


def parse_complete_map(payload: dict[str]) -> ReconstructionCompleteMap:
    """Parse a serialized payload back into a ``ReconstructionCompleteMap``."""

    schema = payload.get("schema_version")
    if schema != COMPLETE_MAP_SCHEMA_VERSION:
        msg = f"unexpected complete_map schema_version: {schema!r}"
        raise ValueError(msg)
    return ReconstructionCompleteMap(
        cells=tuple(_cell_from_dict(cell) for cell in payload["cells"]),
        field_cells=_coords_from_payload(payload["field_cells"]),
        shape_field_cell_count=int(payload["shape_field_cell_count"]),
        fluid_field_cell_count=int(payload["fluid_field_cell_count"]),
        external_void_cells=_coords_from_payload(payload["external_void_cells"]),
        coord_frame=CoordFrame(payload["coord_frame"]),
    )


__all__ = [
    "COMPLETE_MAP_SCHEMA_VERSION",
    "parse_complete_map",
    "serialize_complete_map",
]
