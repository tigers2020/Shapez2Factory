"""Sequence 10A determinism: identical L3 outputs for narrow-corridor fixtures."""

from __future__ import annotations

import hashlib

from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.rim_greedy import (
    IntegratedRimGreedyResult,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from tests.unit.asteroid_lab.layers.fixtures.narrow_corridor_maps import (
    s3_corridor_sharing_catalog,
    s3_corridor_sharing_complete_map,
    s3_corridor_sharing_exterior_plan,
)


def _output_hash(result: IntegratedRimGreedyResult) -> str:
    parts: list[str] = []
    for placement in result.committed_placements:
        parts.append(
            "|".join(
                [
                    placement.placement_id,
                    str(placement.anchor),
                    placement.output_dir,
                    str(sorted(placement.miner_cells)),
                    str(sorted(placement.extension_cells)),
                    str(placement.m_output_stub),
                    str(placement.route_probe_path),
                ]
            )
        )
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()


def _run_s3_corridor() -> IntegratedRimGreedyResult:
    return run_layer_03_rim_greedy_placement(
        complete_map=s3_corridor_sharing_complete_map(),
        exterior_plan=s3_corridor_sharing_exterior_plan(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        genetic_sample_seeds=s3_corridor_sharing_catalog(),
    )


def test_narrow_corridor_s3_l3_output_is_deterministic() -> None:
    first = _run_s3_corridor()
    second = _run_s3_corridor()
    assert [p.placement_id for p in first.committed_placements] == [
        p.placement_id for p in second.committed_placements
    ]
    assert first.reserved_route_cells == second.reserved_route_cells
    assert first.occupied_equipment_cells == second.occupied_equipment_cells
    assert _output_hash(first) == _output_hash(second)
