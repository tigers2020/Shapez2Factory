"""PR-2b: route-confirmed committed throughput sum (MiningExtractionRule authority)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.pattern_library import build_pattern_library
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.services.committed_throughput_summary import (
    build_actual_committed_output_per_min,
    resource_kind_for_transport,
)
from django_apps.game_data.services.mining_extraction_rules import get_active_rule


def _pattern(pattern_id: str = "lin_e_len0"):
    for row in build_pattern_library():
        if row.pattern_id == pattern_id:
            return row
    msg = f"pattern not found: {pattern_id!r}"
    raise AssertionError(msg)


def _candidate(cid: str, factor: int) -> BundleCandidate:
    pattern = _pattern()
    anchor = (0, 0)
    return BundleCandidate(
        candidate_id=cid,
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=frozenset({anchor}),
        output_stub=(1, 0),
        output_dir=pattern.output_dir,
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=factor,
        route_probe_cost=1,
        reachable=True,
    )


@pytest.mark.django_db
def test_resource_kind_for_transport_shape() -> None:
    assert resource_kind_for_transport(TransportKind.SHAPE_BELT) == "shape"


@pytest.mark.django_db
def test_resource_kind_for_transport_fluid() -> None:
    assert resource_kind_for_transport(TransportKind.FLUID_PIPE) == "fluid"


@pytest.mark.django_db
def test_build_actual_sums_committed_throughput_factors() -> None:
    rule = get_active_rule("shape")
    c1 = _candidate("a", 16)
    c2 = _candidate("b", 8)
    expected = rule.mini_unit_output_per_min * Decimal(16)
    expected += rule.mini_unit_output_per_min * Decimal(8)
    actual = build_actual_committed_output_per_min(
        committed_ids=("a", "b"),
        candidates_by_id={"a": c1, "b": c2},
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert actual == format(expected.quantize(Decimal("0.0001")), "f")


@pytest.mark.django_db
def test_build_actual_ignores_missing_candidate_id() -> None:
    c1 = _candidate("a", 4)
    actual = build_actual_committed_output_per_min(
        committed_ids=("a", "missing"),
        candidates_by_id={"a": c1},
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert actual == "120.0000"


@pytest.mark.django_db
def test_actual_committed_output_does_not_double_count_macro_parent_and_children() -> None:
    child = _candidate("child-a", 16)
    rule = get_active_rule("shape")
    expected = rule.mini_unit_output_per_min * Decimal(16)
    actual = build_actual_committed_output_per_min(
        committed_ids=("macro-m1", "child-a"),
        candidates_by_id={"child-a": child},
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert actual == format(expected.quantize(Decimal("0.0001")), "f")


@pytest.mark.django_db
def test_build_actual_empty_committed_returns_zero() -> None:
    actual = build_actual_committed_output_per_min(
        committed_ids=(),
        candidates_by_id={},
        transport_kind=TransportKind.SHAPE_BELT,
    )
    assert actual == "0.0000"
