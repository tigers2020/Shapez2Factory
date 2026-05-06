"""Filesystem storage for baked atomic part PNGs under app static (versionable assets).

Use as ``ImageField(storage=shape_part_sprite_storage)``. Callable storage reads
``SHAPE_PART_SPRITE_*`` from ``settings`` when instantiated so tests can override paths.
"""

from __future__ import annotations

from django.conf import settings
from django.core.files.storage import FileSystemStorage


def shape_part_sprite_storage() -> FileSystemStorage:
    return FileSystemStorage(
        location=str(settings.SHAPE_PART_SPRITE_STATIC_ROOT),
        base_url=settings.SHAPE_PART_SPRITE_URL_PREFIX,
    )
