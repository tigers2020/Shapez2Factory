"""Tests for ``django_apps.shapez_core.domain.crystal_geometry``."""

import pytest

from django_apps.shapez_core.domain.crystal_geometry import (
    connected_crystal_cluster,
    crystal_fill_gaps_and_pins,
    highest_used_layer_index,
    shatter_crystal_cluster,
)
from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_codec import shape_from_pattern


def _shape(code: str):
    return shape_from_pattern(parse_shape_code_list(code)[0])


def test_highest_used_layer_index_top_nonempty() -> None:
    s = _shape("Ru----Ru:----Cu--")
    assert highest_used_layer_index(s) == 1


def test_crystal_fill_two_layers() -> None:
    s = _shape("Ru----Ru:----Cu--")
    out = crystal_fill_gaps_and_pins(s, "c")
    assert out.layers[1].quadrants[2].kind == "C"
    assert out.layers[1].quadrants[2].color == "u"
    assert out.layers[1].quadrants[0].is_crystal


def test_connected_cluster_adjacent_same_layer() -> None:
    # Two cyan crystals SW and NW on one layer: cc cc -- --
    s = _shape("cccc----")
    cluster = connected_crystal_cluster(s, 0, 0)
    assert cluster == frozenset({(0, 0), (0, 1)})


def test_shatter_removes_entire_cluster() -> None:
    s = _shape("cccc----")
    cluster = connected_crystal_cluster(s, 0, 0)
    out = shatter_crystal_cluster(s, cluster)
    assert out.canonical_code == "--------"


def test_invalid_color_raises() -> None:
    with pytest.raises(ValueError, match="invalid crystal color"):
        crystal_fill_gaps_and_pins(_shape("CuCuCuCu"), "z")
