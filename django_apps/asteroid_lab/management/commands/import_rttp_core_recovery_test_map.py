"""Import tests/fixtures/asteroid_lab/test_map.txt as rttp-core-recovery-test-map."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from django_apps.asteroid_lab.contracts.rttp_recovery_evidence import (
    RTTP_CORE_RECOVERY_TEST_MAP_FIXTURE,
    RTTP_CORE_RECOVERY_TEST_MAP_SLUG,
)


def import_core_recovery_test_map(*, replace: bool = False) -> int:
    from django_apps.asteroid_lab import models as m
    from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input

    repo_root = Path(__file__).resolve().parents[4]
    fixture_path = repo_root / RTTP_CORE_RECOVERY_TEST_MAP_FIXTURE
    copy = fixture_path.read_text(encoding="utf-8").strip()

    proj, created = m.AsteroidProject.objects.get_or_create(
        slug=RTTP_CORE_RECOVERY_TEST_MAP_SLUG,
        defaults={"name": "RTTP core recovery test map (test_map.txt)"},
    )
    if not created and replace:
        m.AsteroidMapInput.objects.filter(project_id=proj.pk).delete()
    elif not created and proj.map_inputs.exists():
        return int(proj.pk)

    create_copy_code_map_input(proj, copy)
    return int(proj.pk)


class Command(BaseCommand):  # type: ignore[misc]
    help = f"Import {RTTP_CORE_RECOVERY_TEST_MAP_FIXTURE} as {RTTP_CORE_RECOVERY_TEST_MAP_SLUG}."

    def add_arguments(self, parser: Any) -> None:
        parser.add_argument(
            "--replace",
            action="store_true",
            help="Replace existing map input for the slug.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        project_id = import_core_recovery_test_map(replace=bool(options.get("replace")))
        self.stdout.write(
            self.style.SUCCESS(
                f"Imported {RTTP_CORE_RECOVERY_TEST_MAP_SLUG} (project_id={project_id})"
            )
        )


__all__ = ["Command", "import_core_recovery_test_map"]
