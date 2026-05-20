"""Convert GeneticSample ORM rows to GeneTemplate objects (adapter boundary, ORM allowed here)."""

from __future__ import annotations

import logging
from enum import StrEnum

from django.db.models import QuerySet

from django_apps.asteroid_lab.models import GeneticSample
from django_apps.asteroid_lab.optimization.gene_template import GeneTemplate
from django_apps.asteroid_lab.optimization.gene_template_loader import (
    gene_template_from_generated_sample,
)
from django_apps.asteroid_lab.services.sample_gene_exhaustive_generator import (
    GeneratedSampleGene,
    generate_exhaustive_sample_genes,
)

logger = logging.getLogger(__name__)

_DEFAULT_GENERATOR_VERSION = "exhaustive_sample_gene_v1"


class GeneTemplateExportErrorCode(StrEnum):
    """Per-row export failure codes (aggregated into GeneTemplateSourceMetadata)."""

    NO_GENE_KEY = "no_gene_key"
    GENE_KEY_NOT_IN_CACHE = "gene_key_not_in_cache"
    CONVERSION_ERROR = "conversion_error"


def _build_exhaustive_cache(generator_version: str) -> dict[str, GeneratedSampleGene]:
    """Generate all exhaustive sample genes and return a gene_key → GeneratedSampleGene map."""
    genes, _ = generate_exhaustive_sample_genes(generator_version=generator_version)
    return {g.key: g for g in genes}


def gene_template_from_genetic_sample(
    sample: GeneticSample,
    *,
    cache: dict[str, GeneratedSampleGene] | None = None,
    generator_version: str = _DEFAULT_GENERATOR_VERSION,
) -> tuple[GeneTemplate | None, GeneTemplateExportErrorCode | None]:
    """Convert one GeneticSample row to a GeneTemplate.

    Returns (GeneTemplate, None) on success or (None, error_code) on failure.
    Callers provide *cache* to avoid re-generating for every row.
    """
    gene_key = sample.gene_key if hasattr(sample, "gene_key") else None
    if not gene_key:
        return None, GeneTemplateExportErrorCode.NO_GENE_KEY

    resolved_cache = cache if cache is not None else _build_exhaustive_cache(generator_version)

    gene = resolved_cache.get(gene_key)
    if gene is None:
        logger.debug("gene_key not in exhaustive cache: %r", gene_key)
        return None, GeneTemplateExportErrorCode.GENE_KEY_NOT_IN_CACHE

    try:
        template = gene_template_from_generated_sample(gene)
    except Exception:
        logger.exception("conversion error for gene_key=%r", gene_key)
        return None, GeneTemplateExportErrorCode.CONVERSION_ERROR

    return template, None


def load_gene_templates_from_genetic_samples(
    queryset: QuerySet[GeneticSample],
    *,
    generator_version: str = _DEFAULT_GENERATOR_VERSION,
) -> tuple[tuple[GeneTemplate, ...], int, list[str]]:
    """Convert a GeneticSample queryset to GeneTemplates.

    Returns (templates sorted by gene_id, skipped_count, list of error_code strings).
    """
    cache = _build_exhaustive_cache(generator_version)
    templates: list[GeneTemplate] = []
    skipped = 0
    error_codes: list[str] = []

    for sample in queryset:
        template, err = gene_template_from_genetic_sample(
            sample, cache=cache, generator_version=generator_version
        )
        if template is not None:
            templates.append(template)
        else:
            skipped += 1
            if err is not None:
                error_codes.append(err.value)

    templates.sort(key=lambda t: t.gene_id)
    logger.info(
        "load_gene_templates_from_genetic_samples loaded=%d skipped=%d",
        len(templates),
        skipped,
    )
    return tuple(templates), skipped, error_codes


__all__ = [
    "GeneTemplateExportErrorCode",
    "gene_template_from_genetic_sample",
    "load_gene_templates_from_genetic_samples",
]
