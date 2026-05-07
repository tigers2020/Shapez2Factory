from __future__ import annotations

from django_apps.shapez_asteroid.services.blueprint_map_summary import (
    list_island_entry_plot_points,
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
    assert list_island_entry_plot_points(decoded) == []


def test_symmetric_layout_non_extraction_yields_empty() -> None:
    decoded = {"BP": {"Entries": [{"X": -1, "Y": 0}, {"X": 1, "Y": 0}]}}
    assert summarize_island_entries_map(decoded)["entry_count"] == 0
    assert list_island_entry_plot_points(decoded) == []


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


def test_list_plot_points_unknown_layouts() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 2, "T": "Layout_A"},
                {"X": -1, "T": "Layout_B"},
                {"Y": 1},
            ]
        }
    }
    assert list_island_entry_plot_points(decoded) == []


def test_list_plot_points_non_string_t_unknown() -> None:
    decoded = {"BP": {"Entries": [{"X": 5, "Y": 0, "T": 42}]}}
    assert list_island_entry_plot_points(decoded) == []


def test_x_zero_excluded_from_bounds_and_plot() -> None:
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
    assert list_island_entry_plot_points(decoded) == [
        {"x": -2, "y": 1, "t": "Layout_ShapeMiner", "style": "miner"},
        {"x": 3, "y": 1, "t": "Layout_ShapeMiner", "style": "miner"},
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
    assert list_island_entry_plot_points(decoded) == []


def test_belt_pipe_not_in_plot_fluid_extension_only() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_UndergroundBelt", "R": 0},
                {"X": 2, "Y": 0, "T": "Layout_FluidPipe", "R": 1},
                {"X": 3, "Y": 0, "T": "Layout_FluidMinerExtension", "R": 2},
            ]
        }
    }
    pts = list_island_entry_plot_points(decoded)
    assert len(pts) == 1
    assert pts[0] == {
        "x": 3,
        "y": 0,
        "t": "Layout_FluidMinerExtension",
        "style": "fluid_extension",
        "r": 2,
    }
    assert summarize_island_entries_map(decoded)["entry_count"] == 1


def test_plot_style_extractor_vs_fluid_extension() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_FluidExtractor"},
                {"X": 2, "Y": 0, "T": "Layout_FluidMinerExtension"},
            ]
        }
    }
    pts = list_island_entry_plot_points(decoded)
    assert pts[0]["style"] == "extractor"
    assert pts[1]["style"] == "fluid_extension"
    assert list_island_entry_plot_points({}) == []


def test_plot_style_shape_miner() -> None:
    decoded = {"BP": {"Entries": [{"X": 4, "Y": 0, "T": "Layout_ShapeMiner", "R": 1}]}}
    assert list_island_entry_plot_points(decoded) == [
        {"x": 4, "y": 0, "t": "Layout_ShapeMiner", "style": "miner", "r": 1},
    ]


def test_shape_miner_extension_is_extension_not_miner() -> None:
    decoded = {"BP": {"Entries": [{"X": 1, "Y": 0, "T": "Layout_ShapeMinerExtension"}]}}
    pts = list_island_entry_plot_points(decoded)
    assert len(pts) == 1
    assert pts[0]["style"] == "extension"
    assert classify_layout_type("Layout_ShapeMinerExtension") == PlotStyle.extension
    assert classify_layout_type("Layout_ShapeMinerExtension") != PlotStyle.miner


def test_fluid_miner_layout_before_fluid_extension_prefix() -> None:
    assert classify_layout_type("Layout_FluidMiner") == PlotStyle.fluid_miner
    assert classify_layout_type("Layout_FluidMinerExtension") == PlotStyle.fluid_extension


def test_plot_style_fluid_pump_maps_extractor() -> None:
    decoded = {"BP": {"Entries": [{"X": 2, "Y": 1, "T": "Layout_FluidPump", "R": 0}]}}
    pts = list_island_entry_plot_points(decoded)
    assert pts[0]["style"] == "extractor"


def test_foundation_not_extraction() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": -3, "Y": 0, "T": "Foundation_1x1"},
                {"X": -2, "Y": 0, "T": "Foundation_2x2"},
            ]
        }
    }
    assert list_island_entry_plot_points(decoded) == []
    assert summarize_island_entries_map(decoded)["entry_count"] == 0


def test_booster_extraction() -> None:
    decoded = {"BP": {"Entries": [{"X": 1, "Y": 2, "T": "Layout_SomeBoost_Module"}]}}
    pts = list_island_entry_plot_points(decoded)
    assert len(pts) == 1
    assert pts[0]["style"] == "booster"
