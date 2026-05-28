"""Ingest 18 canonical miner seed patterns from bootstrap copy strings into GeneticSample."""

from __future__ import annotations

import hashlib
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
from django_apps.asteroid_lab.genetic_sample.miner_seed_topology import (
    count_extensions,
    throughput_factor_for_extension_count,
    topology_signature_from_decoded_root,
)
from django_apps.asteroid_lab.models import GeneticSample

_DEFAULT_BOOTSTRAP_PATH = "var/default_miner_pattern.txt"
_EXPECTED_LINE_COUNT = len(EXPECTED_PATTERN_IDS)


class Command(BaseCommand):  # type: ignore[misc]
    help = (
        "Ingest miner seed topologies from var/default_miner_pattern.txt "
        "into GeneticSample (miner_seed_v2 schema, 18 rows)."
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
            help="Validate bootstrap file only; do not write to the database.",
        )
        parser.add_argument(
            "--replace-stale",
            action="store_true",
            help=(
                "Delete GeneticSample rows where metadata_json.generator equals "
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
        topo_sigs: set[str] = set()
        equiv_sigs: set[str] = set()

        pairs = zip(EXPECTED_PATTERN_IDS, lines, strict=True)
        for rank, (pattern_id, code) in enumerate(pairs, start=1):
            dto = decode_copy_string(code)
            try:
                assert_miner_seed_layout_strict(dto.root)
            except MinerSeedLayoutValidationError as exc:
                raise CommandError(
                    f"strict layout validation failed for {pattern_id} (line {rank}): {exc}",
                ) from exc

            topo_sig = topology_signature_from_decoded_root(dto.root)
            if topo_sig in topo_sigs:
                raise CommandError(
                    f"duplicate topology_signature at seed rank {rank} ({pattern_id})",
                )
            topo_sigs.add(topo_sig)

            equiv_sig = equivalence_signature_from_decoded_root(dto.root)
            if equiv_sig in equiv_sigs:
                raise CommandError(
                    f"duplicate equivalence_signature at seed rank {rank} ({pattern_id})",
                )
            equiv_sigs.add(equiv_sig)
            ext = count_extensions(dto.root)
            meta = {
                "schema": MINER_SEED_SCHEMA_V2,
                "is_seed": True,
                "seed_rank": rank,
                "pattern_id": pattern_id,
                "source": {
                    "file": rel_source_file,
                    "line_no": rank,
                    "file_sha256": file_sha,
                },
                "equivalence_signature": equiv_sig,
                "topology_signature": topo_sig,
                "extension_count": ext,
                "throughput_factor": throughput_factor_for_extension_count(ext),
                "resource_kind_stored": "shape",
                "layout_types": list(MINER_LAYOUT_TYPES_SHAPE),
            }
            if options["dry_run"]:
                continue

            gkey = gene_key_for_pattern_id(pattern_id)
            obj, _created = GeneticSample.objects.update_or_create(
                gene_key=gkey,
                defaults={
                    "name": f"Seed {pattern_id} ext={ext}",
                    "code": code,
                    "metadata_json": meta,
                    "project": None,
                },
            )
            obj.save()

        if options["dry_run"]:
            self.stdout.write(
                self.style.NOTICE(
                    f"dry-run: validated {_EXPECTED_LINE_COUNT} seeds; no database writes.",
                ),
            )
            return

        if options["replace_stale"]:
            deleted, _detail = GeneticSample.objects.filter(
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

        seed_count = GeneticSample.objects.filter(
            metadata_json__schema=MINER_SEED_SCHEMA_V2,
            metadata_json__is_seed=True,
        ).count()
        self.stdout.write(
            self.style.SUCCESS(f"miner_seed_v2 GeneticSample rows: {seed_count}"),
        )

    def _purge_stale_miner_seed_rows(self) -> int:
        expected = set(EXPECTED_MINER_SEED_GENE_KEYS)
        stale_ids: list[int] = []
        for row in GeneticSample.objects.filter(gene_key__startswith="miner_seed_").only(
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
        deleted, _detail = GeneticSample.objects.filter(pk__in=stale_ids).delete()
        return int(deleted)
