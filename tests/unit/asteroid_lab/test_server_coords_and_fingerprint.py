"""Server coords (dense x + bbox) and layout fingerprints."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.services.dto import DecodedCellDTO
from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import (
    build_decoded_blueprint_snapshot,
)
from django_apps.asteroid_lab.snapshots.existing_layout_inspection import (
    inspect_existing_layout,
)
from django_apps.asteroid_lab.snapshots.layout_fingerprint import (
    absolute_layout_fingerprint_sha256,
    layout_fingerprint_payload,
    layout_fingerprint_sha256,
)
from django_apps.asteroid_lab.snapshots.server_coords import (
    COORD_SYSTEM_BBOX_RIGHT_BOTTOM,
    attach_server_coords_to_decoded_json,
    coerce_server_axis_int,
    map_bbox_dense_and_y_from_lab_rows,
    raw_x_to_dense_x,
    raw_xy_for_server_xy,
    server_xy_for_raw_xy,
)
from django_apps.shapez_asteroid.adapters.reconstruction_adapter import decoded_cell_to_server_coord


def test_raw_x_to_dense_x_examples() -> None:
    assert raw_x_to_dense_x(-5) == -2
    assert raw_x_to_dense_x(-3) == -1
    assert raw_x_to_dense_x(-1) == 0
    assert raw_x_to_dense_x(1) == 1
    assert raw_x_to_dense_x(3) == 2
    assert raw_x_to_dense_x(5) == 3


def test_raw_x_to_dense_x_adjacent_across_seam() -> None:
    assert raw_x_to_dense_x(1) - raw_x_to_dense_x(-1) == 1


def test_raw_x_zero_raises() -> None:
    with pytest.raises(ValueError, match="no x == 0"):
        raw_x_to_dense_x(0)


def test_server_xy_right_bottom_origin_single_cell() -> None:
    pair = server_xy_for_raw_xy(1, 0, max_dense_x=1, min_raw_y=0)
    assert pair == (0, 0)


def test_raw_xy_for_server_xy_round_trip_with_lookup() -> None:
    lab_rows = [
        {"x": 1, "y": 0, "cell_kind": "field"},
        {"x": 3, "y": 0, "cell_kind": "field"},
    ]
    sx0, sy0 = server_xy_for_raw_xy(1, 0, max_dense_x=2, min_raw_y=0)
    assert (sx0, sy0) == (1, 0)
    sx1, sy1 = server_xy_for_raw_xy(3, 0, max_dense_x=2, min_raw_y=0)
    assert (sx1, sy1) == (0, 0)
    assert raw_xy_for_server_xy(sx0, sy0, max_dense_x=2, min_raw_y=0, lab_rows=lab_rows) == (1, 0)
    assert raw_xy_for_server_xy(sx1, sy1, max_dense_x=2, min_raw_y=0, lab_rows=lab_rows) == (3, 0)


def test_map_bbox_dense_and_y_from_lab_rows_matches_two_columns() -> None:
    rows = [{"x": 1, "y": 0}, {"x": 3, "y": 0}]
    assert map_bbox_dense_and_y_from_lab_rows(rows) == (2, 0)


def test_coerce_server_axis_int_rejects_bool_accepts_integral_float() -> None:
    assert coerce_server_axis_int(None) is None
    assert coerce_server_axis_int(True) is None
    assert coerce_server_axis_int(False) is None
    assert coerce_server_axis_int(0.0) == 0
    assert coerce_server_axis_int(-6.0) == -6
    assert coerce_server_axis_int(" -3 ") == -3


def test_decoded_cell_to_server_coord_accepts_float_zero_server_y() -> None:
    cell = DecodedCellDTO(
        x=-6,
        y=0,
        layer=None,
        rotation=0,
        tile_type="",
        cell_kind="asteroid_shape_field",
        transport_kind="none",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
        server_x=4,
        server_y=0.0,
    )
    c = decoded_cell_to_server_coord(cell, server_xy_params=(1, 0))
    assert c.x == 4 and c.y == 0


def test_decoded_cell_to_server_coord_raw_negative_six_y_zero() -> None:
    cell = DecodedCellDTO(
        x=-6,
        y=0,
        layer=None,
        rotation=0,
        tile_type="",
        cell_kind="asteroid_shape_field",
        transport_kind="none",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
        server_x=None,
        server_y=None,
    )
    c = decoded_cell_to_server_coord(cell, server_xy_params=(1, 0))
    assert (c.x, c.y) == server_xy_for_raw_xy(-6, 0, max_dense_x=1, min_raw_y=0)


def test_decoded_cell_to_server_coord_raw_x_zero_uses_layout_line_bridge() -> None:
    cell = DecodedCellDTO(
        x=0,
        y=5,
        layer=None,
        rotation=0,
        tile_type="",
        cell_kind="asteroid_shape_field",
        transport_kind="none",
        has_nested_blueprint=False,
        nested_entry_count=0,
        nested_type_counts_json={},
        raw_entry_json={},
        server_x=None,
        server_y=None,
    )
    c = decoded_cell_to_server_coord(cell, server_xy_params=(1, 0))
    assert (c.x, c.y) == server_xy_for_raw_xy(-1, 5, max_dense_x=1, min_raw_y=0)


def test_attach_server_coords_pipe_seam() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": -1, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
                {"X": 1, "Y": 0, "R": 0, "T": "SpacePipe_Right"},
            ],
        },
    }
    attach_server_coords_to_decoded_json(decoded)
    e0, e1 = decoded["BP"]["Entries"]
    assert e0["server_x"] == 1 and e0["server_y"] == 0
    assert e1["server_x"] == 0 and e1["server_y"] == 0
    meta = decoded.get("_asteroid_lab_coord_system")
    assert isinstance(meta, dict)
    assert meta.get("coord_system") == COORD_SYSTEM_BBOX_RIGHT_BOTTOM


def test_server_origin_bottom_right_corner_zero() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 3, "Y": 2, "R": 0, "T": "SpaceBelt_Left"},
                {"X": -1, "Y": 2, "R": 0, "T": "SpaceBelt_Right"},
            ],
        },
    }
    attach_server_coords_to_decoded_json(decoded)
    entries = decoded["BP"]["Entries"]
    by_xy = {(e["X"], e["Y"]): e for e in entries}
    br = by_xy[(3, 2)]
    assert br["server_x"] == 0 and br["server_y"] == 0


def test_layout_fingerprint_payload_has_schema_and_coord_system() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "R": 0, "T": "Layout_ShapeMiner"},
                {"X": -1, "Y": 0, "R": 0, "T": "Layout_ShapeMinerExtension"},
            ],
        },
    }
    attach_server_coords_to_decoded_json(decoded)
    p = layout_fingerprint_payload(decoded)
    assert p["schema"] == "asteroid-miner-layout-map.v1"
    assert p["coord_system"] == COORD_SYSTEM_BBOX_RIGHT_BOTTOM
    assert len(p["cells"]) == 2
    kinds = {c["kind"] for c in p["cells"]}
    assert kinds == {"extractor", "extension"}


def test_layout_fingerprint_deterministic_hex() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [{"X": 1, "Y": 0, "R": 2, "T": "Layout_ShapeMiner"}],
        },
    }
    attach_server_coords_to_decoded_json(decoded)
    h1 = layout_fingerprint_sha256(decoded)
    h2 = layout_fingerprint_sha256(decoded)
    assert len(h1) == 64 and h1 == h2


def test_absolute_fingerprint_changes_with_raw_translation() -> None:
    a = {
        "V": 1,
        "BP": {"$type": "Island", "Entries": [{"X": 1, "Y": 0, "R": 0, "T": "Layout_ShapeMiner"}]},
    }
    b = {
        "V": 1,
        "BP": {"$type": "Island", "Entries": [{"X": 3, "Y": 0, "R": 0, "T": "Layout_ShapeMiner"}]},
    }
    attach_server_coords_to_decoded_json(a)
    attach_server_coords_to_decoded_json(b)
    assert layout_fingerprint_sha256(a) == layout_fingerprint_sha256(b)
    assert absolute_layout_fingerprint_sha256(a) != absolute_layout_fingerprint_sha256(b)


def test_inspect_transport_raw_bfs_after_attach() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": -1, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
                {"X": 1, "Y": 0, "R": 0, "T": "SpacePipe_Right"},
            ],
        },
    }
    attach_server_coords_to_decoded_json(decoded)
    snap = build_decoded_blueprint_snapshot(decoded)
    ins = inspect_existing_layout(snap)
    fluid = [c for c in ins.transport_components if c.transport_kind == "fluid_pipe"]
    assert len(fluid) == 1
    assert fluid[0].cell_count == 2


def test_bbox_of_cells_reports_dense_and_server_width() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": -1, "Y": 0, "R": 0, "T": "SpacePipe_Forward"},
                {"X": 1, "Y": 0, "R": 0, "T": "SpacePipe_Right"},
            ],
        },
    }
    attach_server_coords_to_decoded_json(decoded)
    snap = build_decoded_blueprint_snapshot(decoded)
    assert snap.bbox_json["width"] == 3
    assert snap.bbox_json["dense_width"] == 2
    assert snap.bbox_json["server_width"] == 2
