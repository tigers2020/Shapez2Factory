"""Absolute routed shape throughput from committed rim bundles (CANON mini-unit rate)."""

from __future__ import annotations

from decimal import Decimal

from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import (
    RouteProbedBundleCandidate,
)
from shapez2_factory.application.asteroid_lab.reconstruction_capacity import (
    output_per_min_from_mini_unit,
)

# Project-verified bases (documents/game_rules/shapez2_asteroid_space_transport_throughput.md).
SHAPE_MINI_UNIT_OUTPUT_PER_MIN = 30
FLUID_MINI_UNIT_OUTPUT_PER_MIN = 300

# L3 golden-map-origin regression floor (rim-only one-bundle-per-anchor packing).
# Theoretical upper bound: rim_anchor_count × m3e(16) × 30/min (e.g. 81×480 = 38_880).
GOLDEN_ORIGIN_MIN_ROUTED_SHAPE_THROUGHPUT_PER_MIN = 35_000


def routed_shape_throughput_per_min(
    selected: tuple[RouteProbedBundleCandidate, ...],
) -> int:
    """Sum ``mini_unit_output × throughput_factor`` for shape-rim commits."""

    total = 0
    for probed in selected:
        total += int(
            output_per_min_from_mini_unit(
                Decimal(SHAPE_MINI_UNIT_OUTPUT_PER_MIN),
                probed.candidate.throughput_factor,
            )
        )
    return total


def mini_unit_output_per_min_for_resource(resource_kind: str) -> Decimal:
    if resource_kind == "fluid":
        return Decimal(FLUID_MINI_UNIT_OUTPUT_PER_MIN)
    return Decimal(SHAPE_MINI_UNIT_OUTPUT_PER_MIN)


__all__ = [
    "FLUID_MINI_UNIT_OUTPUT_PER_MIN",
    "GOLDEN_ORIGIN_MIN_ROUTED_SHAPE_THROUGHPUT_PER_MIN",
    "SHAPE_MINI_UNIT_OUTPUT_PER_MIN",
    "mini_unit_output_per_min_for_resource",
    "routed_shape_throughput_per_min",
]
