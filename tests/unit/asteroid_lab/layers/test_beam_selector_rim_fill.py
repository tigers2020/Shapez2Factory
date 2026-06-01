"""Rim anchor fill-ratio target helpers and selection policy."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement import (
    beam_selector,
)


def test_min_committed_anchor_count_95_percent() -> None:
    assert beam_selector._min_committed_anchor_count(55, 0.95) == 53
    assert beam_selector._min_committed_anchor_count(81, 0.95) == 77
    assert beam_selector._min_committed_anchor_count(0, 0.95) == 0
