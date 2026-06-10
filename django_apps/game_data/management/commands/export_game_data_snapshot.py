"""``manage.py export_game_data_snapshot --out <path>`` — ORM → frozen snapshot JSON (PR-CLI-2b)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser

from django_apps.game_data.services.game_data_snapshot_export import (
    GameDataSnapshotExportError,
    build_game_data_snapshot_payload,
)


class Command(BaseCommand):
    help = "Export the game_data snapshot (EVTC capacity) used by the Asteroid Lab CLI core."

    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument(
            "--out",
            required=True,
            help="Output path for the snapshot JSON file.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        out_path = Path(options["out"])
        try:
            payload = build_game_data_snapshot_payload()
        except GameDataSnapshotExportError as exc:
            raise CommandError(str(exc)) from exc
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"wrote game_data snapshot ({payload['game_data_dump_hash']}) to {out_path}"
            )
        )
