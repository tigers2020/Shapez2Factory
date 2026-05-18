"""Server coords (dense x + bbox) and layout fingerprints."""

from __future__ import annotations

from django_apps.asteroid_lab.snapshots.blueprint_equivalence import decoded_json_layout_equivalent
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
    COORD_SYSTEM_BBOX_LEFT_BOTTOM,
    attach_server_coords_to_decoded_json,
    full_map_row_for_boundary_jsonl,
    jsonl_coord_fields,
    raw_x_to_dense_index,
    raw_x_to_dense_x,
    server_xy_for_raw_xy,
)


def test_jsonl_coord_fields_server_null_without_bbox_params() -> None:
    d = jsonl_coord_fields(1, 2, server_xy_params=None)
    assert d == {"raw_x": 1, "raw_y": 2, "server_x": None, "server_y": None}


def test_full_map_row_for_boundary_jsonl_merges_keys() -> None:
    row = {"x": 1, "y": 0, "layer": None, "cell_kind": "space_belt"}
    out = full_map_row_for_boundary_jsonl(row, server_xy_params=(0, 0))
    assert out["raw_x"] == 1 and out["x"] == 1
    assert out["server_x"] == 0 and out["server_y"] == 0


def test_raw_x_to_dense_index_examples() -> None:
    assert raw_x_to_dense_index(-5) == -5
    assert raw_x_to_dense_index(-3) == -3
    assert raw_x_to_dense_index(-1) == -1
    assert raw_x_to_dense_index(1) == 0
    assert raw_x_to_dense_index(3) == 2
    assert raw_x_to_dense_index(5) == 4


def test_raw_x_to_dense_x_alias_matches() -> None:
    assert raw_x_to_dense_x(1) == raw_x_to_dense_index(1)


def test_raw_x_to_dense_adjacent_across_seam() -> None:
    assert raw_x_to_dense_index(1) - raw_x_to_dense_index(-1) == 1


def test_raw_x_zero_maps_to_dense_zero() -> None:
    assert raw_x_to_dense_index(0) == 0


def test_server_xy_left_bottom_origin_single_cell() -> None:
    pair = server_xy_for_raw_xy(1, 0, min_dense_x=0, min_raw_y=0)
    assert pair == (0, 0)


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
    assert e0["server_x"] == 0 and e0["server_y"] == 0
    assert e1["server_x"] == 1 and e1["server_y"] == 0
    meta = decoded.get("_asteroid_lab_coord_system")
    assert isinstance(meta, dict)
    assert meta.get("coord_system") == COORD_SYSTEM_BBOX_LEFT_BOTTOM


def test_attach_server_coords_left_bottom_min_corner_zero() -> None:
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
    lb = by_xy[(-1, 2)]
    assert lb["server_x"] == 0 and lb["server_y"] == 0


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
    assert p["coord_system"] == COORD_SYSTEM_BBOX_LEFT_BOTTOM
    assert p["origin"] == "left_bottom"
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


def test_decoded_json_layout_equivalent_parallel_miner_shift() -> None:
    base = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "R": 0, "T": "Layout_ShapeMiner"},
                {"X": 1, "Y": 1, "R": 0, "T": "Layout_ShapeMinerExtension"},
            ],
        },
    }
    shifted = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 3, "Y": 0, "R": 0, "T": "Layout_ShapeMiner"},
                {"X": 3, "Y": 1, "R": 0, "T": "Layout_ShapeMinerExtension"},
            ],
        },
    }
    assert decoded_json_layout_equivalent(base, shifted, include_transport=False)
    assert decoded_json_layout_equivalent(base, shifted, include_transport=True)


def test_decoded_json_layout_equivalent_dense_x_across_raw_x_seam() -> None:
    """Same dense_x offset across negative/positive raw X (column 0 missing)."""

    left = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": -1, "Y": 0, "R": 0, "T": "Layout_ShapeMiner"},
                {"X": 1, "Y": 0, "R": 0, "T": "Layout_ShapeMinerExtension"},
            ],
        },
    }
    right = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "R": 0, "T": "Layout_ShapeMiner"},
                {"X": 2, "Y": 0, "R": 0, "T": "Layout_ShapeMinerExtension"},
            ],
        },
    }
    assert decoded_json_layout_equivalent(left, right, include_transport=False)
