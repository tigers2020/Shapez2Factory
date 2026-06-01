"""Contract tests for genetic_sample_catalog_snapshot (ORM -> genetic_sample_seed_v1 payload)."""

from __future__ import annotations

import pytest
from django.core.management import call_command

from django_apps.asteroid_lab.genetic_sample.exhaustive_generator import (
    ExhaustiveGenerationStats,
    GeneratedSampleGene,
)
from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import (
    EXPECTED_PATTERN_IDS,
    MINER_SEED_SCHEMA_V2,
)
from django_apps.asteroid_lab.models import GeneSeed
from django_apps.asteroid_lab.services.genetic_sample_catalog_snapshot import (
    MINER_SOURCE_BATCH_ID,
    SCHEMA_VERSION,
    build_genetic_sample_seed_snapshot,
)
from django_apps.asteroid_lab.services.genetic_sample_gene_export import (
    load_gene_templates_from_gene_seeds,
)
from django_apps.asteroid_lab.services.miner_gene_seed_template import (
    gene_template_from_miner_gene_seed,
)
from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
    GeneticSampleSeedSnapshot,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_budget import (
    LayerBudgetContext,
)
from shapez2_factory.application.asteroid_lab.layers.layer_03_rim_greedy_placement.run import (
    run_layer_03_rim_greedy_placement,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    expected_golden_rim_anchor_count,
    golden_5x5_complete_map,
    golden_5x5_fluid_complete_map,
    minimal_l2_plan_for_golden,
    minimal_l2_plan_for_golden_fluid,
)

pytestmark = pytest.mark.django_db

_EXPECTED_MINER_COUNT = len(EXPECTED_PATTERN_IDS)
_EXPECTED_MINER_WITH_FLUID_CLONES = _EXPECTED_MINER_COUNT * 2


def _miner_seed_queryset():
    return GeneSeed.objects.filter(
        metadata_json__schema=MINER_SEED_SCHEMA_V2,
        metadata_json__is_seed=True,
    )


def _seed_samples(
    exhaustive_genes_ext0_belt: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
    count: int,
) -> list[GeneSeed]:
    genes, _ = exhaustive_genes_ext0_belt
    assert len(genes) >= count, "exhaustive generator must produce enough genes for seeding"
    samples: list[GeneSeed] = []
    for g in genes[:count]:
        sample, _ = GeneSeed.objects.update_or_create(
            gene_key=g.key,
            defaults={
                "name": g.name,
                "code": g.encoded_copy_string,
                "metadata_json": dict(g.metadata),
            },
        )
        samples.append(sample)
    return samples


def test_build_genetic_sample_seed_snapshot_round_trips(
    exhaustive_genes_ext0_belt: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
) -> None:
    GeneSeed.objects.all().delete()
    _seed_samples(exhaustive_genes_ext0_belt, 1)
    payload = build_genetic_sample_seed_snapshot(GeneSeed.objects.all())

    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["deterministic_sort_key"] == "by_gene_id_then_throughput_desc"
    assert len(payload["entries"]) >= 1
    assert all(e["canonical_output_dir"] == "E" for e in payload["entries"])

    snapshot = GeneticSampleSeedSnapshot.from_payload(payload)
    assert len(snapshot.entries) >= 1


def test_build_genetic_sample_seed_snapshot_empty_queryset() -> None:
    payload = build_genetic_sample_seed_snapshot(GeneSeed.objects.none())
    assert payload["entries"] == []

    snapshot = GeneticSampleSeedSnapshot.from_payload(payload)
    assert snapshot.entries == ()


def test_build_genetic_sample_seed_snapshot_from_miner_seed_v2_entries() -> None:
    call_command("seed_miner_patterns", verbosity=0)
    qs = _miner_seed_queryset()
    assert qs.count() == _EXPECTED_MINER_COUNT

    payload = build_genetic_sample_seed_snapshot(qs)
    assert payload["source_batch_id"] == MINER_SOURCE_BATCH_ID
    assert len(payload["entries"]) == _EXPECTED_MINER_WITH_FLUID_CLONES
    assert all(e["canonical_output_dir"] == "E" for e in payload["entries"])
    shape_entries = [e for e in payload["entries"] if e["resource_kind"] == "shape"]
    fluid_entries = [e for e in payload["entries"] if e["resource_kind"] == "fluid"]
    assert len(shape_entries) == _EXPECTED_MINER_COUNT
    assert len(fluid_entries) == _EXPECTED_MINER_COUNT
    assert all(e["gene_id"].startswith("fluid_miner_seed_") for e in fluid_entries)

    snapshot = GeneticSampleSeedSnapshot.from_payload(payload)
    assert len(snapshot.entries) == _EXPECTED_MINER_WITH_FLUID_CLONES


def test_miner_seed_v2_does_not_require_exhaustive_cache() -> None:
    call_command("seed_miner_patterns", verbosity=0)
    row = GeneSeed.objects.get(gene_key="miner_seed_m0e_01")
    template, err = gene_template_from_miner_gene_seed(row)
    assert err is None
    assert template is not None
    assert template.gene_id == "miner_seed_m0e_01"
    assert template.extractor_offset == (0, 0)
    assert template.fixed_output_transport_offset == (1, 0)


def test_miner_seed_v2_snapshot_ignores_exhaustive_rows_when_miners_present(
    exhaustive_genes_ext0_belt: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
) -> None:
    call_command("seed_miner_patterns", verbosity=0)
    _seed_samples(exhaustive_genes_ext0_belt, 1)

    payload = build_genetic_sample_seed_snapshot(GeneSeed.objects.all())
    assert payload["source_batch_id"] == MINER_SOURCE_BATCH_ID
    assert len(payload["entries"]) == _EXPECTED_MINER_WITH_FLUID_CLONES


def test_miner_seed_v2_invalid_decoded_json_is_skipped() -> None:
    call_command("seed_miner_patterns", verbosity=0)
    row = GeneSeed.objects.get(gene_key="miner_seed_m0e_01")
    GeneSeed.objects.filter(pk=row.pk).update(decoded_json={})

    templates, skipped, errors = load_gene_templates_from_gene_seeds(
        GeneSeed.objects.filter(pk=row.pk)
    )
    assert templates == ()
    assert skipped == 1
    assert "missing_decoded_json" in errors


def test_exhaustive_path_only_when_no_miner_seed_v2_rows(
    exhaustive_genes_ext1_belt: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
) -> None:
    GeneSeed.objects.all().delete()
    _seed_samples(exhaustive_genes_ext1_belt, 2)
    payload = build_genetic_sample_seed_snapshot(GeneSeed.objects.all())
    assert payload["source_batch_id"] == "exhaustive_sample_gene_v1"
    assert len(payload["entries"]) == 2


def test_l3_runs_with_miner_seed_v2_snapshot() -> None:
    call_command("seed_miner_patterns", verbosity=0)
    payload = build_genetic_sample_seed_snapshot(_miner_seed_queryset())
    snapshot = GeneticSampleSeedSnapshot.from_payload(payload)

    result = run_layer_03_rim_greedy_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        genetic_sample_seeds=snapshot,
    )
    assert result.metrics.layer_skip_reason is None
    assert result.metrics.rim_anchor_count == expected_golden_rim_anchor_count()
    assert result.metrics.committed_placement_count >= 1


def test_l3_fluid_map_uses_fluid_gene_clones_from_shape_pool() -> None:
    call_command("seed_miner_patterns", verbosity=0)
    payload = build_genetic_sample_seed_snapshot(_miner_seed_queryset())
    snapshot = GeneticSampleSeedSnapshot.from_payload(payload)

    result = run_layer_03_rim_greedy_placement(
        complete_map=golden_5x5_fluid_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden_fluid(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        genetic_sample_seeds=snapshot,
    )
    assert result.metrics.layer_skip_reason is None
    assert result.metrics.rim_anchor_count == expected_golden_rim_anchor_count()
    assert result.metrics.committed_placement_count >= 1
    assert all(p.seed_id.startswith("fluid_miner_seed_") for p in result.committed_placements)


def test_build_genetic_sample_seed_snapshot_entries_sorted_by_gene_id(
    exhaustive_genes_ext1_belt: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
) -> None:
    GeneSeed.objects.all().delete()
    _seed_samples(exhaustive_genes_ext1_belt, 2)
    payload = build_genetic_sample_seed_snapshot(GeneSeed.objects.all())

    assert len(payload["entries"]) >= 2
    gene_ids = [e["gene_id"] for e in payload["entries"]]
    assert gene_ids == sorted(gene_ids)
