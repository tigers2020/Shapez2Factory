"""Management command ``seed_miner_patterns`` contract tests."""

from __future__ import annotations

import pytest
from django.core.management import call_command

from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import (
    EXPECTED_MINER_SEED_GENE_KEYS,
    EXPECTED_PATTERN_IDS,
    EXHAUSTIVE_GENERATOR_STALE,
    MINER_SEED_SCHEMA_V2,
    gene_key_for_pattern_id,
)
from django_apps.asteroid_lab.models import GeneticSample
from django_apps.asteroid_lab.snapshots.copy_json_coords import entry_raw_x


@pytest.mark.django_db
def test_seed_miner_patterns_ingests_eighteen_unique_signatures() -> None:
    call_command("seed_miner_patterns", replace_stale=True)
    qs = GeneticSample.objects.filter(
        metadata_json__schema=MINER_SEED_SCHEMA_V2,
        metadata_json__is_seed=True,
    )
    assert qs.count() == 18
    topo_sigs = {row.metadata_json["topology_signature"] for row in qs}
    assert len(topo_sigs) == 18
    equiv_sigs = {row.metadata_json["equivalence_signature"] for row in qs}
    assert len(equiv_sigs) == 18
    assert {row.gene_key for row in qs} == set(EXPECTED_MINER_SEED_GENE_KEYS)
    assert not GeneticSample.objects.filter(gene_key="miner_seed_m3e_10").exists()


@pytest.mark.django_db
def test_purge_non_seed_narrow_does_not_delete_manual_rows() -> None:
    valid_code = open("var/default_miner_pattern.txt", encoding="utf-8").readline().strip()
    GeneticSample.objects.create(
        gene_key="manual_legacy_sample",
        name="legacy manual",
        code=valid_code,
        metadata_json={"note": "manual"},
    )
    call_command("seed_miner_patterns", purge_non_seed=True)
    assert GeneticSample.objects.filter(gene_key="manual_legacy_sample").exists()
    assert (
        GeneticSample.objects.filter(
            metadata_json__schema=MINER_SEED_SCHEMA_V2,
            metadata_json__is_seed=True,
        ).count()
        == 18
    )


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
    for pattern_id, line in zip(EXPECTED_PATTERN_IDS, lines, strict=True):
        row = GeneticSample.objects.get(gene_key=gene_key_for_pattern_id(pattern_id))
        assert row.code == line
        assert row.metadata_json["pattern_id"] == pattern_id


@pytest.mark.django_db
def test_decoded_json_preserves_island_local_x_zero() -> None:
    call_command("seed_miner_patterns")
    row = GeneticSample.objects.get(gene_key=gene_key_for_pattern_id("m0e_01"))
    entries = row.decoded_json.get("BP", {}).get("Entries", [])
    xs = {entry_raw_x(e) for e in entries if isinstance(e, dict)}
    assert 0 in xs
