"""ELCP Task 1 — pure lane count and target-load helpers."""

from __future__ import annotations

from decimal import Decimal

import pytest

from django_apps.asteroid_lab.optimization.routing.exterior_lane_capacity_helpers import (
    lane_target_loads_per_min,
    normalize_required_lane_count,
)


def test_normalize_required_lane_count_exact_division() -> None:
    assert (
        normalize_required_lane_count(
            max_asteroid_throughput_per_min=Decimal("5760"),
            lane_capacity_per_min=Decimal("2880"),
        )
        == 2
    )


def test_normalize_required_lane_count_partial_remainder_ceildiv() -> None:
    assert (
        normalize_required_lane_count(
            max_asteroid_throughput_per_min=Decimal("3000"),
            lane_capacity_per_min=Decimal("2880"),
        )
        == 2
    )


def test_normalize_required_lane_count_zero_numerator() -> None:
    assert (
        normalize_required_lane_count(
            max_asteroid_throughput_per_min=Decimal("0"),
            lane_capacity_per_min=Decimal("2880"),
        )
        == 0
    )


def test_normalize_required_lane_count_negative_numerator() -> None:
    assert (
        normalize_required_lane_count(
            max_asteroid_throughput_per_min=Decimal("-1"),
            lane_capacity_per_min=Decimal("2880"),
        )
        == 0
    )


def test_normalize_required_lane_count_zero_capacity() -> None:
    assert (
        normalize_required_lane_count(
            max_asteroid_throughput_per_min=Decimal("5760"),
            lane_capacity_per_min=Decimal("0"),
        )
        == 0
    )


def test_normalize_required_lane_count_negative_capacity() -> None:
    assert (
        normalize_required_lane_count(
            max_asteroid_throughput_per_min=Decimal("5760"),
            lane_capacity_per_min=Decimal("-1"),
        )
        == 0
    )


def test_lane_target_loads_exact_division() -> None:
    assert lane_target_loads_per_min(
        max_asteroid_throughput_per_min=Decimal("5760"),
        lane_capacity_per_min=Decimal("2880"),
        required_lane_count=2,
    ) == (Decimal("2880"), Decimal("2880"))


def test_lane_target_loads_partial_last_lane_only() -> None:
    assert lane_target_loads_per_min(
        max_asteroid_throughput_per_min=Decimal("3000"),
        lane_capacity_per_min=Decimal("2880"),
        required_lane_count=2,
    ) == (Decimal("2880"), Decimal("120"))


def test_lane_target_loads_required_lane_count_zero_returns_empty() -> None:
    assert (
        lane_target_loads_per_min(
            max_asteroid_throughput_per_min=Decimal("5760"),
            lane_capacity_per_min=Decimal("2880"),
            required_lane_count=0,
        )
        == ()
    )


def test_lane_target_loads_zero_throughput_returns_empty() -> None:
    assert (
        lane_target_loads_per_min(
            max_asteroid_throughput_per_min=Decimal("0"),
            lane_capacity_per_min=Decimal("2880"),
            required_lane_count=2,
        )
        == ()
    )


def test_lane_target_loads_zero_capacity_returns_empty() -> None:
    assert (
        lane_target_loads_per_min(
            max_asteroid_throughput_per_min=Decimal("5760"),
            lane_capacity_per_min=Decimal("0"),
            required_lane_count=2,
        )
        == ()
    )


@pytest.mark.parametrize(
    ("max_throughput", "capacity"),
    [
        (Decimal("5760"), Decimal("2880")),
        (Decimal("3000"), Decimal("2880")),
    ],
)
def test_lane_target_loads_sum_covers_numerator_when_positive(
    max_throughput: Decimal,
    capacity: Decimal,
) -> None:
    required = normalize_required_lane_count(
        max_asteroid_throughput_per_min=max_throughput,
        lane_capacity_per_min=capacity,
    )
    loads = lane_target_loads_per_min(
        max_asteroid_throughput_per_min=max_throughput,
        lane_capacity_per_min=capacity,
        required_lane_count=required,
    )
    assert sum(loads, start=Decimal("0")) >= max_throughput
