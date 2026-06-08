"""Predictive fitness penalty profiles for Layer 03 beam selection (10B v0.1)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class PenaltyMode(StrEnum):
    """Beam-selector soft-penalty weight profiles (not solver feedback from replay)."""

    STANDARD = "standard"
    CONSERVATIVE = "conservative"


@dataclass(frozen=True, slots=True)
class BeamPenaltyWeights:
    throughput_weight: int
    route_cost_weight: int
    corridor_pressure_weight: int
    future_expansion_weight: int


_STANDARD = BeamPenaltyWeights(
    throughput_weight=1000,
    route_cost_weight=1,
    corridor_pressure_weight=10,
    future_expansion_weight=0,
)
_CONSERVATIVE = BeamPenaltyWeights(
    throughput_weight=1000,
    route_cost_weight=5,
    corridor_pressure_weight=50,
    future_expansion_weight=5000,
)


def beam_penalty_weights(mode: PenaltyMode = PenaltyMode.STANDARD) -> BeamPenaltyWeights:
    if mode is PenaltyMode.CONSERVATIVE:
        return _CONSERVATIVE
    return _STANDARD


__all__ = [
    "BeamPenaltyWeights",
    "PenaltyMode",
    "beam_penalty_weights",
]
