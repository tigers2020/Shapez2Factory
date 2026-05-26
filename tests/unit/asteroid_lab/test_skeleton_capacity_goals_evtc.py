"""EVTC-3 — capacity_goals aligned with required exterior connectors."""

from __future__ import annotations

from dataclasses import replace

import pytest

from django_apps.asteroid_lab.optimization.input_contracts import RttpSkeletonConfig
from django_apps.asteroid_lab.optimization.skeleton.skeleton_builder import RttpSkeletonBuilder


@pytest.mark.django_db
def test_skeleton_capacity_goals_matches_required_connectors(
    greenfield_optimization_input,
    imported_game_data_batch_module: object,
) -> None:
    _ = imported_game_data_batch_module
    inp = replace(greenfield_optimization_input, required_external_connector_count=4)
    skeleton = RttpSkeletonBuilder.build(inp, config=RttpSkeletonConfig())
    assert skeleton.capacity_goals == 4
