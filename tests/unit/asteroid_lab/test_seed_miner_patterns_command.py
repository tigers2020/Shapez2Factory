"""Management command ``seed_miner_patterns`` contract tests (PR-Seed Task 2)."""

from __future__ import annotations

import pytest
from django.core.management import call_command

from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import (
    EXHAUSTIVE_GENERATOR_STALE,
    MINER_SEED_SCHEMA,
)
from django_apps.asteroid_lab.models import GeneticSample
from django_apps.asteroid_lab.snapshots.copy_json_coords import entry_raw_x


@pytest.mark.django_db
def test_seed_miner_patterns_ingests_fourteen_unique_signatures() -> None:
    call_command("seed_miner_patterns", replace_stale=True)
    qs = GeneticSample.objects.filter(
        metadata_json__schema=MINER_SEED_SCHEMA,
        metadata_json__is_seed=True,
    )
    assert qs.count() == 14
    sigs = {row.metadata_json["topology_signature"] for row in qs}
    assert len(sigs) == 14


@pytest.mark.django_db
def test_stale_exhaustive_samples_removed_on_replace() -> None:
    valid_code = open("var/default_miner_pattern.txt", encoding="utf-8").readline().strip()
    GeneticSample.objects.create(
        gene_key="stale_exhaustive_key",
        name="stale",
        code=valid_code,
        metadata_json={"generator": EXHAUSTIVE_GENERATOR_STALE},
    )
    call_command("seed_miner_patterns", replace_stale=True)
    assert not GeneticSample.objects.filter(
        metadata_json__generator=EXHAUSTIVE_GENERATOR_STALE,
    ).exists()


@pytest.mark.django_db
def test_stored_code_matches_bootstrap_bytes() -> None:
    call_command("seed_miner_patterns")
    lines = [ln.strip() for ln in open("var/default_miner_pattern.txt") if ln.strip()]
    for rank, line in enumerate(lines, start=1):
        row = GeneticSample.objects.get(gene_key=f"miner_seed_{rank:02d}")
        assert row.code == line


@pytest.mark.django_db
def test_decoded_json_preserves_island_local_x_zero() -> None:
    call_command("seed_miner_patterns")
    row = GeneticSample.objects.get(gene_key="miner_seed_01")
    entries = row.decoded_json.get("BP", {}).get("Entries", [])
    xs = {entry_raw_x(e) for e in entries if isinstance(e, dict)}
    assert 0 in xs
