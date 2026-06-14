"""GeneSeed DB catalog → genetic_sample_seed_v1 snapshot (L3 boundary)."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import (
    CANONICAL_MINER_SEED_COUNT,
    MINER_SEED_SCHEMA_V2,
)
from django_apps.asteroid_lab.models import GeneSeed
from django_apps.asteroid_lab.services.gene_seed_l3_catalog import (
    build_genetic_sample_seed_snapshot_from_db,
    gene_seed_l3_catalog_queryset,
    load_genetic_sample_seed_snapshot_from_db,
)


@pytest.mark.django_db
def test_gene_seed_l3_catalog_matches_admin_filter_after_seed() -> None:
    from django.core.management import call_command

    call_command("seed_miner_patterns", verbosity=0)
    qs = gene_seed_l3_catalog_queryset(scope="admin")
    assert qs.count() == CANONICAL_MINER_SEED_COUNT
    v2_count = qs.filter(metadata_json__schema=MINER_SEED_SCHEMA_V2).count()
    assert v2_count == CANONICAL_MINER_SEED_COUNT

    payload = build_genetic_sample_seed_snapshot_from_db(scope="admin")
    assert payload["schema_version"] == "genetic_sample_seed_v1"
    entries = payload["entries"]
    assert isinstance(entries, list)
    assert len(entries) >= CANONICAL_MINER_SEED_COUNT

    snap = load_genetic_sample_seed_snapshot_from_db(scope="admin")
    assert len(snap.entries) == len(entries)
    assert all(e.gene_id for e in snap.entries)


@pytest.mark.django_db
def test_ensure_miner_gene_seeds_bootstrapped_seeds_empty_db() -> None:
    from django_apps.asteroid_lab.services.gene_seed_l3_catalog import (
        ensure_miner_gene_seeds_bootstrapped,
    )

    GeneSeed.objects.all().delete()
    assert ensure_miner_gene_seeds_bootstrapped() is True
    assert (
        gene_seed_l3_catalog_queryset(scope="admin").count() == CANONICAL_MINER_SEED_COUNT
    )


@pytest.mark.django_db
def test_gene_seed_l3_catalog_all_scope_is_superset_of_admin() -> None:
    from django.core.management import call_command

    call_command("seed_miner_patterns", verbosity=0)
    admin_count = gene_seed_l3_catalog_queryset(scope="admin").count()
    all_count = gene_seed_l3_catalog_queryset(scope="all").count()
    assert all_count >= admin_count
