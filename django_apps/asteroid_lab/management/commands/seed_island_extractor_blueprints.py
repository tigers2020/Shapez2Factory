"""Idempotent DB seed for canonical island extractor blueprints."""

from __future__ import annotations

from typing import Any

from django.core.management.base import BaseCommand

from django_apps.asteroid_lab.catalog.island_extractor_defaults import (
    ISLAND_EXTRACTOR_DEFAULTS,
    inner_entry_fingerprint,
)
from django_apps.asteroid_lab.models import IslandExtractorBlueprint


class Command(BaseCommand):  # type: ignore[misc]
    help = "Upsert IslandExtractorBlueprint rows from catalog.island_extractor_defaults."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print actions only; do not write to the database.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        dry_run = bool(options["dry_run"])
        saved = 0
        for row in ISLAND_EXTRACTOR_DEFAULTS:
            fingerprint = inner_entry_fingerprint(row.copy_code)
            payload = {
                "carrier_kind": row.carrier_kind.value,
                "display_name": row.display_name,
                "summary": row.summary_ko,
                "layout_t": row.layout_t,
                "copy_code": row.copy_code,
                "inner_fingerprint": fingerprint,
                "metadata_json": dict(row.metadata_json),
            }
            if dry_run:
                self.stdout.write(f"would upsert {row.variant_key.value} fp={fingerprint[:12]}...")
                saved += 1
                continue
            _, created = IslandExtractorBlueprint.objects.update_or_create(
                variant_key=row.variant_key.value,
                defaults=payload,
            )
            verb = "created" if created else "updated"
            self.stdout.write(f"{verb} {row.variant_key.value}")
            saved += 1
        self.stdout.write(self.style.SUCCESS(f"island extractor blueprints: {saved}"))
