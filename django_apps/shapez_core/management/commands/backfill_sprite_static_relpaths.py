"""Refresh ShapezGameIdentifier.sprite_static_relpath for all rows."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from django_apps.shapez_core.lab_sprite_path import resolve_sprite_static_relpath
from django_apps.shapez_core.models import ShapezGameIdentifier


class Command(BaseCommand):
    help = (
        "Re-evaluate sprite_static_relpath for every ShapezGameIdentifier row "
        "against the current static asset tree and update stale entries. "
        "Run after adding new SVG files to web/assets/sprites/."
    )

    def handle(self, *args: object, **options: object) -> None:
        updated = 0
        batch: list[ShapezGameIdentifier] = []

        for gid in ShapezGameIdentifier.objects.iterator(chunk_size=500):
            rel = resolve_sprite_static_relpath(gid.value)
            if gid.sprite_static_relpath != rel:
                gid.sprite_static_relpath = rel
                batch.append(gid)
            if len(batch) >= 500:
                ShapezGameIdentifier.objects.bulk_update(batch, ["sprite_static_relpath"])
                updated += len(batch)
                batch.clear()

        if batch:
            ShapezGameIdentifier.objects.bulk_update(batch, ["sprite_static_relpath"])
            updated += len(batch)

        self.stdout.write(self.style.SUCCESS(f"Updated {updated} sprite_static_relpath entries."))
