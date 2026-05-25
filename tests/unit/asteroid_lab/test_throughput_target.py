"""Throughput target percent and budget evaluation (PR-2c)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from django_apps.asteroid_lab.services.throughput_target import (
    compute_target_throughput_per_min,
    evaluate_throughput_budget,
    parse_throughput_target_percent,
    primary_reconstruction_max_per_min,
    throughput_utilization_ratios,
)


def test_parse_defaults_to_80() -> None:
    assert parse_throughput_target_percent({}) == 80


def test_parse_rejects_below_10() -> None:
    with pytest.raises(ValueError, match="10"):
        parse_throughput_target_percent({"throughput_target_percent": 9})


def test_parse_rejects_above_80() -> None:
    with pytest.raises(ValueError, match="80"):
        parse_throughput_target_percent({"throughput_target_percent": 81})


def test_ceil_target_60_percent_of_4800() -> None:
    target = compute_target_throughput_per_min(
        reconstruction_max=Decimal("4800"),
        percent=60,
    )
    assert target == Decimal("2880")


def test_budget_satisfied_when_actual_ge_target() -> None:
    ev = evaluate_throughput_budget(
        actual=Decimal("3040"),
        target=Decimal("2880"),
    )
    assert ev.satisfied is True
    assert ev.shortfall == Decimal("0")


def test_budget_shortfall() -> None:
    ev = evaluate_throughput_budget(
        actual=Decimal("2400"),
        target=Decimal("2880"),
    )
    assert ev.satisfied is False
    assert ev.shortfall == Decimal("480")


def test_primary_max_from_envelope() -> None:
    env = {
        "primary_resource_kind": "shape",
        "by_resource": {
            "shape": {"max_throughput_per_min": "68160.0000"},
            "fluid": {"max_throughput_per_min": "1000.0000"},
        },
    }
    assert primary_reconstruction_max_per_min(env) == Decimal("68160.0000")


def test_utilization_ratios() -> None:
    target_u, actual_u = throughput_utilization_ratios(
        actual=Decimal("3040"),
        reconstruction_max=Decimal("4800"),
        percent=60,
    )
    assert target_u == Decimal("0.6000")
    assert actual_u == Decimal("0.6333")
