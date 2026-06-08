"""PenaltyMode contract for Layer 03 beam selector (10B v0.1)."""

from __future__ import annotations

from shapez2_factory.application.asteroid_lab.layers.contracts.penalty_mode import (
    PenaltyMode,
    beam_penalty_weights,
)


def test_penalty_mode_enum_values() -> None:
    assert PenaltyMode.STANDARD.value == "standard"
    assert PenaltyMode.CONSERVATIVE.value == "conservative"


def test_conservative_weights_are_stricter_than_standard() -> None:
    standard = beam_penalty_weights(PenaltyMode.STANDARD)
    conservative = beam_penalty_weights(PenaltyMode.CONSERVATIVE)
    assert conservative.throughput_weight == standard.throughput_weight
    assert conservative.route_cost_weight > standard.route_cost_weight
    assert conservative.corridor_pressure_weight > standard.corridor_pressure_weight
    assert conservative.future_expansion_weight > standard.future_expansion_weight
