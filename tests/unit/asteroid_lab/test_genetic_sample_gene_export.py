"""Contract tests for genetic_sample_gene_export (GeneticSample → GeneTemplate)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.models import GeneticSample
from django_apps.asteroid_lab.optimization.gene_template import GeneTemplate
from django_apps.asteroid_lab.services.genetic_sample_gene_export import (
    GeneTemplateExportErrorCode,
    gene_template_from_genetic_sample,
    load_gene_templates_from_genetic_samples,
)
from django_apps.asteroid_lab.services.sample_gene_exhaustive_generator import (
    ExhaustiveGenerationStats,
    GeneratedSampleGene,
)

pytestmark = pytest.mark.django_db


def _seed_one_sample(
    exhaustive_genes_ext0_belt: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
) -> GeneticSample:
    genes, _ = exhaustive_genes_ext0_belt
    assert genes, "exhaustive generator must produce at least one gene with max_extensions=0"
    g = genes[0]
    sample, _ = GeneticSample.objects.update_or_create(
        gene_key=g.key,
        defaults={
            "name": g.name,
            "code": g.encoded_copy_string,
            "metadata_json": dict(g.metadata),
        },
    )
    return sample


def test_gene_template_from_genetic_sample_success(
    exhaustive_genes_ext0_belt: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
) -> None:
    sample = _seed_one_sample(exhaustive_genes_ext0_belt)
    template, err = gene_template_from_genetic_sample(sample)
    assert err is None
    assert isinstance(template, GeneTemplate)
    assert template.gene_id == sample.gene_key


def test_gene_template_from_genetic_sample_no_gene_key() -> None:
    sample = GeneticSample(name="manual", gene_key=None, code="x", metadata_json={})
    template, err = gene_template_from_genetic_sample(sample)
    assert template is None
    assert err == GeneTemplateExportErrorCode.NO_GENE_KEY


def test_gene_template_from_genetic_sample_unknown_gene_key() -> None:
    sample = GeneticSample(
        name="unknown",
        gene_key='{"ec":99,"e":[],"tk":"belt"}',
        code="x",
        metadata_json={"generator": "exhaustive_sample_gene_v1"},
    )
    template, err = gene_template_from_genetic_sample(sample)
    assert template is None
    assert err == GeneTemplateExportErrorCode.GENE_KEY_NOT_IN_CACHE


def test_load_gene_templates_from_genetic_samples_basic(
    exhaustive_genes_ext0_belt: tuple[list[GeneratedSampleGene], ExhaustiveGenerationStats],
) -> None:
    _seed_one_sample(exhaustive_genes_ext0_belt)
    qs = GeneticSample.objects.filter(
        gene_key__isnull=False,
        metadata_json__generator="exhaustive_sample_gene_v1",
    )
    templates, skipped, errors = load_gene_templates_from_genetic_samples(qs)
    assert len(templates) >= 1
    assert skipped == 0
    assert errors == []
    # sorted by gene_id
    ids = [t.gene_id for t in templates]
    assert ids == sorted(ids)


def test_load_gene_templates_skips_manual_samples() -> None:
    """Samples without gene_key are skipped with NO_GENE_KEY code."""
    manual = GeneticSample(name="manual_no_key", gene_key=None, metadata_json={})
    template, err = gene_template_from_genetic_sample(manual)
    assert template is None
    assert err == GeneTemplateExportErrorCode.NO_GENE_KEY


def test_load_gene_templates_empty_queryset() -> None:
    qs = GeneticSample.objects.none()
    templates, skipped, errors = load_gene_templates_from_genetic_samples(qs)
    assert templates == ()
    assert skipped == 0
    assert errors == []
