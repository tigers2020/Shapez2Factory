"""Regression: L3 route probe budget must cover all rim anchors on large fluid maps."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shapez2_factory.adapters.asteroid_lab.complete_map_serializer import parse_complete_map
from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
    GeneticSampleSeedSnapshot,
)
from shapez2_factory.adapters.asteroid_lab.json_snapshot_rules import (
    JsonSnapshotGameDataRulesAdapter,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport.run import (
    run_layer_02_exterior_transport,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from shapez2_factory.application.asteroid_lab.run_stack import _capacity_envelope

_ARTIFACT_RUN = Path(__file__).resolve().parents[4] / (
    "var/runs/asteroid-23-d6e546dee6e34b8fbba3790c50ae5984"
)


@pytest.mark.skipif(
    not _ARTIFACT_RUN.is_dir(),
    reason="requires local CLI artifact run (fluid 307-cell map)",
)
def test_large_fluid_map_all_rim_anchors_route_feasible_in_pool() -> None:
    """Run #437 class map: fixed 64-cell probe falsely left 35/55 anchors unreachable."""

    complete_map = parse_complete_map(
        json.loads((_ARTIFACT_RUN / "output/layer01_complete_map.json").read_text()),
    )
    seeds = GeneticSampleSeedSnapshot.from_payload(
        json.loads((_ARTIFACT_RUN / "input/genetic_sample_seeds.json").read_text()),
    )
    rules = JsonSnapshotGameDataRulesAdapter.from_payload(
        json.loads((_ARTIFACT_RUN / "input/game_data_snapshot.json").read_text()),
    )
    capacity = _capacity_envelope(complete_map=complete_map, rules=rules)
    exterior_plan = run_layer_02_exterior_transport(
        complete_map=complete_map,
        capacity_envelope=capacity,
        throughput_target_percent=80,
        speed_tier=1,
        rules=rules,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
    result = run_layer_03_rim_greedy_placement(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        genetic_sample_seeds=seeds,
    )
    rim = result.metrics.rim_anchor_count
    feasible = result.metrics.route_feasible_rim_anchor_count
    committed = result.metrics.committed_placement_count
    assert rim == 55
    assert feasible == rim, f"expected every rim anchor in normal pool, got {feasible}/{rim}"
    assert committed >= int(0.95 * rim), f"expected >=95% commit, got {committed}/{rim}"
