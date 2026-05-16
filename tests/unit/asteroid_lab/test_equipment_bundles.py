"""Tests for port-based equipment bundles (PORT_TABLE calibrated on a real blueprint)."""

from __future__ import annotations

from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.replay.snapshot_map_replay import rows_from_cells
from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import (
    build_decoded_blueprint_snapshot,
)
from django_apps.asteroid_lab.snapshots.equipment_bundles import (
    build_equipment_bundles,
    equipment_ports,
)

# Real asteroid layouts (copy strings) for regression on PORT_TABLE + bundle graph.
_USER_BLUEPRINT_COPY = "SHAPEZ2-4-H4sIAD56CGoA/5yWUUvDMBSF/8vFxwhLsrZbHsU9DBTGlKGMIUEjFmo6khQspf/drJkgyCT3Umhpe757Tm6akgF2oDiXFYObDagBrkJ/NKBg7Rtt34DB+rW1pxe3OmhQe6jjvdo0Ory37tMDs13TpBP4D300atulAw4jg5UNrjY+ggM8gbqeM3iOl2j3GE3udN924eXhxN3X1rjVVzDW19FxZAmQCeCCwRaUvMD9kfN/5RdtqjwXntRldvkzIDFAhjK3M+iWTMAMCVR5QUpkWZlXViDKZsxx6pbInTCRJrhA6pH1OU5e4uQLZJjsNLg1TFzCP9iMhC1JVIUZUEmyKEiUxAQTtEZTKI7IRYolKVCBSEWaxQXCgPQlckxjObKz818DFzhoSYF49r/3EHcttdWu3xk3PZm2MuP4LYAAAwAZxBUl1ggAAA=="
_USER_BLUEPRINT_COPY_ALT = "SHAPEZ2-4-H4sIAB+ACGoA/5xWXWuDMBT9L5c9pg+Jn+RxrA+FDUo3ysooI2wZE1wsMcJE/O9LFcGNtd4bBEE9595zrickHexBch5lDG63IDu4ce1Jg4RNXSrzDgw2b5U5f7hTToF8gcI/y22p3Edlv2pgpinL8Qb1pzppuWvGC449g7VxttC1J3bwDHKVM3jy1e9VWzXu9fFMeCiMtutvp01d+FY9G5Fe0Q5kdAE/hx28A3TZFFc2ncpeAf9b3LMEGp9MeIykeACvOBpNkh4T5xjPpOMNR4ix/gELohExayGILDyeU4xwspHDKGmp+HIefpel9OdYIDEDlMnxkAQIWpJFSJCj+VoUCy4ooQ/K/EiKaKQYY+ECCz3cJKhJQhhYEjKwNEhWSvOO28CykI0mCzGdTSnBwXPCT8hD9OS01B79CaUwyrZ7bYc3w7Gl738EEGAAdbS61MIIAAA="


def _row(
    x: int,
    y: int,
    cell_kind: str,
    *,
    rotation: int = 0,
    layer: int | None = None,
) -> dict:
    transport = "fluid_pipe" if cell_kind.startswith("fluid") else "shape_belt"
    r: dict = {
        "x": x,
        "y": y,
        "rotation": rotation,
        "cell_kind": cell_kind,
        "transport_kind": transport,
    }
    if layer is not None:
        r["layer"] = layer
    return r


def _bundle_ids_by_xy(bundles: list[dict]) -> dict[tuple[int, int], int]:
    out: dict[tuple[int, int], int] = {}
    for block in bundles:
        bid = int(block["bundle_id"])
        for c in block["cells_json"]:
            out[(int(c["x"]), int(c["y"]))] = bid
    return out


def _shape_rows_from_copy(copy_code: str) -> list[dict]:
    root = decode_copy_string(copy_code.strip().rstrip("$")).root
    snap = build_decoded_blueprint_snapshot(root)
    rows = rows_from_cells(snap.cells)
    return [r for r in rows if r.get("cell_kind") in ("shape_miner", "shape_miner_extension")]


def test_user_blueprint_shape_thirteen_bundles() -> None:
    """Golden: first calibration map → 13 shape equipment bundles."""

    shape_rows = _shape_rows_from_copy(_USER_BLUEPRINT_COPY)
    bundles = build_equipment_bundles(shape_rows)
    assert len(bundles) == 13


def test_user_blueprint_shape_alt_twelve_bundles() -> None:
    """Second real map decodes and yields 12 shape bundles (topology differs from 13-map)."""

    shape_rows = _shape_rows_from_copy(_USER_BLUEPRINT_COPY_ALT)
    assert len(shape_rows) == 44
    bundles = build_equipment_bundles(shape_rows)
    assert len(bundles) == 12


def test_ports_face_each_other_same_bundle() -> None:
    """R=0 miner south into extension with R=3 (input faces north)."""

    rows = [
        _row(-1, 0, "fluid_miner", rotation=0),
        _row(-1, 1, "fluid_miner_extension", rotation=3),
    ]
    bundles = build_equipment_bundles(rows)
    assert len(bundles) == 1
    assert bundles[0]["bundle_id"] == 1
    assert len(bundles[0]["cells_json"]) == 2
    ids = _bundle_ids_by_xy(bundles)
    assert ids[(-1, 0)] == ids[(-1, 1)]


def test_adjacent_extractors_never_merge() -> None:
    """Two 4-neighbor extractors stay in separate bundles (miner–miner edge forbidden)."""

    rows = [
        _row(-1, 0, "fluid_miner", rotation=0),
        _row(1, 0, "fluid_miner", rotation=0),
    ]
    bundles = build_equipment_bundles(rows)
    assert len(bundles) == 2
    ids = _bundle_ids_by_xy(bundles)
    assert ids[(-1, 0)] != ids[(1, 0)]


def test_x_scenario_adjacent_rotation_blocks_link() -> None:
    """Neighbor exists but extension input does not accept miner's south output -> split."""

    rows = [
        _row(-1, 0, "fluid_miner", rotation=0),
        _row(-1, 1, "fluid_miner_extension", rotation=0),
    ]
    bundles = build_equipment_bundles(rows)
    assert len(bundles) == 2


def test_transport_tile_not_in_graph() -> None:
    """Belt/pipe rows are ignored; they neither join nor relay equipment."""

    rows = [
        _row(-1, 0, "fluid_miner"),
        {
            "x": 1,
            "y": 0,
            "rotation": 0,
            "cell_kind": "space_belt",
            "transport_kind": "shape_belt",
        },
    ]
    bundles = build_equipment_bundles(rows)
    assert len(bundles) == 1
    assert len(bundles[0]["cells_json"]) == 1


def test_fluid_shape_no_cross_family_edge() -> None:
    rows = [
        _row(-1, 0, "fluid_miner"),
        _row(1, 0, "shape_miner_extension"),
    ]
    bundles = build_equipment_bundles(rows)
    assert len(bundles) == 2


def test_output_schema_bundle_edges() -> None:
    rows = [
        _row(-1, 0, "shape_miner", rotation=0),
        _row(-1, 1, "shape_miner_extension", rotation=3),
    ]
    bundles = build_equipment_bundles(rows)
    assert len(bundles) == 1
    for c in bundles[0]["cells_json"]:
        assert "bundle_edges" in c
        assert isinstance(c["bundle_edges"], str)
    joined = "".join(c["bundle_edges"] for c in bundles[0]["cells_json"])
    assert "n" in joined or "e" in joined or "s" in joined or "w" in joined


def test_equipment_ports_rotation_normalizes() -> None:
    p0 = equipment_ports("shape_miner", 0)
    assert p0 is not None
    p4 = equipment_ports("shape_miner", 4)
    assert p4 is not None
    assert p0.input_dirs == p4.input_dirs
    assert p0.output_dirs == p4.output_dirs


def test_different_layers_no_link() -> None:
    rows = [
        _row(-1, 0, "fluid_miner", layer=0),
        _row(-1, 1, "fluid_miner_extension", layer=1),
    ]
    bundles = build_equipment_bundles(rows)
    assert len(bundles) == 2
