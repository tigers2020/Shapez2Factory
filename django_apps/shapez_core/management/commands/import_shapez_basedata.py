"""Import a shapez2 basedata bundle (IVVD) into the canonical DB."""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from django_apps.shapez_core.services.basedata_import_service import import_basedata_bundle


class Command(BaseCommand):
    help = (
        "Import basedata-v1137 layout from SHAPEZ_BASEDATA_ROOT or --root "
        "into shapez_core IVVD tables."
    )

    def add_arguments(self, parser) -> None:  # type: ignore[no-untyped-def]
        parser.add_argument(
            "--root",
            type=str,
            default=None,
            help="Path to basedata root (default: settings.SHAPEZ_BASEDATA_ROOT).",
        )
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Delete existing ShapezBasedataRelease for the same game_version and re-import.",
        )
        parser.add_argument(
            "--strict-seal",
            action="store_true",
            dest="strict_seal",
            help=(
                "Abort with error if non-superseded error-level integrity issues "
                "exist before seal."
            ),
        )

    def handle(self, *args, **options) -> None:  # type: ignore[no-untyped-def]
        raw = options["root"]
        root = Path(raw) if raw else Path(settings.SHAPEZ_BASEDATA_ROOT)
        try:
            release = import_basedata_bundle(
                root,
                replace=bool(options["replace"]),
                strict_seal=bool(options["strict_seal"]),
            )
        except (OSError, ValueError, FileNotFoundError) as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported game_version={release.game_version} "
                f"release_hash={release.release_integrity_hash!r} "
                f"documents={release.document_count}"
            )
        )
