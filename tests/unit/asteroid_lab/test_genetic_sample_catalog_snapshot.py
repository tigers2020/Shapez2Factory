"""Contract tests for genetic_sample_catalog_snapshot (ORM -> gene_catalog_v1 payload)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.genetic_sample.exhaustive_generator import (
    ExhaustiveGenerationStats,
    GeneratedSampleGene,
)
from django_apps.asteroid_lab.models import GeneticSample
from django_apps.asteroid_lab.services.genetic_sample_catalog_snapshot import (
    SCHEMA_VERSION,
    build_gene_catalog_snapshot,
)
from shapez2_factory.adapters.asteroid_lab.gene_catalog_snapshot import GeneCatalogSnapshot

pytestmark = pytest.mark.django_db


def _seed_samples(
    exhaustive_genes_ext0_belt: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
    count: int,
) -> list[GeneticSample]:
    genes, _ = exhaustive_genes_ext0_belt
    assert len(genes) >= count, "exhaustive generator must produce enough genes for seeding"
    samples: list[GeneticSample] = []
    for g in genes[:count]:
        sample, _ = GeneticSample.objects.update_or_create(
            gene_key=g.key,
            defaults={
                "name": g.name,
                "code": g.encoded_copy_string,
                "metadata_json": dict(g.metadata),
            },
        )
        samples.append(sample)
    return samples


def test_build_gene_catalog_snapshot_round_trips(
    exhaustive_genes_ext0_belt: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
) -> None:
    _seed_samples(exhaustive_genes_ext0_belt, 1)
    payload = build_gene_catalog_snapshot(GeneticSample.objects.all())

    assert payload["schema_version"] == SCHEMA_VERSION
    assert payload["schema_version"] == "gene_catalog_v1"
    assert payload["deterministic_sort_key"] == "by_gene_id_then_throughput_desc"
    assert isinstance(payload["entries"], list)
    assert len(payload["entries"]) >= 1
    assert all(e["canonical_output_dir"] == "E" for e in payload["entries"])

    snapshot = GeneCatalogSnapshot.from_payload(payload)
    assert snapshot.schema_version == "gene_catalog_v1"
    assert len(snapshot.entries) >= 1
    assert all(e.canonical_output_dir == "E" for e in snapshot.entries)


def test_build_gene_catalog_snapshot_empty_queryset() -> None:
    payload = build_gene_catalog_snapshot(GeneticSample.objects.none())
    assert payload["entries"] == []

    snapshot = GeneCatalogSnapshot.from_payload(payload)
    assert snapshot.entries == ()


def test_build_gene_catalog_snapshot_entries_sorted_by_gene_id(
    exhaustive_genes_ext1_belt: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
) -> None:
    _seed_samples(exhaustive_genes_ext1_belt, 2)
    payload = build_gene_catalog_snapshot(GeneticSample.objects.all())

    assert len(payload["entries"]) >= 2
    gene_ids = [e["gene_id"] for e in payload["entries"]]
    assert gene_ids == sorted(gene_ids)
