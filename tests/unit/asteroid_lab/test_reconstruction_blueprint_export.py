"""Reconstructed blueprint export/import: Extension T ??asteroid_*_field."""

from __future__ import annotations

from django_apps.asteroid_lab.adapters.reconstruction_blueprint_export import (
    T_FLUID_FIELD,
    T_SHAPE_FIELD,
    build_reconstructed_normalized_dto,
    cell_kind_for_reconstruction_import,
    encode_reconstructed_copy_string,
    load_reconstruction_cells_from_copy_code,
    load_reconstruction_cells_from_decoded_json,
    reconstruction_cell_keys,
    tile_type_for_reconstruction_export,
)
from django_apps.asteroid_lab.services.dto import DecodedCellDTO


def _cell(
    x: int,
    y: int,
    *,
    cell_kind: str = "unknown",
    tile_type: str = "",
    transport_kind: str = "none",
) -> DecodedCellDTO:
    return DecodedCellDTO(
        x=x,
        y=y,
        layer=None,
        rotation=0,
        tile_type=tile_type,
        cell_kind=cell_kind,
        transport_kind=transport_kind,
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
    )


def test_tile_type_export_shape_and_fluid_fields() -> None:
    assert tile_type_for_reconstruction_export(_cell(0, 0, cell_kind="asteroid_shape_field")) == (
        T_SHAPE_FIELD
    )
    assert tile_type_for_reconstruction_export(_cell(0, 0, cell_kind="asteroid_fluid_field")) == (
        T_FLUID_FIELD
    )


def test_import_maps_extension_to_asteroid_field_kinds() -> None:
    sk, _ = cell_kind_for_reconstruction_import(T_SHAPE_FIELD)
    fk, _ = cell_kind_for_reconstruction_import(T_FLUID_FIELD)
    assert sk == "asteroid_shape_field"
    assert fk == "asteroid_fluid_field"
    ext_sk, ext_tk = cell_kind_for_reconstruction_import(T_SHAPE_FIELD)
    assert ext_sk == "asteroid_shape_field"
    assert ext_tk == "none"
    # generic classifier would be miner_extension ??must not use here for our T
    assert ext_sk != "shape_miner_extension"


def test_encode_copy_string_ends_with_dollar() -> None:
    cells = (
        _cell(1, 1, cell_kind="asteroid_shape_field"),
        _cell(2, 1, cell_kind="asteroid_fluid_field"),
    )
    norm = build_reconstructed_normalized_dto(cells, run_key="rk1")
    code = encode_reconstructed_copy_string(norm.decoded_json)
    assert code.startswith("SHAPEZ2-4-")
    assert code.endswith("$")


def test_roundtrip_cell_kind_keys() -> None:
    cells = (
        _cell(0, 0, cell_kind="asteroid_shape_field"),
        _cell(1, 0, cell_kind="asteroid_fluid_field"),
    )
    norm = build_reconstructed_normalized_dto(cells, map_input_id=7, run_key="inspection-1")
    code = encode_reconstructed_copy_string(norm.decoded_json)
    loaded = load_reconstruction_cells_from_copy_code(code)
    assert reconstruction_cell_keys(cells) == reconstruction_cell_keys(loaded)


def test_load_from_decoded_json_matches_copy_code() -> None:
    cells = (_cell(3, 4, cell_kind="asteroid_fluid_field"),)
    norm = build_reconstructed_normalized_dto(cells)
    from_copy = load_reconstruction_cells_from_copy_code(
        encode_reconstructed_copy_string(norm.decoded_json)
    )
    from_json = load_reconstruction_cells_from_decoded_json(norm.decoded_json)
    assert reconstruction_cell_keys(from_copy) == reconstruction_cell_keys(from_json)
