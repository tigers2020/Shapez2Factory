"""Pure decoded blueprint snapshot builder (A5)."""

from __future__ import annotations

import json
from dataclasses import asdict

from django_apps.asteroid_lab.snapshots.cell_classifier import classify_blueprint_entry
from django_apps.asteroid_lab.snapshots.decoded_blueprint_snapshot import (
    build_decoded_blueprint_snapshot,
)


def test_classify_space_pipe_fluid_pipe() -> None:
    ck, tk = classify_blueprint_entry("SpacePipe_Forward")
    assert ck == "space_pipe" and tk == "fluid_pipe"


def test_classify_space_belt_shape_belt() -> None:
    ck, tk = classify_blueprint_entry("SpaceBelt_Left")
    assert ck == "space_belt" and tk == "shape_belt"


def test_classify_fluid_miner_and_extension() -> None:
    assert classify_blueprint_entry("Layout_FluidMiner") == ("fluid_miner", "fluid_pipe")
    assert classify_blueprint_entry("Layout_FluidMinerExtension") == (
        "fluid_miner_extension",
        "fluid_pipe",
    )


def test_classify_shape_miner_and_extension() -> None:
    assert classify_blueprint_entry("Layout_ShapeMiner") == ("shape_miner", "shape_belt")
    assert classify_blueprint_entry("Layout_ProMiner") == ("shape_miner", "shape_belt")
    assert classify_blueprint_entry("Layout_ShapeMinerExtension") == (
        "shape_miner_extension",
        "shape_belt",
    )


def test_classify_unknown_none() -> None:
    assert classify_blueprint_entry("TotallyUnknown") == ("unknown", "none")
    assert classify_blueprint_entry(None) == ("unknown", "none")


def test_nested_b_entries_summarized_not_unfolded() -> None:
    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {
                    "X": -8,
                    "Y": 0,
                    "R": 3,
                    "T": "Layout_FluidMiner",
                    "B": {
                        "$type": "Building",
                        "Entries": [
                            {"X": 5, "Y": 8, "T": "PumpDefaultInternalVariant"},
                            {"X": 5, "Y": 7, "T": "PumpDefaultInternalVariant"},
                        ],
                    },
                },
            ],
        },
    }
    snap = build_decoded_blueprint_snapshot(decoded)
    assert len(snap.cells) == 1
    c0 = snap.cells[0]
    assert c0.x == -8 and c0.y == 0
    assert c0.cell_kind == "fluid_miner"
    assert c0.nested_entry_count == 2
    assert c0.nested_type_counts_json == {"PumpDefaultInternalVariant": 2}
    assert c0.has_nested_blueprint is True


def test_bbox_and_counts() -> None:
    decoded = {
        "V": 7,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 2, "Y": 1, "R": 0, "T": "SpacePipe_Forward"},
                {"X": -1, "Y": -1, "R": 1, "T": "SpaceBelt_Right"},
                {"X": 2, "Y": 1, "R": 0, "T": "WeirdUnknown"},
            ],
        },
    }
    snap = build_decoded_blueprint_snapshot(decoded)
    assert snap.bbox_json["min_x"] == -1
    assert snap.bbox_json["max_x"] == 2
    assert snap.bbox_json["min_y"] == -1
    assert snap.bbox_json["max_y"] == 1
    assert snap.bbox_json["width"] == 4
    assert snap.bbox_json["height"] == 3
    assert snap.cell_kind_counts_json["space_pipe"] == 1
    assert snap.cell_kind_counts_json["space_belt"] == 1
    assert snap.cell_kind_counts_json["unknown"] == 1
    assert snap.transport_kind_counts_json["fluid_pipe"] == 1
    assert snap.transport_kind_counts_json["shape_belt"] == 1
    assert snap.transport_kind_counts_json["none"] == 1


def test_raw_x_zero_entry_gets_explicit_server_xy_for_algorithm_boundary() -> None:
    """Raw blueprint ``X == 0`` has no dense horizontal index; DTO still carries server (0, Δy)."""

    decoded = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 0, "Y": -6, "R": 0, "T": "SpaceBelt_Left"},
                {"X": 1, "Y": -6, "R": 0, "T": "SpaceBelt_Left"},
            ],
        },
    }
    snap = build_decoded_blueprint_snapshot(decoded)
    c0 = next(c for c in snap.cells if c.x == 0)
    assert c0.server_x == 0
    assert c0.server_y == 0


def test_snapshot_dto_json_serializable() -> None:
    decoded = {
        "V": 1,
        "_asteroid_lab_summary": {"k": "v"},
        "BP": {"$type": "Island", "Entries": [{"X": 1, "Y": 0, "R": 0, "T": "SpacePipe_A"}]},
    }
    snap = build_decoded_blueprint_snapshot(decoded, project_id=9, map_input_id=3)
    blob = json.dumps(asdict(snap))
    assert "space_pipe" in blob
    assert snap.summary_json.get("k") == "v"
