"""Footprint transform contract (spec §T / Amendment 6) ??pure geometry.

Locks the full-footprint D4 transform primitives (``rotate_xy`` / ``rotate_r`` /
``mirror_xy`` / ``mirror_r``) and the deduplicated D4 enumeration. A rotation/mirror
variant transforms equipment coordinates AND building ``R`` together (T1); mirror is a
distinct transform from rotation, so asymmetric layouts keep both while symmetric ones
collapse after full normalization (T3).
"""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.footprint_transform import (  # noqa: E501
    FootprintVariant,
    enumerate_d4,
    mirror_r,
    mirror_xy,
    rotate_r,
    rotate_xy,
)


def test_rotate_xy_quarter_turns_clockwise() -> None:
    # canonical East output (1, 0) rotates clockwise (y-down frame).
    assert rotate_xy(1, 0, 0) == (1, 0)
    assert rotate_xy(1, 0, 1) == (0, 1)
    assert rotate_xy(1, 0, 2) == (-1, 0)
    assert rotate_xy(1, 0, 3) == (0, -1)


def test_rotate_xy_locked_extension_vectors_t5() -> None:
    # canonical-East extension at (-3, 0): E->S, E->W, E->N.
    assert rotate_xy(-3, 0, 1) == (0, -3)
    assert rotate_xy(-3, 0, 2) == (3, 0)
    assert rotate_xy(-3, 0, 3) == (0, 3)


def test_rotate_r_is_additive_mod4() -> None:
    assert rotate_r(0, 0) == 0
    assert rotate_r(0, 1) == 1
    assert rotate_r(0, 2) == 2
    assert rotate_r(3, 1) == 0


def test_mirror_xy_axes() -> None:
    # mirror_x reflects across the vertical axis (East<->West, N/S fixed).
    assert mirror_xy(1, 0, "x") == (-1, 0)
    assert mirror_xy(0, 1, "x") == (0, 1)
    # mirror_y reflects across the horizontal axis (North<->South, E/W fixed).
    assert mirror_xy(1, 0, "y") == (1, 0)
    assert mirror_xy(0, 1, "y") == (0, -1)


def test_mirror_r_axes() -> None:
    assert mirror_r(0, "x") == 2  # East -> West
    assert mirror_r(2, "x") == 0
    assert mirror_r(1, "x") == 1  # South fixed
    assert mirror_r(3, "x") == 3
    assert mirror_r(1, "y") == 3  # South -> North
    assert mirror_r(0, "y") == 0  # East fixed


def test_enumerate_d4_straight_line_dedups_mirror_to_four_t3() -> None:
    # A symmetric straight line: mirror coincides with a rotation after full
    # normalization (same coords AND same R), so only 4 unique variants survive.
    variants = enumerate_d4(extractor_offset=(0, 0), extension_offsets=((-1, 0), (-2, 0), (-3, 0)))
    assert all(isinstance(v, FootprintVariant) for v in variants)
    assert len(variants) == 4
    ext_cell_sets = {frozenset((c[0], c[1]) for c in v.extension_cells) for v in variants}
    assert ext_cell_sets == {
        frozenset({(-1, 0), (-2, 0), (-3, 0)}),
        frozenset({(0, -1), (0, -2), (0, -3)}),
        frozenset({(1, 0), (2, 0), (3, 0)}),
        frozenset({(0, 1), (0, 2), (0, 3)}),
    }


def test_enumerate_d4_corner_keeps_mirror_distinct_eight_t3() -> None:
    # An asymmetric L (corner) layout: 180-rotation != mirror, so all 8 D4 variants
    # are geometrically distinct and none are deduped.
    variants = enumerate_d4(extractor_offset=(0, 0), extension_offsets=((-1, 0), (-2, 0), (0, -1)))
    assert len(variants) == 8
    keys = {v.normalized_key for v in variants}
    assert len(keys) == 8


def test_enumerate_d4_transforms_coordinates_and_r_together_t1() -> None:
    # T1: each variant transforms coordinates and building R jointly; a pure 90 CW
    # rotation maps extension (-1, 0, R=0) -> (0, -1, R=1).
    variants = enumerate_d4(extractor_offset=(0, 0), extension_offsets=((-1, 0),))
    by_kind = {(v.mirrored, v.orientation_k): v for v in variants}
    rot1 = by_kind[(False, 1)]
    assert rot1.extension_cells == ((0, -1, 1),)
