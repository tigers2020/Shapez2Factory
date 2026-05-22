"""Rebuild GameDataNamespace / GameDataSection for admin browse after flush or loaddata."""

from __future__ import annotations

from django.core.management.base import BaseCommand

from django_apps.game_data.services.taxonomy_seed import rebuild_game_data_taxonomy


class Command(BaseCommand):
    help = (
        "Rebuild admin browse taxonomy from game_data model verbose_name_plural labels. "
        "Run after flush, loaddata, or import when namespaces are empty."
    )

    def handle(self, *args: object, **options: object) -> None:
        summary = rebuild_game_data_taxonomy()
        self.stdout.write(self.style.SUCCESS("Taxonomy seed complete"))
        for key, value in summary.items():
            self.stdout.write(f"  {key}: {value}")
