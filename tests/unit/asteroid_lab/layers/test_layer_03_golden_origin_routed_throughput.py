"""L3 rim throughput on golden_map_origin (regression: corridor sharing, not 13-cap)."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest
from django.core.management import call_command

from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import MINER_SEED_SCHEMA_V2
from django_apps.asteroid_lab.models import GeneSeed
from django_apps.asteroid_lab.services.genetic_sample_catalog_snapshot import (
    build_genetic_sample_seed_snapshot,
)
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
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.rim_throughput import (  # noqa: E501
    GOLDEN_ORIGIN_MIN_ROUTED_SHAPE_THROUGHPUT_PER_MIN,
    SHAPE_MINI_UNIT_OUTPUT_PER_MIN,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from shapez2_factory.application.asteroid_lab.run_stack import _capacity_envelope
from shapez2_factory.domain.asteroid_lab.cleanup.pipeline import deconstruct_snapshot
from shapez2_factory.domain.asteroid_lab.reconstruction.complete_map import (
    build_reconstruction_complete_map,
)
from shapez2_factory.domain.asteroid_lab.reconstruction.pipeline import run_topology_reconstruction
from shapez2_factory.domain.asteroid_lab.reconstruction.topology_contract import (
    decode_shapez_copy_string,
)

pytestmark = pytest.mark.django_db

_FIXTURE_ROOT = Path(__file__).resolve().parents[3] / "fixtures" / "asteroid_lab"
_GOLDEN_ORIGIN = _FIXTURE_ROOT / "golden_map_origin.txt"
_SNAPSHOT = _FIXTURE_ROOT / "game_data_snapshot_min.json"


def _miner_seed_snapshot() -> GeneticSampleSeedSnapshot:
    call_command("seed_miner_patterns", verbosity=0)
    payload = build_genetic_sample_seed_snapshot(
        GeneSeed.objects.filter(metadata_json__schema=MINER_SEED_SCHEMA_V2),
    )
    return GeneticSampleSeedSnapshot.from_payload(payload)


def _golden_origin_l3() -> tuple[object, GeneticSampleSeedSnapshot]:
    rules = JsonSnapshotGameDataRulesAdapter.from_file(_SNAPSHOT)
    copy = _GOLDEN_ORIGIN.read_text(encoding="utf-8").strip().splitlines()[0]
    cleanup = deconstruct_snapshot(decode_shapez_copy_string(copy))
    complete_map = build_reconstruction_complete_map(
        cleanup=cleanup,
        recon=run_topology_reconstruction(cleanup),
    )
    capacity = _capacity_envelope(
        shape_field_cell_count=complete_map.shape_field_cell_count,
        fluid_field_cell_count=complete_map.fluid_field_cell_count,
        rules=rules,
    )
    exterior_plan = run_layer_02_exterior_transport(
        complete_map=complete_map,
        capacity_envelope=capacity,
        throughput_target_percent=80,
        speed_tier=1,
        rules=rules,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
    snapshot = _miner_seed_snapshot()
    result = run_layer_03_rim_greedy_placement(
        complete_map=complete_map,
        exterior_plan=exterior_plan,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        genetic_sample_seeds=snapshot,
    )
    return result, snapshot


def test_golden_origin_commits_most_rim_anchors_not_thirteen_cap() -> None:
    result, _snapshot = _golden_origin_l3()
    assert result.metrics.layer_skip_reason is None
    assert result.metrics.committed_placement_count >= 78
    assert result.metrics.rim_anchor_count == 81


def test_golden_origin_routed_shape_throughput_meets_l3_target() -> None:
    """Was ~6,240/min (13×480) when void corridors were hard-blocked."""

    result, snapshot = _golden_origin_l3()
    tf_by_gene = {entry.gene_id: entry.throughput_factor for entry in snapshot.entries}
    routed = sum(
        int(Decimal(tf_by_gene[p.seed_id]) * Decimal(SHAPE_MINI_UNIT_OUTPUT_PER_MIN))
        for p in result.committed_placements
    )
    assert routed >= GOLDEN_ORIGIN_MIN_ROUTED_SHAPE_THROUGHPUT_PER_MIN
    assert routed > 13 * 16 * SHAPE_MINI_UNIT_OUTPUT_PER_MIN
    assert routed == int((result.metrics.pass2_score or 0) * SHAPE_MINI_UNIT_OUTPUT_PER_MIN)
