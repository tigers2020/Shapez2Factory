"""Management command ``seed_miner_patterns`` contract tests."""

from __future__ import annotations

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import (
    EXHAUSTIVE_GENERATOR_STALE,
    EXPECTED_DIFFICULTY_RANK_ORDER,
    EXPECTED_MINER_SEED_GENE_KEYS,
    EXPECTED_PATTERN_IDS,
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
def test_seed_miner_patterns_writes_difficulty_metadata() -> None:
    call_command("seed_miner_patterns")
    row = GeneticSample.objects.get(gene_key="miner_seed_m3e_01")
    meta = row.metadata_json
    assert meta["difficulty_rank"] == 7
    assert meta["difficulty_score"] == 337
    assert isinstance(meta["difficulty_score"], int)
    assert meta["difficulty_tier"] == 4
    assert meta["search_priority_rank"] is None
    assert meta["search_priority_source"] == "deferred_phase5"
    assert "compactness_approx" in meta["rank_reason"]
    assert "coverage_approx" not in meta["rank_reason"]
    assert meta["seed_rank"] == EXPECTED_PATTERN_IDS.index("m3e_01") + 1


@pytest.mark.django_db
def test_difficulty_ranks_are_permutation_1_to_18() -> None:
    call_command("seed_miner_patterns")
    rows = GeneticSample.objects.filter(
        metadata_json__schema=MINER_SEED_SCHEMA_V2,
        metadata_json__is_seed=True,
    )
    ranks = [int(row.metadata_json["difficulty_rank"]) for row in rows]
    assert sorted(ranks) == list(range(1, 19))
    by_rank = {
        int(row.metadata_json["difficulty_rank"]): row.metadata_json["pattern_id"]
        for row in rows
    }
    assert [by_rank[i] for i in range(1, 19)] == list(EXPECTED_DIFFICULTY_RANK_ORDER)


@pytest.mark.django_db
def test_dry_run_prints_difficulty_table(capsys: pytest.CaptureFixture[str]) -> None:
    call_command("seed_miner_patterns", dry_run=True)
    out = capsys.readouterr().out
    assert "difficulty_rank  pattern_id" in out
    assert "m0e_01" in out
    assert "dry-run: validated 18 seeds" in out


@pytest.mark.django_db
def test_strict_rank_ambiguity_flags_m3e_score_tie() -> None:
    """m3e_02 and m3e_04 share pre-pattern_id key; pattern_id resolves in default ingest."""

    with pytest.raises(CommandError, match="m3e_02.*m3e_04"):
        call_command("seed_miner_patterns", dry_run=True, strict_rank_ambiguity=True)


@pytest.mark.django_db
def test_decoded_json_preserves_island_local_x_zero() -> None:
    call_command("seed_miner_patterns")
    row = GeneticSample.objects.get(gene_key=gene_key_for_pattern_id("m0e_01"))
    entries = row.decoded_json.get("BP", {}).get("Entries", [])
    xs = {entry_raw_x(e) for e in entries if isinstance(e, dict)}
    assert 0 in xs
