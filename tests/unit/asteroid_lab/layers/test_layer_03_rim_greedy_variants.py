"""Traversal variant anchor order transforms (Task 5)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.rim_anchors import (
    build_ordered_outer_rim_anchors,
)
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.traversal_variants import (
    VARIANT_IDS,
    build_variant_anchor_order,
)
from tests.unit.asteroid_lab.layers.fixtures.rim_anchor_walk_map import (
    rim_walk_full_5x5_complete_map,
    rim_walk_pocket_complete_map,
)


@pytest.fixture
def base_anchors():
    return build_ordered_outer_rim_anchors(rim_walk_full_5x5_complete_map())


def test_variant_ids_are_locked() -> None:
    assert VARIANT_IDS == ("CW_TL", "CCW_TL", "CW_MID", "EDGE_INTERLEAVE")


def test_variants_preserve_anchor_set_without_duplicates(base_anchors) -> None:
    base_coords = {a.coord for a in base_anchors}
    for variant_id in VARIANT_IDS:
        ordered = build_variant_anchor_order(base_anchors, variant_id)
        assert len(ordered) == len(base_anchors)
        assert {a.coord for a in ordered} == base_coords
        assert len({a.coord for a in ordered}) == len(ordered)


def test_ccw_keeps_same_start_and_reverses_tail(base_anchors) -> None:
    ccw = build_variant_anchor_order(base_anchors, "CCW_TL")
    assert ccw[0].coord == base_anchors[0].coord
    assert [a.coord for a in ccw[1:]] == [a.coord for a in reversed(base_anchors[1:])]


def test_cw_tl_is_identity(base_anchors) -> None:
    cw = build_variant_anchor_order(base_anchors, "CW_TL")
    assert [a.coord for a in cw] == [a.coord for a in base_anchors]


def test_variants_are_deterministic(base_anchors) -> None:
    for variant_id in VARIANT_IDS:
        first = build_variant_anchor_order(base_anchors, variant_id)
        second = build_variant_anchor_order(base_anchors, variant_id)
        assert [a.coord for a in first] == [a.coord for a in second]


def test_variants_are_distinct_on_asymmetric_map() -> None:
    anchors = build_ordered_outer_rim_anchors(rim_walk_pocket_complete_map())
    orders = {
        variant_id: tuple(a.coord for a in build_variant_anchor_order(anchors, variant_id))
        for variant_id in VARIANT_IDS
    }
    unique_orders = set(orders.values())
    assert len(unique_orders) >= 2


def test_unknown_variant_rejected(base_anchors) -> None:
    with pytest.raises(ValueError, match="unknown variant_id"):
        build_variant_anchor_order(base_anchors, "INVALID_VARIANT")
