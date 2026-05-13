"""Filesystem storage for baked atomic part PNGs under app static (versionable assets).

Use as ``ImageField(storage=shape_part_sprite_storage)``. Callable storage reads
``SHAPE_PART_SPRITE_*`` from ``settings`` when instantiated so tests can override paths.
"""

from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
from django.core.files.storage import FileSystemStorage


def shape_part_sprite_storage() -> FileSystemStorage:
    # Defaults match ``config/settings.py`` when both keys are absent (e.g. minimal test settings).
    r_missing = not hasattr(settings, "SHAPE_PART_SPRITE_STATIC_ROOT")
    p_missing = not hasattr(settings, "SHAPE_PART_SPRITE_URL_PREFIX")
    if r_missing and p_missing:
        root = Path(settings.BASE_DIR) / "django_apps" / "web" / "static" / "web"
        prefix = "/static/web/"
    elif r_missing or p_missing:
        raise ImproperlyConfigured(
            "SHAPE_PART_SPRITE_STATIC_ROOT and SHAPE_PART_SPRITE_URL_PREFIX must be "
            "configured together, or both omitted to use project defaults (see config/settings.py)."
        )
    else:
        root = settings.SHAPE_PART_SPRITE_STATIC_ROOT
        prefix = settings.SHAPE_PART_SPRITE_URL_PREFIX
        if root is None or prefix is None:
            raise ImproperlyConfigured(
                "SHAPE_PART_SPRITE_STATIC_ROOT and SHAPE_PART_SPRITE_URL_PREFIX must be "
                "non-null when set (see config/settings.py)."
            )
    return FileSystemStorage(location=str(root), base_url=prefix)
