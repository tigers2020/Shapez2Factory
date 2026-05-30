"""PR-CLI-2c Slice 2 — ``ReconstructionCompleteMap`` JSON serializer round-trip (no Django)."""

from __future__ import annotations

import json

from shapez2_factory.adapters.asteroid_lab.complete_map_serializer import (
    COMPLETE_MAP_SCHEMA_VERSION,
    parse_complete_map,
    serialize_complete_map,
)
from shapez2_factory.domain.asteroid_lab.coord_frames import CoordFrame
from shapez2_factory.domain.asteroid_lab.decoded_cell import DecodedCellDTO
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    ReconstructionCompleteMap,
)


def _cell(x: int, y: int, cell_kind: str) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type="",
        cell_kind=cell_kind,
        transport_kind="none",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={"T": "SomeBuilding", "X": x, "Y": y},
    )


def _sample_complete_map() -> ReconstructionCompleteMap:
    cells = (
        _cell(0, 0, "asteroid_shape_field"),
        _cell(1, 0, "asteroid_fluid_field"),
        _cell(2, 1, "wall"),
    )
    return ReconstructionCompleteMap(
        cells=cells,
        field_cells=frozenset({(0, 0), (1, 0)}),
        shape_field_cell_count=1,
        fluid_field_cell_count=1,
        external_void_cells=frozenset({(-1, 0), (3, 1)}),
        coord_frame=CoordFrame.ISLAND_RAW,
    )


def test_serialize_emits_schema_version_and_jsonable_payload() -> None:
    payload = serialize_complete_map(_sample_complete_map())

    assert payload["schema_version"] == COMPLETE_MAP_SCHEMA_VERSION
    # Must be JSON-serializable end to end.
    json.dumps(payload)


def test_serialize_is_deterministic_sorted_coords() -> None:
    payload = serialize_complete_map(_sample_complete_map())

    assert payload["coord_frame"] == "island_raw"
    assert payload["field_cells"] == [[0, 0], [1, 0]]
    assert payload["external_void_cells"] == [[-1, 0], [3, 1]]
    # Re-serializing the same map yields byte-identical JSON.
    again = serialize_complete_map(_sample_complete_map())
    assert json.dumps(payload, sort_keys=True) == json.dumps(again, sort_keys=True)


def test_round_trip_equals_original() -> None:
    original = _sample_complete_map()

    parsed = parse_complete_map(serialize_complete_map(original))

    assert parsed == original
    assert parsed.cells == original.cells
    assert parsed.field_cells == original.field_cells
    assert parsed.external_void_cells == original.external_void_cells
    assert parsed.coord_frame is CoordFrame.ISLAND_RAW


def test_round_trip_through_json_text() -> None:
    original = _sample_complete_map()

    text = json.dumps(serialize_complete_map(original))
    parsed = parse_complete_map(json.loads(text))

    assert parsed == original
