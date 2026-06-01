"""L3 commit reprobe: void belt trunks are not hard-blocked (CANON 12:1 miner-to-belt)."""

from __future__ import annotations

import inspect

from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement import (
    commit_reprobe,
)


def test_commit_reprobe_hard_blockers_are_equipment_only() -> None:
    """Regression: ``state.corridor`` must not appear in walkable blockers."""

    source = inspect.getsource(commit_reprobe.try_commit_reprobe)
    blockers_line = next(
        line for line in source.splitlines() if line.strip().startswith("blockers =")
    )
    assert blockers_line.strip() == "blockers = state.occupied | set(own_equipment)"
    assert "state.corridor" not in blockers_line
