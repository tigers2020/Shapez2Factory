"""Narrow purge for stale miner_seed_* v1/v2 catalog rows."""

from __future__ import annotations

import pytest
from django.core.management import call_command

from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import (
    MINER_SEED_SCHEMA,
    MINER_SEED_SCHEMA_V2,
    gene_key_for_pattern_id,
    gene_key_for_rank,
)
from django_apps.asteroid_lab.models import GeneticSample


@pytest.mark.django_db
def test_purge_narrow_keeps_manual_and_removes_stale_v1() -> None:
    valid_code = open("var/default_miner_pattern.txt", encoding="utf-8").readline().strip()
    GeneticSample.objects.create(
        gene_key="manual_legacy_sample",
        name="legacy manual",
        code=valid_code,
        metadata_json={"note": "manual"},
    )
    GeneticSample.objects.create(
        gene_key=gene_key_for_rank(1),
        name="stale v1",
        code=valid_code,
        metadata_json={"schema": MINER_SEED_SCHEMA, "is_seed": True, "seed_rank": 1},
    )
    call_command("seed_miner_patterns", purge_non_seed=True)
    assert GeneticSample.objects.filter(gene_key="manual_legacy_sample").exists()
    assert not GeneticSample.objects.filter(gene_key=gene_key_for_rank(1)).exists()
    assert GeneticSample.objects.filter(
        metadata_json__schema=MINER_SEED_SCHEMA_V2,
        metadata_json__is_seed=True,
    ).count() == 19


@pytest.mark.django_db
def test_purge_narrow_removes_extra_v2_key() -> None:
    valid_code = open("var/default_miner_pattern.txt", encoding="utf-8").readline().strip()
    GeneticSample.objects.create(
        gene_key="miner_seed_m9e_99",
        name="fake v2",
        code=valid_code,
        metadata_json={"schema": MINER_SEED_SCHEMA_V2, "is_seed": True},
    )
    call_command("seed_miner_patterns", purge_non_seed=True)
    assert not GeneticSample.objects.filter(gene_key="miner_seed_m9e_99").exists()
    assert GeneticSample.objects.get(gene_key=gene_key_for_pattern_id("m0e_01"))
