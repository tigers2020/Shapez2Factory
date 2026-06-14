"""Import normalized game_data from JSON bundle."""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand, CommandError, CommandParser

from django_apps.game_data.importers import GameDataImporter
from django_apps.game_data.services.bundle_gate import (
    GameDataBundleInvalid,
    validate_game_data_bundle,
)
from django_apps.game_data.services.import_guards import GameDataImportBlockedError
from django_apps.game_data.services.import_verify import (
    GameDataVerifyError,
    verify_game_data_source,
)


class Command(BaseCommand):
    help = "Import game_data JSON bundle into normalized models (auto-resolve via bundle_gate)."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--source",
            type=str,
            default=None,
            help=(
                "Directory containing manifest.json and artifact JSON files "
                "(default: auto-resolve repo candidates)."
            ),
        )
        parser.add_argument(
            "--batch-name",
            type=str,
            default="default",
            help="Human-readable label stored on ImportBatch.",
        )
        parser.add_argument(
            "--verify",
            action="store_true",
            help="Verify on-disk manifest matches latest ImportBatch (no import).",
        )

    def handle(self, *args: object, **options: object) -> None:
        source_raw = options.get("source")
        source = Path(str(source_raw)) if source_raw else None
        batch_name = str(options["batch_name"])

        if bool(options.get("verify")):
            try:
                batch = verify_game_data_source(source)
            except GameDataBundleInvalid as exc:
                raise CommandError(str(exc)) from exc
            except GameDataVerifyError as exc:
                raise CommandError(str(exc)) from exc
            self.stdout.write(
                self.style.SUCCESS(
                    f"Verify OK: manifest matches ImportBatch id={batch.pk} "
                    f"({batch.manifest_self_hash[:16]}…)"
                )
            )
            return

        try:
            bundle = validate_game_data_bundle(source=source)
        except GameDataBundleInvalid as exc:
            raise CommandError(str(exc)) from exc

        try:
            summary = GameDataImporter(bundle, batch_name=batch_name).run()
        except GameDataImportBlockedError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS("Import complete"))
        for key, value in summary.items():
            self.stdout.write(f"  {key}: {value}")
