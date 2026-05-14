"""Pass2 exterior-margin diagnostic: universe-outside neighbors vs ``is_external`` shell."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass12_route_probe as p12rp,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
    final_validation as fin,
)


def _two_miners_map() -> list[dict[str, Any]]:
    row = {
        "role": "occupied",
        "layout_kind": "miner",
        "surface": "shape",
        "t": "C",
        "r": 0,
    }
    return [
        {**row, "x": 10, "y": 0},
        {**row, "x": 11, "y": 0},
    ]


def test_margin_generation_flags_outside_universe_void_inside_predicate_shell() -> None:
    """Void neighbor outside ``cells`` keys can still sit inside bbox±margin → margin stays 0."""

    mining_map = _two_miners_map()
    shell = fin.external_bbox_margin_for_mining_map(mining_map)
    assert shell is not None
    bbox_t, margin = shell
    pred = fin.external_predicate_for_mining_map(mining_map)
    universe = {(10, 0), (11, 0)}
    diag = p12rp._build_pass2_external_margin_diagnostic(
        universe=universe,
        margin=set(),
        is_external=pred,
        bbox={"x_min": 10, "x_max": 11, "y_min": 0, "y_max": 0},
        is_external_shell_bbox=bbox_t,
        is_external_shell_margin=margin,
    )
    assert diag["sampled_neighbor_outside_universe_count"] >= 1
    assert diag["is_external_true_neighbor_sample_count"] == 0
    reasons = diag.get("margin_generation_reason_if_zero") or []
    assert "outside_universe_neighbors_inside_predicate_shell_padding" in reasons
    assert diag.get("exterior_margin_status") == "predicate_shell_padding_suppressed"
