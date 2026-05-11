from __future__ import annotations

from django_apps.shapez_asteroid.services.blueprint_map_summary import (
    MAP_TIMELINE_STEP_IDS,
    build_map_timeline,
    list_island_mining_map,
    merge_with_transport_and_final_mining_map,
    summarize_island_entries_map,
)
from django_apps.shapez_asteroid.services.style_classifier import PlotStyle, classify_layout_type


def test_empty_entries() -> None:
    assert summarize_island_entries_map({"V": 1, "BP": {"Entries": []}}) == {
        "entry_count": 0,
        "x_min": None,
        "x_max": None,
        "y_min": None,
        "y_max": None,
    }


def test_missing_bp() -> None:
    assert summarize_island_entries_map({"V": 1})["entry_count"] == 0


def test_bp_not_dict() -> None:
    assert summarize_island_entries_map({"BP": "no"})["entry_count"] == 0


def test_entries_not_list() -> None:
    out = summarize_island_entries_map({"BP": {"Entries": {}}})
    assert out["entry_count"] == 0


def test_unknown_type_yields_zero_extraction() -> None:
    decoded = {"BP": {"Entries": [{"X": 3, "Y": 5, "T": "X"}]}}
    assert summarize_island_entries_map(decoded) == {
        "entry_count": 0,
        "x_min": None,
        "x_max": None,
        "y_min": None,
        "y_max": None,
    }
    assert list_island_mining_map(decoded) == []


def test_symmetric_layout_non_extraction_yields_empty() -> None:
    decoded = {"BP": {"Entries": [{"X": -1, "Y": 0}, {"X": 1, "Y": 0}]}}
    assert summarize_island_entries_map(decoded)["entry_count"] == 0
    assert list_island_mining_map(decoded) == []


def test_negative_coords_extraction() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": -7, "Y": -6, "T": "Layout_ShapeMiner"},
                {"X": -7, "Y": 4, "T": "Layout_ShapeMiner"},
            ]
        }
    }
    assert summarize_island_entries_map(decoded) == {
        "entry_count": 2,
        "x_min": -7,
        "x_max": -7,
        "y_min": -6,
        "y_max": 4,
    }


def test_missing_y_defaults_to_zero_extraction() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": -7, "Y": 1, "T": "Layout_ShapeMiner"},
                {"X": -7, "T": "Layout_ShapeMiner"},
            ]
        }
    }
    assert summarize_island_entries_map(decoded) == {
        "entry_count": 2,
        "x_min": -7,
        "x_max": -7,
        "y_min": 0,
        "y_max": 1,
    }


def test_entries_without_x_skipped_for_bounds() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"Y": 1, "T": "Layout_ShapeMiner"},
                {"X": 2, "Y": 3, "T": "Layout_ShapeMiner"},
            ]
        }
    }
    assert summarize_island_entries_map(decoded) == {
        "entry_count": 1,
        "x_min": 2,
        "x_max": 2,
        "y_min": 3,
        "y_max": 3,
    }


def test_all_entries_lack_x_bounds_null() -> None:
    decoded = {"BP": {"Entries": [{"Y": 1}, {"T": "z"}]}}
    assert summarize_island_entries_map(decoded) == {
        "entry_count": 0,
        "x_min": None,
        "x_max": None,
        "y_min": None,
        "y_max": None,
    }


def test_non_dict_entry_ignored_for_bounds() -> None:
    decoded = {"BP": {"Entries": ["skip", {"X": 1, "Y": 0, "T": "Layout_ShapeMiner"}]}}
    assert summarize_island_entries_map(decoded) == {
        "entry_count": 1,
        "x_min": 1,
        "x_max": 1,
        "y_min": 0,
        "y_max": 0,
    }


def test_list_mining_map_unknown_layouts() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 2, "T": "Layout_A"},
                {"X": -1, "T": "Layout_B"},
                {"Y": 1},
            ]
        }
    }
    assert list_island_mining_map(decoded) == []


def test_list_mining_map_non_string_t_unknown() -> None:
    decoded = {"BP": {"Entries": [{"X": 5, "Y": 0, "T": 42}]}}
    assert list_island_mining_map(decoded) == []


def test_x_zero_excluded_from_bounds_and_map() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 0, "Y": 99, "T": "Layout_ShapeMiner"},
                {"X": -2, "Y": 1, "T": "Layout_ShapeMiner"},
                {"X": 3, "Y": 1, "T": "Layout_ShapeMiner"},
            ]
        }
    }
    assert summarize_island_entries_map(decoded) == {
        "entry_count": 2,
        "x_min": -2,
        "x_max": 3,
        "y_min": 1,
        "y_max": 1,
    }
    assert list_island_mining_map(decoded) == [
        {
            "x": -2,
            "y": 1,
            "role": "occupied",
            "surface": "shape",
            "layout_kind": "asteroid_field",
            "source_layout_kind": "miner",
        },
        {
            "x": 3,
            "y": 1,
            "role": "occupied",
            "surface": "shape",
            "layout_kind": "asteroid_field",
            "source_layout_kind": "miner",
        },
    ]


def test_only_x_zero_entries_yields_no_bounds() -> None:
    decoded = {"BP": {"Entries": [{"X": 0, "Y": 1, "T": "Layout_ShapeMiner"}]}}
    assert summarize_island_entries_map(decoded) == {
        "entry_count": 0,
        "x_min": None,
        "x_max": None,
        "y_min": None,
        "y_max": None,
    }
    assert list_island_mining_map(decoded) == []


def test_build_map_timeline_final_matches_list_island_mining_map() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 2, "T": "Layout_ShapeMiner"},
                {"X": -2, "Y": 1, "T": "Layout_UndergroundBelt"},
                {"X": 3, "Y": 1, "T": "Layout_FluidPipe"},
            ]
        }
    }
    tl = build_map_timeline(decoded)
    assert len(tl) == len(MAP_TIMELINE_STEP_IDS)
    assert [s["id"] for s in tl] == list(MAP_TIMELINE_STEP_IDS)
    assert tl[-1]["mining_map"] == list_island_mining_map(decoded)
    assert tl[-1]["summary"] == summarize_island_entries_map(decoded)


def test_build_map_timeline_first_step_has_belt_and_pipe_roles() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_ShapeMiner"},
                {"X": 2, "Y": 0, "T": "Layout_UndergroundBelt"},
                {"X": 3, "Y": 0, "T": "Layout_FluidPipe"},
            ]
        }
    }
    first = build_map_timeline(decoded)[0]
    assert first["id"] == "with_transport"
    roles = {(c["x"], c["y"]): c["role"] for c in first["mining_map"]}
    assert roles[(2, 0)] == "belt"
    assert roles[(3, 0)] == "pipe"
    assert roles[(1, 0)] == "occupied"


def test_with_transport_transport_over_void_on_extraction_shell() -> None:
    """Belt/pipe on extraction shell keep fill; lone transport off shell is void (UI)."""

    decoded = {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_ShapeMiner"},
                {"X": 1, "Y": 0, "T": "Layout_UndergroundBelt"},
                {"X": 5, "Y": 0, "T": "Layout_UndergroundBelt"},
                {"X": 6, "Y": 0, "T": "Layout_FluidPipe"},
            ]
        }
    }
    first = build_map_timeline(decoded)[0]["mining_map"]
    by_xy = {(c["x"], c["y"]): c for c in first}
    assert by_xy[(1, 0)]["role"] == "belt"
    assert by_xy[(1, 0)]["transport_over_void"] is False
    assert by_xy[(5, 0)]["transport_over_void"] is True
    assert by_xy[(6, 0)]["transport_over_void"] is True


def test_strip_extractors_step_marks_removed_cells_as_asteroid_field() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 5, "Y": 1, "T": "Layout_FluidPump"},
                {"X": 6, "Y": 1, "T": "Layout_ShapeMiner"},
            ]
        }
    }
    tl = build_map_timeline(decoded)
    strip_ex = next(s for s in tl if s["id"] == "strip_extractors")
    by_xy = {(c["x"], c["y"]): c for c in strip_ex["mining_map"] if c.get("role") == "occupied"}
    assert by_xy[(5, 1)]["layout_kind"] == "asteroid_field"
    assert "t" not in by_xy[(5, 1)]
    assert by_xy[(6, 1)]["layout_kind"] == "asteroid_field"
    assert by_xy[(6, 1)]["surface"] == "shape"


def test_belt_pipe_not_in_map_fluid_extension_only() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                {"X": 2, "Y": 0, "T": "Layout_FluidPipe", "R": 1},
                {"X": 3, "Y": 0, "T": "Layout_FluidMinerExtension", "R": 2},
            ]
        }
    }
    pts = list_island_mining_map(decoded)
    assert len(pts) == 1
    assert pts[0] == {
        "x": 3,
        "y": 0,
        "role": "occupied",
        "surface": "fluid",
        "r": 2,
        "layout_kind": "asteroid_field",
        "source_layout_kind": "fluid_extension",
    }
    assert summarize_island_entries_map(decoded)["entry_count"] == 1


def test_unified_map_extractor_and_extension_same_role() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_FluidExtractor"},
                {"X": 2, "Y": 0, "T": "Layout_FluidMinerExtension"},
            ]
        }
    }
    pts = list_island_mining_map(decoded)
    assert pts[0]["role"] == "occupied"
    assert pts[1]["role"] == "occupied"
    assert pts[0]["surface"] == "fluid"
    assert pts[1]["surface"] == "fluid"
    assert pts[0]["layout_kind"] == "asteroid_field"
    assert pts[1]["layout_kind"] == "asteroid_field"
    assert pts[0]["source_layout_kind"] == "extractor"
    assert pts[1]["source_layout_kind"] == "fluid_extension"
    assert "t" not in pts[0]
    assert "t" not in pts[1]
    assert list_island_mining_map({}) == []


def test_shape_miner_on_map() -> None:
    decoded = {"BP": {"Entries": [{"X": 4, "Y": 0, "T": "Layout_ShapeMiner", "R": 1}]}}
    assert list_island_mining_map(decoded) == [
        {
            "x": 4,
            "y": 0,
            "role": "occupied",
            "surface": "shape",
            "r": 1,
            "layout_kind": "asteroid_field",
            "source_layout_kind": "miner",
        },
    ]


def test_shape_miner_extension_classified_for_filter_only() -> None:
    decoded = {"BP": {"Entries": [{"X": 1, "Y": 0, "T": "Layout_ShapeMinerExtension"}]}}
    pts = list_island_mining_map(decoded)
    assert len(pts) == 1
    assert pts[0]["role"] == "occupied"
    assert pts[0]["surface"] == "shape"
    assert pts[0]["layout_kind"] == "asteroid_field"
    assert pts[0]["source_layout_kind"] == "extension"
    assert "t" not in pts[0]
    assert classify_layout_type("Layout_ShapeMinerExtension") == PlotStyle.extension


def test_fluid_miner_layout_before_fluid_extension_prefix() -> None:
    assert classify_layout_type("Layout_FluidMiner") == PlotStyle.fluid_miner
    assert classify_layout_type("Layout_FluidMinerExtension") == PlotStyle.fluid_extension


def test_fluid_pump_maps_extraction_filter() -> None:
    decoded = {"BP": {"Entries": [{"X": 2, "Y": 1, "T": "Layout_FluidPump", "R": 0}]}}
    pts = list_island_mining_map(decoded)
    assert pts[0]["role"] == "occupied"
    assert pts[0]["surface"] == "fluid"
    assert pts[0]["layout_kind"] == "asteroid_field"
    assert pts[0]["r"] == 0
    assert pts[0]["source_layout_kind"] == "extractor"
    assert "t" not in pts[0]


def test_foundation_not_extraction() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": -3, "Y": 0, "T": "Foundation_1x1"},
                {"X": -2, "Y": 0, "T": "Foundation_2x2"},
            ]
        }
    }
    assert list_island_mining_map(decoded) == []
    assert summarize_island_entries_map(decoded)["entry_count"] == 0


def test_booster_on_map() -> None:
    decoded = {"BP": {"Entries": [{"X": 1, "Y": 2, "T": "Layout_SomeBoost_Module"}]}}
    pts = list_island_mining_map(decoded)
    assert len(pts) == 1
    assert pts[0]["role"] == "occupied"
    assert pts[0]["surface"] == "shape"
    assert pts[0]["layout_kind"] == "asteroid_field"
    assert pts[0]["source_layout_kind"] == "booster"


def test_inferred_patch_surface_follows_fluid_if_any_fluid_miner() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 1, "T": "Layout_ShapeMiner"},
                {"X": 2, "Y": 1, "T": "Layout_FluidMiner"},
                {"X": 3, "Y": 1, "T": "Layout_ShapeMiner"},
                {"X": 1, "Y": 2, "T": "Layout_ShapeMiner"},
                {"X": 3, "Y": 2, "T": "Layout_ShapeMiner"},
                {"X": 1, "Y": 3, "T": "Layout_ShapeMiner"},
                {"X": 2, "Y": 3, "T": "Layout_ShapeMiner"},
                {"X": 3, "Y": 3, "T": "Layout_ShapeMiner"},
            ]
        }
    }
    m = list_island_mining_map(decoded)
    inf = [c for c in m if c.get("role") == "inferred"]
    assert len(inf) == 1
    assert inf[0]["surface"] == "fluid"


def test_duplicate_coords_last_entry_wins() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 5, "Y": 1, "T": "Layout_ShapeMiner"},
                {"X": 5, "Y": 1, "T": "Layout_FluidExtractor", "R": 2},
            ]
        }
    }
    assert summarize_island_entries_map(decoded)["entry_count"] == 1
    assert list_island_mining_map(decoded) == [
        {
            "x": 5,
            "y": 1,
            "role": "occupied",
            "surface": "fluid",
            "r": 2,
            "layout_kind": "asteroid_field",
            "source_layout_kind": "extractor",
        },
    ]


def test_merge_with_transport_and_final_includes_inferred_interior() -> None:
    """STEP0.5 / solver_init baseline: mineable interior from final overlaid on with_transport."""

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
            ]
        }
    }
    tl = build_map_timeline(decoded)
    wt = tl[0]["mining_map"]
    fin = tl[-1]["mining_map"]
    merged = merge_with_transport_and_final_mining_map(wt, fin)
    by_xy = {(c["x"], c["y"]): c for c in merged}
    assert by_xy[(2, 2)]["role"] == "inferred"
    assert by_xy[(2, 2)]["surface"] == "shape"
    assert sum(1 for c in merged if c.get("role") == "inferred") == 1


def test_map_timeline_six_steps_fill_interior_equals_final() -> None:
    decoded = {"BP": {"Entries": [{"X": 1, "Y": 0, "T": "Layout_ShapeMiner"}]}}
    tl = build_map_timeline(decoded)
    assert len(tl) == 6
    assert [s["id"] for s in tl] == list(MAP_TIMELINE_STEP_IDS)
    assert tl[-1]["id"] == "final"
    assert tl[-2]["mining_map"] == tl[-1]["mining_map"]


def test_strip_extensions_removes_booster() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_ShapeMiner"},
                {"X": 2, "Y": 0, "T": "Layout_SomeBoost_Module"},
            ]
        }
    }
    tl = build_map_timeline(decoded)
    strip_ex = next(s for s in tl if s["id"] == "strip_extractors")
    kinds_ex = {c.get("layout_kind") for c in strip_ex["mining_map"] if c.get("role") == "occupied"}
    assert "booster" in kinds_ex
    strip_ext = next(s for s in tl if s["id"] == "strip_extensions")
    kinds_ext = {
        c.get("layout_kind") for c in strip_ext["mining_map"] if c.get("role") == "occupied"
    }
    assert kinds_ext == {"asteroid_field"}


def test_final_timeline_step_has_only_field_and_inferred_roles() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_FluidMiner"},
                {"X": 2, "Y": 0, "T": "Layout_FluidMinerExtension"},
                {"X": 3, "Y": 0, "T": "Layout_SomeBoost_Module"},
            ]
        }
    }
    final = build_map_timeline(decoded)[-1]["mining_map"]
    for c in final:
        role = c.get("role")
        assert role in ("occupied", "inferred")
        if role == "occupied":
            assert c.get("layout_kind") == "asteroid_field"
