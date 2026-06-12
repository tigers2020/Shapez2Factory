"""Regenerate admin changelist thumbnails for ReconstructedAsteroidMap rows."""

from __future__ import annotations

from django.core.management.base import BaseCommand, CommandError

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.reconstructed_map_thumbnail_service import (
    sync_admin_list_thumbnail,
)


class Command(BaseCommand):  # type: ignore[misc]
    help = "Regenerate admin_list_thumbnail for ReconstructedAsteroidMap rows."

    def add_arguments(self, parser: object) -> None:
        parser.add_argument("--pk", type=int, action="append", default=[])
        parser.add_argument("--all", action="store_true")
        parser.add_argument("--force", action="store_true")

    def handle(self, *args: object, **options: object) -> None:
        qs = m.ReconstructedAsteroidMap.objects.all()
        pks: list[int] = list(options["pk"] or [])
        if pks:
            qs = qs.filter(pk__in=pks)
        elif options["all"]:
            pass
        else:
            raise CommandError("Specify --pk ID (repeatable) or --all")

        qs = qs.only(
            "pk",
            "decoded_json",
            "admin_list_thumbnail",
            "admin_list_thumbnail_hash",
            "admin_list_thumbnail_renderer_version",
        )
        updated = 0
        for row in qs.iterator(chunk_size=50):
            if sync_admin_list_thumbnail(row, force=bool(options["force"])):
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Updated {updated} thumbnails."))
