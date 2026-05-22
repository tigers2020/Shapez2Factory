"""Align ``assets/shape_part_sprites/`` PNG names with ``ShapePartSprite.sprite_key``."""

from __future__ import annotations

from pathlib import Path

from django.core.management.base import BaseCommand

from django_apps.web.models import ShapePartSprite
from django_apps.web.services.shape_part_sprites import (
    TANK_VORTEX_MESH_KEY,
    canonical_shape_part_sprite_basename,
    iter_atomic_sprite_specs,
    make_pedestal_sprite_key,
    make_sprite_key,
    make_tank_vortex_sprite_key,
    shape_part_sprite_image_relpath,
    sprite_key_from_storage_basename,
    sprite_key_to_storage_basename,
)
from django_apps.web.shape_part_sprite_storage import shape_part_sprite_storage


class Command(BaseCommand):
    help = (
        "Align shape_part_sprites PNG basenames with DB sprite_key "
        "(colon → underscore; drop Django upload hash suffixes)."
    )

    def add_arguments(self, parser) -> None:
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Print planned renames/deletes without touching disk or DB.",
        )

    def handle(self, *args, **options) -> None:
        dry_run: bool = bool(options["dry_run"])
        storage = shape_part_sprite_storage()
        root = Path(storage.location)
        upload_to = str(ShapePartSprite._meta.get_field("image").upload_to).strip("/")
        sprite_dir = root.joinpath(*upload_to.split("/"))
        if not sprite_dir.is_dir():
            self.stdout.write(self.style.WARNING(f"No sprite directory: {sprite_dir}"))
            return

        known_keys = _catalog_sprite_keys(renderer_version="v1")
        # sprite_key -> paths on disk (case-sensitive; ``Cr------`` ≠ ``cr------``)
        by_key: dict[str, list[Path]] = {}
        for path in sorted(sprite_dir.glob("*.png")):
            canonical = canonical_shape_part_sprite_basename(path.name)
            sprite_key = sprite_key_from_storage_basename(canonical)
            if sprite_key is None:
                self.stdout.write(self.style.WARNING(f"Skip unrecognized basename: {path.name}"))
                continue
            if sprite_key not in known_keys:
                self.stdout.write(
                    self.style.WARNING(f"Skip non-catalog sprite_key {sprite_key!r}: {path.name}")
                )
                continue
            by_key.setdefault(sprite_key, []).append(path)

        renamed = 0
        removed = 0
        for sprite_key, paths in sorted(by_key.items()):
            target_name = sprite_key_to_storage_basename(sprite_key)
            target_path = sprite_dir / target_name
            for path in paths:
                if path.name == target_name:
                    continue
                if target_path.exists():
                    self._log(dry_run, f"delete duplicate {path.name} (keep {target_name})")
                    if not dry_run:
                        path.unlink()
                    removed += 1
                else:
                    self._log(dry_run, f"rename {path.name} -> {target_name}")
                    if not dry_run:
                        path.rename(target_path)
                    renamed += 1
                    target_path = sprite_dir / target_name

        db_updated = 0
        expected_rel = shape_part_sprite_image_relpath
        for row in ShapePartSprite.objects.only("pk", "sprite_key", "image"):
            rel = expected_rel(row.sprite_key)
            if str(row.image or "") == rel:
                continue
            self._log(dry_run, f"db pk={row.pk} image -> {rel}")
            if not dry_run:
                row.image = rel
                row.save(update_fields=["image"])
            db_updated += 1

        summary = f"renamed={renamed} removed_dupes={removed} db_image_updated={db_updated}"
        if dry_run:
            self.stdout.write(self.style.WARNING(f"[dry-run] {summary}"))
        else:
            self.stdout.write(self.style.SUCCESS(summary))

    def _log(self, dry_run: bool, message: str) -> None:
        prefix = "[dry-run] " if dry_run else ""
        self.stdout.write(prefix + message)


def _catalog_sprite_keys(*, renderer_version: str) -> set[str]:
    """All ``sprite_key`` values produced by :func:`iter_atomic_sprite_specs` (+ pedestal)."""

    from django_apps.web.services.shape_part_sprites import MESH_KEY_TO_SHAPE_CODE

    out: set[str] = set()
    for mesh_key, color_code, _material_key, quadrant_index in iter_atomic_sprite_specs():
        if mesh_key == TANK_VORTEX_MESH_KEY:
            out.add(make_tank_vortex_sprite_key(color_code, renderer_version))
        else:
            shape_code = MESH_KEY_TO_SHAPE_CODE.get(mesh_key)
            if shape_code is None:
                continue
            out.add(make_sprite_key(shape_code, color_code, quadrant_index, renderer_version))
    out.add(make_pedestal_sprite_key(renderer_version))
    return out
