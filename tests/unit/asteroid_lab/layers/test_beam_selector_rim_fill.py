"""Rim anchor fill-ratio target helpers and selection policy."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.beam_selector import (
    _min_committed_anchor_count,
)


def test_min_committed_anchor_count_95_percent() -> None:
    assert _min_committed_anchor_count(55, 0.95) == 53
    assert _min_committed_anchor_count(81, 0.95) == 77
    assert _min_committed_anchor_count(0, 0.95) == 0
