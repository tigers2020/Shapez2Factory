"""STEP4 route failure replay overlay (bounded samples, deterministic merge)."""

from __future__ import annotations

import json

from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_route_failure_replay_overlay as s4rro,
)


def test_merge_step4_route_failure_replay_overlay_sorted_and_bounded() -> None:
    rows = [
        {
            "step4_route_failure_detail": {
                "step4_replay_overlay": {
                    "failed_stub_cells": [[5, 2], [1, 1]],
                    "failed_placement_ids": ["p2-000002", "p2-000001"],
                    "blocked_frontier_sample": [[6, 2], [5, 3]],
                    "nearest_blocked_cell": [[6, 2]],
                    "nearest_blocked_zone": ["blocked"],
                    "route_goal_cells_sample": [[10, 10], [9, 9]],
                    "reachable_goal_cells_sample": [[9, 9]],
                    "existing_trunk_cells_sample": [[8, 8]],
                    "trunk_seed_cells_sample": [[7, 7]],
                    "exterior_margin_cells_sample": [[3, 0]],
                }
            }
        },
        {
            "step4_route_failure_detail": {
                "step4_replay_overlay": {
                    "failed_stub_cells": [[1, 1]],
                    "failed_placement_ids": ["p2-000001"],
                    "blocked_frontier_sample": [[5, 1]],
                    "route_goal_cells_sample": [[11, 11]],
                    "reachable_goal_cells_sample": [],
                    "existing_trunk_cells_sample": [],
                    "trunk_seed_cells_sample": [],
                    "exterior_margin_cells_sample": [],
                }
            }
        },
    ]
    rs = {
        "hard_protected_corridors": [[2, 9], [1, 8]],
        "soft_protected_corridors": [[4, 4]],
    }
    m = s4rro.merge_step4_route_failure_replay_overlay(
        routing_failures=rows,
        routing_state=rs,
        quarantined_placements=("p2-000002", "p2-000001"),
        rolled_back_placements=("p2-000002",),
    )
    assert m["failed_placement_ids"] == ["p2-000001", "p2-000002"]
    assert m["failed_stub_cells"] == [[1, 1], [5, 2]]
    assert m["hard_protected_corridors"] == [[1, 8], [2, 9]]
    assert m["soft_protected_corridors"] == [[4, 4]]
    assert m["quarantined_placements"] == ["p2-000001", "p2-000002"]
    assert m["rolled_back_placements"] == ["p2-000002"]
    s1 = json.dumps(m, sort_keys=True)
    s2 = json.dumps(m, sort_keys=True)
    assert s1 == s2


def test_overlay_module_does_not_import_merge_routing() -> None:
    from pathlib import Path

    root = Path("django_apps/shapez_asteroid/services/asteroid_mining_layout/step4")
    text = (root / "step4_route_failure_replay_overlay.py").read_text(encoding="utf-8")
    assert "step4_merge_routing" not in text
