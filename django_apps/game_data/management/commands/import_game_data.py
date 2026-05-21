"""Import normalized game_data from JSON bundle."""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandParser

from django_apps.game_data.importers import GameDataImporter
from django_apps.game_data.services.import_guards import GameDataImportBlockedError


class Command(BaseCommand):
    help = "Import documents/game_data JSON into normalized game_data models."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--source",
            type=str,
            default="documents/game_data",
            help="Directory containing manifest.json and artifact JSON files.",
        )
        parser.add_argument(
            "--batch-name",
            type=str,
            default="default",
            help="Human-readable label stored on ImportBatch.",
        )

    def handle(self, *args: object, **options: object) -> None:
        source = Path(str(options["source"]))
        batch_name = str(options["batch_name"])
        if not (source / "manifest.json").is_file():
            self.stderr.write(self.style.ERROR(f"manifest.json not found in {source}"))
            return
        try:
            summary = GameDataImporter(source, batch_name=batch_name).run()
        except GameDataImportBlockedError as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            return
        self.stdout.write(self.style.SUCCESS("Import complete"))
        for key, value in summary.items():
            self.stdout.write(f"  {key}: {value}")
