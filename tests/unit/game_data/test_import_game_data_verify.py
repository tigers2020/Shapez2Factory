"""TDD: import_game_data --verify (manifest pin vs latest ImportBatch)."""

from __future__ import annotations

import shutil

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.django_db
def test_import_game_data_verify_passes_when_disk_matches_latest_batch(
    imported_game_data_batch,
    game_data_dir,
) -> None:
    call_command("import_game_data", verify=True, source=str(game_data_dir))


@pytest.mark.django_db
def test_import_game_data_verify_fails_when_manifest_hash_differs(
    imported_game_data_batch,
    game_data_dir,
    tmp_path,
) -> None:
    stale_dir = tmp_path / "stale_bundle"
    shutil.copytree(game_data_dir, stale_dir)
    manifest = stale_dir / "manifest.json"
    manifest.write_text(manifest.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    with pytest.raises(CommandError, match="manifest"):
        call_command("import_game_data", verify=True, source=str(stale_dir))


@pytest.mark.django_db
def test_import_game_data_verify_fails_when_no_import_batch(
    game_data_dir,
    db,
) -> None:
    from django_apps.game_data.models import ImportBatch

    ImportBatch.objects.all().delete()

    with pytest.raises(CommandError, match="no import batch"):
        call_command("import_game_data", verify=True, source=str(game_data_dir))
