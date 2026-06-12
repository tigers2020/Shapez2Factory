"""Bake atomic quadrant PNGs via Playwright and persist ``ShapePartSprite`` rows."""

from __future__ import annotations

from argparse import ArgumentParser

from django.core.management.base import BaseCommand

from django_apps.web.services.shape_part_sprite_generation import generate_shape_part_sprites


class Command(BaseCommand):  # type: ignore[misc]
    help = (
        "Render atomic shape part PNGs (mesh × color × quadrant) "
        "and upsert ShapePartSprite rows."
    )

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--renderer-version",
            default="v1",
            help="Stored on each row and used by tile manifest (default: v1).",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print variant count / keys only; do not invoke Playwright or write DB.",
        )
        parser.add_argument(
            "--skip-existing",
            action="store_true",
            help="Skip variants that already have a DB row with an image file on storage.",
        )
        parser.add_argument(
            "--limit",
            type=int,
            default=None,
            help="Process at most N variants (after enumeration / skip filter).",
        )

    def handle(self, *args: object, **options: object) -> None:
        renderer_version: str = options["renderer_version"]
        dry_run: bool = options["dry_run"]
        skip_existing: bool = options["skip_existing"]
        limit: int | None = options["limit"]

        try:
            stats = generate_shape_part_sprites(
                renderer_version=renderer_version,
                skip_existing=skip_existing,
                limit=limit,
                dry_run=dry_run,
                stdout=self.stdout,
                stderr=self.stderr,
            )
        except RuntimeError as exc:
            self.stderr.write(f"{exc}\n")
            raise SystemExit(1) from exc
        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    "shape part sprites: rendered="
                    f"{stats.rendered} skipped_existing={stats.skipped} errors={stats.errors}"
                )
            )
