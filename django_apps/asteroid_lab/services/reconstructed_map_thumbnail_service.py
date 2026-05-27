"""Admin changelist thumbnails for ReconstructedAsteroidMap (display-only)."""

from __future__ import annotations

import logging

from django.core.files.base import ContentFile

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.admin_map_list_thumbnail import (
    ADMIN_LIST_THUMBNAIL_RENDERER_VERSION,
    ListThumbnailWindow,
    canonical_decoded_json_hash,
    compute_list_thumbnail_window,
    render_list_thumbnail_image_bytes,
)

logger = logging.getLogger(__name__)


def _thumbnail_error_types() -> tuple[type[BaseException], ...]:
    types: tuple[type[BaseException], ...] = (ValueError, OSError, TypeError)
    try:
        from PIL import UnidentifiedImageError  # noqa: PLC0415

        return types + (UnidentifiedImageError,)
    except ImportError:
        return types


def clear_admin_list_thumbnail(pk: int) -> None:
    row = m.ReconstructedAsteroidMap.objects.filter(pk=int(pk)).first()
    if row is None:
        return
    if row.admin_list_thumbnail:
        row.admin_list_thumbnail.delete(save=False)
    m.ReconstructedAsteroidMap.objects.filter(pk=int(pk)).update(
        admin_list_thumbnail="",
        admin_list_thumbnail_hash="",
        admin_list_thumbnail_renderer_version="",
        admin_list_thumbnail_cell_count=0,
        admin_list_thumbnail_grid_w=0,
        admin_list_thumbnail_grid_h=0,
        admin_list_thumbnail_truncated=False,
    )


def _persist_thumbnail_metadata(
    *,
    pk: int,
    thumbnail_name: str,
    new_hash: str,
    win: ListThumbnailWindow,
) -> None:
    m.ReconstructedAsteroidMap.objects.filter(pk=int(pk)).update(
        admin_list_thumbnail=thumbnail_name,
        admin_list_thumbnail_hash=new_hash,
        admin_list_thumbnail_renderer_version=ADMIN_LIST_THUMBNAIL_RENDERER_VERSION,
        admin_list_thumbnail_cell_count=win.cell_count,
        admin_list_thumbnail_grid_w=win.grid_w,
        admin_list_thumbnail_grid_h=win.grid_h,
        admin_list_thumbnail_truncated=win.truncated,
    )


def _write_thumbnail_for_row(row: m.ReconstructedAsteroidMap, decoded: dict, new_hash: str) -> None:
    win = compute_list_thumbnail_window(decoded)
    if win is None:
        clear_admin_list_thumbnail(int(row.pk))
        return
    data, ext = render_list_thumbnail_image_bytes(decoded)
    name = f"recon_map_{row.pk}_{new_hash[:12]}.{ext}"
    row.admin_list_thumbnail.save(name, ContentFile(data), save=False)
    thumbnail_name = row.admin_list_thumbnail.name
    if not thumbnail_name:
        msg = "thumbnail save produced empty name"
        raise OSError(msg)
    _persist_thumbnail_metadata(
        pk=int(row.pk),
        thumbnail_name=thumbnail_name,
        new_hash=new_hash,
        win=win,
    )


def sync_admin_list_thumbnail(
    row: m.ReconstructedAsteroidMap,
    *,
    force: bool = False,
) -> bool:
    """Generate thumbnail when hash/version mismatch. Never raises to callers."""

    decoded = dict(row.decoded_json or {})
    new_hash = canonical_decoded_json_hash(decoded) if decoded else ""
    if (
        not force
        and row.admin_list_thumbnail
        and row.admin_list_thumbnail_hash == new_hash
        and row.admin_list_thumbnail_renderer_version == ADMIN_LIST_THUMBNAIL_RENDERER_VERSION
    ):
        return False
    if not decoded:
        clear_admin_list_thumbnail(int(row.pk))
        return True
    try:
        _write_thumbnail_for_row(row, decoded, new_hash)
    except _thumbnail_error_types() as exc:
        logger.warning(
            "Failed admin list thumbnail for ReconstructedAsteroidMap pk=%s: %s",
            row.pk,
            exc,
            exc_info=True,
        )
        clear_admin_list_thumbnail(int(row.pk))
    except Exception as exc:  # noqa: BLE001 — storage/backend must not fail persist
        logger.warning(
            "Unexpected admin list thumbnail failure for ReconstructedAsteroidMap pk=%s: %s",
            row.pk,
            exc,
            exc_info=True,
        )
        clear_admin_list_thumbnail(int(row.pk))
    return True


__all__ = [
    "clear_admin_list_thumbnail",
    "sync_admin_list_thumbnail",
]
