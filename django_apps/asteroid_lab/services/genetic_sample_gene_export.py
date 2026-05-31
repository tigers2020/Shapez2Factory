"""Convert GeneSeed ORM rows to GeneTemplate objects (adapter boundary, ORM allowed here)."""

from __future__ import annotations

import logging
from enum import StrEnum

from django.db.models import QuerySet

from django_apps.asteroid_lab.genetic_sample.exhaustive_generator import (
    GeneratedSampleGene,
    generate_exhaustive_sample_genes,
)
from django_apps.asteroid_lab.genetic_sample.gene_template import GeneTemplate
from django_apps.asteroid_lab.genetic_sample.gene_template_loader import (
    gene_template_from_generated_sample,
)
from django_apps.asteroid_lab.models import GeneSeed
from django_apps.asteroid_lab.services.miner_gene_seed_template import (
    gene_template_from_miner_gene_seed,
    is_miner_seed_v2,
)

logger = logging.getLogger(__name__)

_DEFAULT_GENERATOR_VERSION = "exhaustive_sample_gene_v1"


class GeneTemplateExportErrorCode(StrEnum):
    NO_GENE_KEY = "no_gene_key"
    GENE_KEY_NOT_IN_CACHE = "gene_key_not_in_cache"
    CONVERSION_ERROR = "conversion_error"


def _build_exhaustive_cache(generator_version: str) -> dict[str, GeneratedSampleGene]:
    genes, _ = generate_exhaustive_sample_genes(generator_version=generator_version)
    return {g.key: g for g in genes}


def gene_template_from_gene_seed(
    seed: GeneSeed,
    *,
    cache: dict[str, GeneratedSampleGene] | None = None,
    generator_version: str = _DEFAULT_GENERATOR_VERSION,
) -> tuple[GeneTemplate | None, GeneTemplateExportErrorCode | None]:
    if is_miner_seed_v2(seed):
        template, _err = gene_template_from_miner_gene_seed(seed)
        if template is not None:
            return template, None
        return None, GeneTemplateExportErrorCode.CONVERSION_ERROR

    gene_key = seed.gene_key if hasattr(seed, "gene_key") else None
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


def _load_miner_seed_templates(
    queryset: QuerySet[GeneSeed],
) -> tuple[tuple[GeneTemplate, ...], int, list[str]]:
    templates: list[GeneTemplate] = []
    skipped = 0
    error_codes: list[str] = []
    for seed in queryset.order_by("gene_key"):
        if not is_miner_seed_v2(seed):
            continue
        template, err = gene_template_from_miner_gene_seed(seed)
        if template is not None:
            templates.append(template)
        else:
            skipped += 1
            if err is not None:
                error_codes.append(err.value)
    templates.sort(key=lambda t: t.gene_id)
    return tuple(templates), skipped, error_codes


def _load_exhaustive_templates(
    queryset: QuerySet[GeneSeed],
    *,
    generator_version: str = _DEFAULT_GENERATOR_VERSION,
) -> tuple[tuple[GeneTemplate, ...], int, list[str]]:
    cache = _build_exhaustive_cache(generator_version)
    templates: list[GeneTemplate] = []
    skipped = 0
    error_codes: list[str] = []

    for seed in queryset:
        if is_miner_seed_v2(seed):
            continue
        template, err = gene_template_from_gene_seed(
            seed, cache=cache, generator_version=generator_version
        )
        if template is not None:
            templates.append(template)
        else:
            skipped += 1
            if err is not None:
                error_codes.append(err.value)

    templates.sort(key=lambda t: t.gene_id)
    return tuple(templates), skipped, error_codes


def queryset_has_miner_seed_v2(queryset: QuerySet[GeneSeed]) -> bool:
    return queryset.filter(
        gene_key__startswith="miner_seed_",
        metadata_json__schema="miner_seed_v2",
        metadata_json__is_seed=True,
    ).exists()


def load_gene_templates_from_gene_seeds(
    queryset: QuerySet[GeneSeed],
    *,
    generator_version: str = _DEFAULT_GENERATOR_VERSION,
) -> tuple[tuple[GeneTemplate, ...], int, list[str]]:
    if queryset_has_miner_seed_v2(queryset):
        templates, skipped, error_codes = _load_miner_seed_templates(queryset)
    else:
        templates, skipped, error_codes = _load_exhaustive_templates(
            queryset, generator_version=generator_version
        )

    logger.info(
        "load_gene_templates_from_gene_seeds loaded=%d skipped=%d",
        len(templates),
        skipped,
    )
    return tuple(templates), skipped, error_codes


__all__ = [
    "GeneTemplateExportErrorCode",
    "gene_template_from_gene_seed",
    "load_gene_templates_from_gene_seeds",
    "queryset_has_miner_seed_v2",
]
