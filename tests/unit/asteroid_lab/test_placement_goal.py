"""PR-2d placement goal policy tests."""

from __future__ import annotations

from decimal import Decimal

import pytest

from django_apps.asteroid_lab.optimization.candidates.candidate_dtos import BundleCandidate
from django_apps.asteroid_lab.optimization.candidates.pattern_library import build_pattern_library
from django_apps.asteroid_lab.optimization.input_contracts import TransportKind
from django_apps.asteroid_lab.services.placement_goal import (
    DEFAULT_MAX_PLACEMENT_GOAL_COUNT,
    build_placement_goal_plan,
    parse_max_placement_goal_count,
)


def _pattern_by_id(pattern_id: str):
    for pattern in build_pattern_library():
        if pattern.pattern_id == pattern_id:
            return pattern
    msg = f"pattern not found: {pattern_id!r}"
    raise AssertionError(msg)


def _translate(anchor: tuple[int, int], offset: tuple[int, int]) -> tuple[int, int]:
    return (anchor[0] + offset[0], anchor[1] + offset[1])


def _candidate(
    anchor: tuple[int, int],
    *,
    factor: int,
    reachable: bool = True,
) -> BundleCandidate:
    pattern = _pattern_by_id("lin_e_len0")
    occupied = frozenset(_translate(anchor, off) for off in pattern.occupied_offsets)
    stub = _translate(anchor, pattern.output_stub_offset)
    return BundleCandidate(
        candidate_id=f"{anchor[0]},{anchor[1]}:{pattern.pattern_id}:shape_belt",
        anchor_coord=anchor,
        pattern=pattern,
        occupied_cells=occupied,
        output_stub=stub,
        output_dir=pattern.output_dir,
        transport_kind=TransportKind.SHAPE_BELT,
        throughput_factor=factor,
        route_probe_cost=5,
        reachable=reachable,
    )


def test_parse_max_placement_goal_defaults_to_32() -> None:
    assert parse_max_placement_goal_count({}) == DEFAULT_MAX_PLACEMENT_GOAL_COUNT
    assert DEFAULT_MAX_PLACEMENT_GOAL_COUNT == 32


def test_parse_max_placement_goal_rejects_0() -> None:
    with pytest.raises(ValueError, match="1"):
        parse_max_placement_goal_count({"max_placement_goal_count": 0})


def test_parse_max_placement_goal_rejects_129() -> None:
    with pytest.raises(ValueError, match="128"):
        parse_max_placement_goal_count({"max_placement_goal_count": 129})


def test_parse_max_placement_goal_rejects_bool() -> None:
    with pytest.raises(ValueError, match="integer"):
        parse_max_placement_goal_count({"max_placement_goal_count": True})


def test_reference_slug_plan_factor4_only(monkeypatch: pytest.MonkeyPatch) -> None:
    from django_apps.game_data.models.mining import MiningExtractionRule

    rule = MiningExtractionRule(
        resource_kind="shape",
        mini_unit_output_per_min=Decimal("30"),
        max_extension_count=3,
        is_active=True,
    )

    monkeypatch.setattr(
        "django_apps.game_data.services.mining_extraction_rules.get_active_rule",
        lambda resource_kind: rule if resource_kind == "shape" else rule,
    )

    normals = tuple(_candidate((i, 0), factor=4) for i in range(20))
    plan = build_placement_goal_plan(
        normal_candidates=normals,
        transport_kind=TransportKind.SHAPE_BELT,
        target_throughput_per_min=Decimal("1536"),
        skeleton_capacity_goals=1,
        configured_max_placement_goal=32,
    )
    assert plan.best_bundle_throughput_per_min == Decimal("120")
    assert plan.bundles_needed_for_target == 13
    assert plan.placement_goal_count == 13
    assert plan.configured_max_placement_goal == 32


def test_plan_uses_factor16_when_reachable(monkeypatch: pytest.MonkeyPatch) -> None:
    from django_apps.game_data.models.mining import MiningExtractionRule

    rule = MiningExtractionRule(
        resource_kind="shape",
        mini_unit_output_per_min=Decimal("30"),
        max_extension_count=3,
        is_active=True,
    )

    monkeypatch.setattr(
        "django_apps.game_data.services.mining_extraction_rules.get_active_rule",
        lambda resource_kind: rule if resource_kind == "shape" else rule,
    )

    normals = (
        _candidate((0, 0), factor=4),
        _candidate((5, 0), factor=16),
    )
    plan = build_placement_goal_plan(
        normal_candidates=normals,
        transport_kind=TransportKind.SHAPE_BELT,
        target_throughput_per_min=Decimal("1536"),
        skeleton_capacity_goals=1,
        configured_max_placement_goal=32,
    )
    assert plan.best_bundle_throughput_per_min == Decimal("480")
    assert plan.bundles_needed_for_target == 4
    assert plan.route_feasible_candidate_cap == 2
    assert plan.placement_goal_count == 2
