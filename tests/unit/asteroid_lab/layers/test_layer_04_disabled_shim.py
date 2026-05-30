"""Layer 04 disabled shim (superseded by rim greedy L3)."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.layer04_disabled import LAYER04_DISABLED_REASON
from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
    run_layer_04_rim_bundle_placement,
)


def test_layer_04_shim_returns_disabled_without_side_effects() -> None:
    result = run_layer_04_rim_bundle_placement(
        complete_map=None,  # type: ignore[arg-type]
        exterior_plan=None,
        candidate_set=None,  # type: ignore[arg-type]
        budget_ctx=None,  # type: ignore[arg-type]
    )
    assert result.status == "DISABLED"
    assert result.reason == LAYER04_DISABLED_REASON
    assert result.provisional_overlay.occupied_cells == frozenset()
    assert result.replay_frames == ()
