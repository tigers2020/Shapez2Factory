"""Ingest 14 canonical miner seed patterns from bootstrap copy strings into GeneticSample."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import (
    EXHAUSTIVE_GENERATOR_STALE,
    MINER_LAYOUT_TYPES_SHAPE,
    MINER_SEED_SCHEMA,
    gene_key_for_rank,
)
from django_apps.asteroid_lab.genetic_sample.miner_seed_topology import (
    count_extensions,
    throughput_factor_for_extension_count,
    topology_signature_from_decoded_root,
)
from django_apps.asteroid_lab.models import GeneticSample

_DEFAULT_BOOTSTRAP_PATH = "var/default_miner_pattern.txt"


class Command(BaseCommand):  # type: ignore[misc]
    help = (
        "Ingest miner seed topologies from var/default_miner_pattern.txt "
        "into GeneticSample (miner_seed_v1 schema, 14 rows)."
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

    @transaction.atomic
    def handle(self, *args: Any, **options: Any) -> None:
        path = Path(str(options["file"]))
        if not path.is_file():
            raise CommandError(f"bootstrap file not found: {path}")

        lines = [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
        if len(lines) != 14:
            raise CommandError(f"expected 14 non-empty lines in {path}, got {len(lines)}")

        file_sha = hashlib.sha256(path.read_bytes()).hexdigest()
        rel_source_file = str(path).replace("\\", "/")
        sigs: set[str] = set()

        for rank, code in enumerate(lines, start=1):
            dto = decode_copy_string(code)
            sig = topology_signature_from_decoded_root(dto.root)
            if sig in sigs:
                raise CommandError(f"duplicate topology_signature at seed rank {rank}")
            sigs.add(sig)
            ext = count_extensions(dto.root)
            meta = {
                "schema": MINER_SEED_SCHEMA,
                "is_seed": True,
                "seed_rank": rank,
                "source": {
                    "file": rel_source_file,
                    "line_no": rank,
                    "file_sha256": file_sha,
                },
                "topology_signature": sig,
                "extension_count": ext,
                "throughput_factor": throughput_factor_for_extension_count(ext),
                "resource_kind_stored": "shape",
                "layout_types": list(MINER_LAYOUT_TYPES_SHAPE),
            }
            if options["dry_run"]:
                continue

            gkey = gene_key_for_rank(rank)
            obj, _created = GeneticSample.objects.update_or_create(
                gene_key=gkey,
                defaults={
                    "name": f"Seed ext={ext} rank={rank:02d}",
                    "code": code,
                    "metadata_json": meta,
                    "project": None,
                },
            )
            obj.save()

        if options["dry_run"]:
            self.stdout.write(self.style.NOTICE("dry-run: validated 14 seeds; no database writes."))
            return

        if options["replace_stale"]:
            deleted, _detail = GeneticSample.objects.filter(
                metadata_json__generator=EXHAUSTIVE_GENERATOR_STALE,
            ).delete()
            self.stdout.write(
                self.style.WARNING(f"deleted stale exhaustive rows (objects): {deleted}"),
            )

        seed_count = GeneticSample.objects.filter(
            metadata_json__schema=MINER_SEED_SCHEMA,
            metadata_json__is_seed=True,
        ).count()
        self.stdout.write(self.style.SUCCESS(f"miner_seed_v1 GeneticSample rows: {seed_count}"))
