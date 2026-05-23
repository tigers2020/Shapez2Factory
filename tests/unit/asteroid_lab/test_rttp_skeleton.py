"""RTTP Layer 1 skeleton builder — RTTP-G1 (deterministic), RTTP-G2 (no equipment)."""

from __future__ import annotations

import dataclasses

import pytest

from django_apps.asteroid_lab.optimization.input_contracts import (
    LiftColumn,
    OptimizationInput,
    RingPort,
    RttpSkeletonConfig,
)
from django_apps.asteroid_lab.optimization.skeleton.rttp_skeleton import RttpSkeleton
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder

_EQUIPMENT_MARKERS = frozenset(
    {
        "miner",
        "extractor",
        "pump",
        "booster",
        "equipment",
        "layout_type",
        "BundlePattern",
    }
)


def default_config() -> RttpSkeletonConfig:
    return RttpSkeletonConfig()


def test_rttp_skeleton_deterministic_for_same_input(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    config = default_config()
    first = RttpSkeletonBuilder.build(greenfield_optimization_input, config=config)
    second = RttpSkeletonBuilder.build(greenfield_optimization_input, config=config)
    assert first == second
    assert first.skeleton_id == second.skeleton_id


def test_rttp_skeleton_has_no_equipment_cells(
    greenfield_optimization_input: OptimizationInput,
) -> None:
    skeleton = RttpSkeletonBuilder.build(greenfield_optimization_input, config=default_config())
    _assert_skeleton_has_no_equipment(skeleton)


def _assert_skeleton_has_no_equipment(skeleton: RttpSkeleton) -> None:
    for field in dataclasses.fields(skeleton):
        value = getattr(skeleton, field.name)
        _assert_value_is_topology_only(value, field.name)

    assert isinstance(skeleton.capacity_goals, int)
    assert skeleton.capacity_goals >= 0
    assert isinstance(skeleton.skeleton_id, str)
    assert skeleton.skeleton_id


def _assert_value_is_topology_only(value: object, path: str) -> None:
    if isinstance(value, int):
        return
    if isinstance(value, str):
        lowered = value.lower()
        for marker in _EQUIPMENT_MARKERS:
            assert marker.lower() not in lowered, f"equipment marker in {path}: {value!r}"
        return
    if (
        isinstance(value, tuple)
        and len(value) == 2
        and all(isinstance(part, int) for part in value)
    ):
        return
    if isinstance(value, frozenset):
        for item in value:
            _assert_value_is_topology_only(item, f"{path}[]")
        return
    if isinstance(value, tuple):
        for index, item in enumerate(value):
            _assert_value_is_topology_only(item, f"{path}[{index}]")
        return
    if isinstance(value, RingPort):
        _assert_value_is_topology_only(value.coord, f"{path}.coord")
        _assert_value_is_topology_only(value.preferred_dir, f"{path}.preferred_dir")
        return
    if isinstance(value, LiftColumn):
        _assert_value_is_topology_only(value.platform_coord, f"{path}.platform_coord")
        _assert_value_is_topology_only(value.lift_coord, f"{path}.lift_coord")
        _assert_value_is_topology_only(value.target_lane, f"{path}.target_lane")
        return
    pytest.fail(f"unexpected skeleton value type at {path}: {type(value)!r}")
