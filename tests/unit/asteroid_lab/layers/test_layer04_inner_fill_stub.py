"""Layer 04 inner fill stub contract (PR-1 renumber)."""

from __future__ import annotations

import inspect

from shapez2_factory.application.asteroid_lab.layers.layer_05_inner_pattern_fill.run import (
    run_layer_04_inner_pattern_fill,
)


def test_inner_fill_stub_has_no_route_plan_parameter() -> None:
    params = inspect.signature(run_layer_04_inner_pattern_fill).parameters
    assert "layer04_route_plan" not in params
    assert "layer05_route_plan" not in params
