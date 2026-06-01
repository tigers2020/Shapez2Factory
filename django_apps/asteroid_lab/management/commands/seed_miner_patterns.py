"""Ingest 18 canonical miner seed patterns from bootstrap copy strings into GeneSeed."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import (
    EXHAUSTIVE_GENERATOR_STALE,
    EXPECTED_MINER_SEED_GENE_KEYS,
    EXPECTED_PATTERN_IDS,
    MINER_LAYOUT_TYPES_SHAPE,
    MINER_SEED_SCHEMA_V2,
    MINER_SEED_SCHEMAS_PURGEABLE,
    gene_key_for_pattern_id,
)
from django_apps.asteroid_lab.genetic_sample.miner_seed_equivalence import (
    MinerSeedLayoutValidationError,
    assert_miner_seed_layout_strict,
    equivalence_signature_from_decoded_root,
)
from django_apps.asteroid_lab.genetic_sample.miner_seed_intrinsic_difficulty import (
    IntrinsicDifficultyResult,
    assign_difficulty_ranks,
    assign_intrinsic_priority_ranks,
    find_rank_ambiguity,
    intrinsic_difficulty_from_root,
    intrinsic_priority_score,
)
from django_apps.asteroid_lab.genetic_sample.miner_seed_topology import (
    count_extensions,
    throughput_factor_for_extension_count,
    topology_signature_from_decoded_root,
)
from django_apps.asteroid_lab.models import GeneSeed

_DEFAULT_BOOTSTRAP_PATH = "var/default_miner_pattern.txt"
_EXPECTED_LINE_COUNT = len(EXPECTED_PATTERN_IDS)
_SEARCH_PRIORITY_SOURCE_DEFERRED = "deferred_phase5"
_INTRINSIC_PRIORITY_SOURCE = "production_adjusted_intrinsic_v1"


@dataclass(frozen=True)
class _ParsedSeed:
    catalog_rank: int
    pattern_id: str
    code: str
    root: dict[str, Any]
    equivalence_signature: str
    topology_signature: str
    extension_count: int


class Command(BaseCommand):  # type: ignore[misc]
    help = (
        "Ingest miner seed topologies from var/default_miner_pattern.txt "
        "into GeneSeed (miner_seed_v2 schema, 18 rows). "
        "L3 also needs exhaustive gene_key rows: run seed_exhaustive_sample_genes "
        "(solver falls back to in-memory exhaustive catalog when only miner_seed_* exist)."
    )

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--file",
            default=_DEFAULT_BOOTSTRAP_PATH,
            help="Bootstrap copy-string file (default: var/default_miner_pattern.txt).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate bootstrap, compute difficulty ranks, print table; no DB writes.",
        )
        parser.add_argument(
            "--strict-rank-ambiguity",
            action="store_true",
            help=(
                "Fail when two pattern_ids share the same pre-pattern_id sort key "
                "(tier, score, compactness_approx, throughput_factor)."
            ),
        )
        parser.add_argument(
            "--replace-stale",
            action="store_true",
            help=(
                "Delete GeneSeed rows where metadata_json.generator equals "
                f"{EXHAUSTIVE_GENERATOR_STALE!r}."
            ),
        )
        parser.add_argument(
            "--purge-non-seed",
            action="store_true",
            help=(
                "Delete stale miner_seed_* rows with miner_seed_v1 or miner_seed_v2 schema "
                "whose gene_key is not in the expected 18 canonical keys."
            ),
        )

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        path = Path(str(options["file"]))
        if not path.is_file():
            raise CommandError(f"bootstrap file not found: {path}")

        lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if len(lines) != _EXPECTED_LINE_COUNT:
            raise CommandError(
                f"expected {_EXPECTED_LINE_COUNT} non-empty lines in {path}, got {len(lines)}",
            )

        file_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        rel_source_file = str(path).replace("\\", "/")
        parsed = self._parse_bootstrap(lines)

        scored = [(seed.pattern_id, intrinsic_difficulty_from_root(seed.root)) for seed in parsed]
        if options["strict_rank_ambiguity"]:
            self._raise_on_rank_ambiguity(scored)

        ranked = assign_difficulty_ranks(scored)
        difficulty_by_pattern = {
            pattern_id: (result, difficulty_rank) for pattern_id, result, difficulty_rank in ranked
        }

        priority_ranked = assign_intrinsic_priority_ranks(scored)
        priority_by_pattern = {
            pattern_id: (result, intrinsic_priority_rank)
            for pattern_id, result, intrinsic_priority_rank in priority_ranked
        }

        if options["dry_run"]:
            self._print_rank_table(parsed, difficulty_by_pattern, priority_by_pattern)
            self.stdout.write(
                self.style.NOTICE(
                    f"dry-run: validated {_EXPECTED_LINE_COUNT} seeds; no database writes.",
                ),
            )
            return

        for seed in parsed:
            difficulty, difficulty_rank = difficulty_by_pattern[seed.pattern_id]
            _priority_result, intrinsic_priority_rank = priority_by_pattern[seed.pattern_id]
            meta = self._build_metadata(
                seed=seed,
                rel_source_file=rel_source_file,
                file_sha=file_sha,
                difficulty=difficulty,
                difficulty_rank=difficulty_rank,
                intrinsic_priority_rank=intrinsic_priority_rank,
            )
            gkey = gene_key_for_pattern_id(seed.pattern_id)
            obj, _created = GeneSeed.objects.update_or_create(
                gene_key=gkey,
                defaults={
                    "name": f"Seed {seed.pattern_id} ext={seed.extension_count}",
                    "code": seed.code,
                    "metadata_json": meta,
                    "project": None,
                },
            )
            obj.save()

        if options["replace_stale"]:
            deleted, _detail = GeneSeed.objects.filter(
                metadata_json__generator=EXHAUSTIVE_GENERATOR_STALE,
            ).delete()
            self.stdout.write(
                self.style.WARNING(f"deleted stale exhaustive rows (objects): {deleted}"),
            )

        if options["purge_non_seed"]:
            deleted = self._purge_stale_miner_seed_rows()
            self.stdout.write(
                self.style.WARNING(
                    f"deleted stale miner_seed catalog rows (objects): {deleted}",
                ),
            )

        seed_count = GeneSeed.objects.filter(
            metadata_json__schema=MINER_SEED_SCHEMA_V2,
            metadata_json__is_seed=True,
        ).count()
        self.stdout.write(
            self.style.SUCCESS(f"miner_seed_v2 GeneSeed rows: {seed_count}"),
        )

    def _parse_bootstrap(self, lines: list[str]) -> list[_ParsedSeed]:
        topo_sigs: set[str] = set()
        equiv_sigs: set[str] = set()
        parsed: list[_ParsedSeed] = []
        for catalog_rank, (pattern_id, code) in enumerate(
            zip(EXPECTED_PATTERN_IDS, lines, strict=True),
            start=1,
        ):
            dto = decode_copy_string(code)
            try:
                assert_miner_seed_layout_strict(dto.root)
            except MinerSeedLayoutValidationError as exc:
                raise CommandError(
                    f"strict layout validation failed for {pattern_id} "
                    f"(catalog rank {catalog_rank}): {exc}",
                ) from exc

            topo_sig = topology_signature_from_decoded_root(dto.root)
            if topo_sig in topo_sigs:
                raise CommandError(
                    f"duplicate topology_signature at catalog rank {catalog_rank} "
                    f"({pattern_id})",
                )
            topo_sigs.add(topo_sig)

            equiv_sig = equivalence_signature_from_decoded_root(dto.root)
            if equiv_sig in equiv_sigs:
                raise CommandError(
                    f"duplicate equivalence_signature at catalog rank {catalog_rank} "
                    f"({pattern_id})",
                )
            equiv_sigs.add(equiv_sig)
            parsed.append(
                _ParsedSeed(
                    catalog_rank=catalog_rank,
                    pattern_id=pattern_id,
                    code=code,
                    root=dto.root,
                    equivalence_signature=equiv_sig,
                    topology_signature=topo_sig,
                    extension_count=count_extensions(dto.root),
                ),
            )
        return parsed

    def _build_metadata(
        self,
        *,
        seed: _ParsedSeed,
        rel_source_file: str,
        file_sha: str,
        difficulty: IntrinsicDifficultyResult,
        difficulty_rank: int,
        intrinsic_priority_rank: int,
    ) -> dict[str, Any]:
        ext = seed.extension_count
        priority_score = intrinsic_priority_score(difficulty)
        return {
            "schema": MINER_SEED_SCHEMA_V2,
            "is_seed": True,
            "seed_rank": seed.catalog_rank,
            "pattern_id": seed.pattern_id,
            "difficulty_score": difficulty.score,
            "difficulty_rank": difficulty_rank,
            "difficulty_tier": difficulty.tier,
            "rank_reason": difficulty.reason,
            "intrinsic_priority_score": priority_score,
            "intrinsic_priority_rank": intrinsic_priority_rank,
            "intrinsic_priority_source": _INTRINSIC_PRIORITY_SOURCE,
            "search_priority_rank": None,
            "search_priority_source": _SEARCH_PRIORITY_SOURCE_DEFERRED,
            "source": {
                "file": rel_source_file,
                "line_no": seed.catalog_rank,
                "file_sha256": file_sha,
            },
            "equivalence_signature": seed.equivalence_signature,
            "topology_signature": seed.topology_signature,
            "extension_count": ext,
            "throughput_factor": throughput_factor_for_extension_count(ext),
            "resource_kind_stored": "shape",
            "layout_types": list(MINER_LAYOUT_TYPES_SHAPE),
        }

    def _raise_on_rank_ambiguity(
        self,
        scored: list[tuple[str, IntrinsicDifficultyResult]],
    ) -> None:
        collisions = find_rank_ambiguity(scored)
        if not collisions:
            return
        a, b, key = collisions[0]
        raise CommandError(
            f"rank ambiguity between {a!r} and {b!r} for pre-pattern_id sort key {key}",
        )

    def _print_rank_table(
        self,
        parsed: list[_ParsedSeed],
        difficulty_by_pattern: dict[str, tuple[IntrinsicDifficultyResult, int]],
        priority_by_pattern: dict[str, tuple[IntrinsicDifficultyResult, int]],
    ) -> None:
        self.stdout.write(
            "difficulty_rank  intrinsic_priority_rank  pattern_id   tier  score  catalog_rank",
        )
        rows = sorted(
            parsed,
            key=lambda s: difficulty_by_pattern[s.pattern_id][1],
        )
        for seed in rows:
            difficulty, difficulty_rank = difficulty_by_pattern[seed.pattern_id]
            _priority_result, intrinsic_priority_rank = priority_by_pattern[seed.pattern_id]
            self.stdout.write(
                f"{difficulty_rank:>15}  {intrinsic_priority_rank:>24}  {seed.pattern_id:<11}  "
                f"{difficulty.tier:>4}  {difficulty.score:>5}  {seed.catalog_rank:>12}",
            )

    def _purge_stale_miner_seed_rows(self) -> int:
        expected = set(EXPECTED_MINER_SEED_GENE_KEYS)
        stale_ids: list[int] = []
        for row in GeneSeed.objects.filter(gene_key__startswith="miner_seed_").only(
            "pk",
            "gene_key",
            "metadata_json",
        ):
            gkey = row.gene_key or ""
            meta = row.metadata_json if isinstance(row.metadata_json, dict) else {}
            schema = meta.get("schema")
            if schema not in MINER_SEED_SCHEMAS_PURGEABLE:
                continue
            if gkey in expected:
                continue
            stale_ids.append(int(row.pk))
        if not stale_ids:
            return 0
        deleted, _detail = GeneSeed.objects.filter(pk__in=stale_ids).delete()
        return int(deleted)
