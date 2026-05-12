from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.existing_layout.existing_layout_analysis import (  # noqa: E501
    analyze_existing_layout_from_mining_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    external_predicate_for_mining_map,
)
from django_apps.shapez_asteroid.services.blueprint_map_summary import (
    build_map_timeline,
    merge_with_transport_and_final_mining_map,
)


def test_raw_asteroid_no_transport_classifies_raw_field() -> None:
    mining_map = [
        {
            "x": 1,
            "y": 1,
            "role": "occupied",
            "surface": "shape",
            "layout_kind": "miner",
            "r": 0,
        },
    ]
    is_ext = external_predicate_for_mining_map(mining_map)
    out = analyze_existing_layout_from_mining_map(mining_map, is_external=is_ext)
    assert out["source_kind"] == "raw_asteroid_field"
    assert out["transport"]["transport_kind"] == "none"


def test_belt_single_component_classifies_shape_layout() -> None:
    mining_map = [
        {"x": 1, "y": 1, "role": "occupied", "surface": "shape", "layout_kind": "miner", "r": 0},
        {"x": 2, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 3, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
    ]
    is_ext = external_predicate_for_mining_map(mining_map)
    out = analyze_existing_layout_from_mining_map(mining_map, is_external=is_ext)
    assert out["source_kind"] == "existing_shape_layout"
    belt = out["transport"]
    assert belt["component_count"] == 1
    st = belt["components"][0]["status"]
    assert st in ("main_trunk_candidate", "orphan_component", "cleanup_candidate")


def test_step05_merge_baseline_includes_inferred_for_analysis() -> None:
    """STEP 0.5 uses merged with_transport + final map (same contract as solver_init)."""

    decoded = {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 1, "T": "Layout_ShapeMiner"},
                {"X": 2, "Y": 1, "T": "Layout_ShapeMiner"},
                {"X": 3, "Y": 1, "T": "Layout_ShapeMiner"},
                {"X": 1, "Y": 2, "T": "Layout_ShapeMiner"},
                {"X": 3, "Y": 2, "T": "Layout_ShapeMiner"},
                {"X": 1, "Y": 3, "T": "Layout_ShapeMiner"},
                {"X": 2, "Y": 3, "T": "Layout_ShapeMiner"},
                {"X": 3, "Y": 3, "T": "Layout_ShapeMiner"},
                {"X": 10, "Y": 2, "T": "Layout_UndergroundBelt", "R": 0},
            ]
        }
    }
    tl = build_map_timeline(decoded)
    merged = merge_with_transport_and_final_mining_map(tl[0]["mining_map"], tl[-1]["mining_map"])
    assert any(c.get("role") == "inferred" for c in merged)
    is_ext = external_predicate_for_mining_map(tl[1]["mining_map"])
    out = analyze_existing_layout_from_mining_map(merged, is_external=is_ext)
    assert "source_kind" in out
    assert "transport" in out


def test_isolated_belt_component_is_orphan_issue() -> None:
    mining_map = [
        {"x": 1, "y": 1, "role": "occupied", "surface": "shape", "layout_kind": "miner", "r": 0},
        {"x": 2, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 3, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 80, "y": 80, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 81, "y": 80, "role": "belt", "surface": "shape", "layout_kind": "belt"},
    ]
    is_ext = external_predicate_for_mining_map(mining_map)
    out = analyze_existing_layout_from_mining_map(mining_map, is_external=is_ext)
    codes = {i["code"] for i in out["issues"]}
    assert "ORPHAN_TRANSPORT_COMPONENT" in codes
