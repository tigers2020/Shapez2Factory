"""Regression: L3 greedy replay accepts Direction wire (lowercase n/e/s/w)."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.layer03_rim_greedy_segment import (
    _canonical_cardinal_dir,
    _placement_output_rotation,
)


def test_canonical_cardinal_dir_normalizes_lowercase_direction() -> None:
    assert _canonical_cardinal_dir("w") == "W"
    assert _canonical_cardinal_dir("E") == "E"


def test_placement_output_rotation_accepts_lowercase_west() -> None:
    assert _placement_output_rotation("w") == 2
    assert _placement_output_rotation("W") == 2
