"""Shared fixtures for ``tests/integration``."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.genetic_sample.exhaustive_generator import (
    ExhaustiveGenerationStats,
    GeneratedSampleGene,
    generate_exhaustive_sample_genes,
)


@pytest.fixture(scope="module")
def exhaustive_genes_ext0_belt_v1() -> tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats]:
    return generate_exhaustive_sample_genes(
        max_extensions=0,
        transport_kinds=("belt",),
        generator_version="exhaustive_sample_gene_v1",
    )


@pytest.fixture(autouse=True)
def seed_gene_templates_from_exhaustive(
    db: None,
    exhaustive_genes_ext0_belt_v1: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
) -> None:
    genes, _stats = exhaustive_genes_ext0_belt_v1
    for g in genes:
        m.GeneticSample.objects.update_or_create(
            gene_key=g.key,
            defaults={
                "name": g.name,
                "code": g.encoded_copy_string,
                "metadata_json": dict(g.metadata),
            },
        )
