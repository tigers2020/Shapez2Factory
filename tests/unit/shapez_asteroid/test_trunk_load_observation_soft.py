"""Soft diagnostics: trunk edge observation vs final map."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.trunk_load_observation_soft import (  # noqa: E501
    trunk_load_observation_soft_warnings,
)


def test_trunk_observation_soft_warns_when_endpoint_missing() -> None:
    mining_map = [
        {"x": 1, "y": 0, "role": "belt", "surface": "shape"},
    ]
    trunk_load = {
        "transport_usage_load": {
            "trunk_edge_load": {"shape_belt": {"1,0--2,0": 3}},
        },
    }
    w = trunk_load_observation_soft_warnings(mining_map, trunk_load)
    assert any("missing_transport" in s for s in w)


def test_trunk_observation_soft_clean_when_edge_endpoints_present() -> None:
    mining_map = [
        {"x": 1, "y": 0, "role": "belt", "surface": "shape"},
        {"x": 2, "y": 0, "role": "belt", "surface": "shape"},
    ]
    trunk_load = {
        "transport_usage_load": {
            "trunk_edge_load": {"shape_belt": {"1,0--2,0": 3}},
        },
    }
    assert trunk_load_observation_soft_warnings(mining_map, trunk_load) == []
