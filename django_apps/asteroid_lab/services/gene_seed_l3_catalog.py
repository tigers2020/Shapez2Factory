"""GeneSeed ORM queryset + snapshot loader for L3 genetic_sample_seeds (adapter boundary)."""

from __future__ import annotations

from typing import Literal

from django.db.models import QuerySet

from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import MINER_SEED_SCHEMA_V2
from django_apps.asteroid_lab.models import GeneSeed
from django_apps.asteroid_lab.services.genetic_sample_catalog_snapshot import (
    build_genetic_sample_seed_snapshot,
)
from shapez2_factory.adapters.asteroid_lab.genetic_sample_seed_snapshot import (
    GeneticSampleSeedSnapshot,
)

GeneSeedCatalogScope = Literal["admin", "all"]


def gene_seed_l3_catalog_queryset(
    *,
    scope: GeneSeedCatalogScope = "admin",
) -> QuerySet[GeneSeed]:
    """Rows serialized into ``genetic_sample_seed_v1`` for L3 candidate expansion.

    ``admin`` — matches ``GeneSeedAdmin.get_queryset`` (canonical miner seeds in admin).
    ``all`` — every ``GeneSeed`` row (web solver subprocess default).
    """

    if scope == "all":
        return GeneSeed.objects.all().order_by("gene_key", "pk")
    return GeneSeed.objects.filter(
        gene_key__isnull=False,
        metadata_json__schema=MINER_SEED_SCHEMA_V2,
        metadata_json__is_seed=True,
    ).order_by("metadata_json__seed_rank", "gene_key")


def build_genetic_sample_seed_snapshot_from_db(
    *,
    scope: GeneSeedCatalogScope = "admin",
) -> dict[str, object]:
    """Build ``genetic_sample_seed_v1`` JSON payload from live ``GeneSeed`` rows."""

    return build_genetic_sample_seed_snapshot(gene_seed_l3_catalog_queryset(scope=scope))


def load_genetic_sample_seed_snapshot_from_db(
    *,
    scope: GeneSeedCatalogScope = "admin",
) -> GeneticSampleSeedSnapshot:
    """Parse live DB catalog into ``GeneticSampleSeedSnapshot`` for Django-free L3 stack."""

    return GeneticSampleSeedSnapshot.from_payload(
        build_genetic_sample_seed_snapshot_from_db(scope=scope),
    )


__all__ = [
    "GeneSeedCatalogScope",
    "build_genetic_sample_seed_snapshot_from_db",
    "gene_seed_l3_catalog_queryset",
    "load_genetic_sample_seed_snapshot_from_db",
]
