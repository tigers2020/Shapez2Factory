"""DB-only runtime gene template resolver (entry boundary, ORM allowed here)."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from django_apps.asteroid_lab.models import GeneticSample
from django_apps.asteroid_lab.optimization.gene_template import GeneTemplate
from django_apps.asteroid_lab.services.genetic_sample_gene_export import (
    load_gene_templates_from_genetic_samples,
)
from django_apps.asteroid_lab.services.runtime_gene_template_source import (
    GeneTemplateLoadErrorCode,
    GeneTemplateSourceKind,
    GeneTemplateSourceMetadata,
)

logger = logging.getLogger(__name__)

_DEFAULT_GENERATOR_VERSION = "exhaustive_sample_gene_v1"


def resolve_runtime_gene_templates_from_db(
    *,
    generator_version: str = _DEFAULT_GENERATOR_VERSION,
    gene_keys: Sequence[str] | None = None,
    limit: int | None = None,
) -> tuple[
    tuple[GeneTemplate, ...] | None,
    GeneTemplateSourceMetadata | None,
    GeneTemplateLoadErrorCode | None,
]:
    """Load GeneTemplates from GeneticSample DB rows (gene_key scoped).

    Returns (templates, metadata, None) on success,
    or (None, None, error_code) when no usable templates exist.
    """
    qs = GeneticSample.objects.filter(
        gene_key__isnull=False,
        metadata_json__generator=generator_version,
    ).order_by("gene_key")

    if gene_keys is not None:
        qs = qs.filter(gene_key__in=list(gene_keys))

    if limit is not None:
        qs = qs[:limit]

    templates, skipped, error_codes = load_gene_templates_from_genetic_samples(
        qs, generator_version=generator_version
    )

    gene_count = len(templates)
    gene_ids = tuple(t.gene_id for t in templates)
    gene_key_filter = tuple(gene_keys) if gene_keys is not None else None

    logger.info(
        "resolve_runtime_gene_templates_from_db source=genetic_sample_db "
        "generator=%s gene_count=%d skipped=%d",
        generator_version,
        gene_count,
        skipped,
    )

    if gene_count == 0:
        return None, None, GeneTemplateLoadErrorCode.NO_GENE_TEMPLATES_IN_DB

    metadata = GeneTemplateSourceMetadata(
        source=GeneTemplateSourceKind.GENETIC_SAMPLE_DB,
        gene_count=gene_count,
        generator_version=generator_version,
        gene_ids=gene_ids,
        export_skipped_count=skipped,
        export_error_codes=tuple(error_codes),
        gene_key_filter=gene_key_filter,
    )
    return templates, metadata, None


__all__ = [
    "resolve_runtime_gene_templates_from_db",
]
