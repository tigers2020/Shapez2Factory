"""Asteroid sprite projection — DB-first ``GameContentAsset`` / ``AssetMetaReference`` resolver."""

from __future__ import annotations

from typing import Final

from django_apps.asteroid_lab.catalog.projection_source import (
    ProjectedSpriteRef,
    ProjectionSourceKind,
)
from django_apps.game_data.models import AssetMetaReference, GameContentAsset

_DETAIL_GAME_DATA_META: Final[str] = "game_data:asset_meta_reference"
_DETAIL_GAME_DATA_CONTENT: Final[str] = "game_data:content_asset"
_DETAIL_COMPAT_IDENTIFIER: Final[str] = "compat:shapez_game_identifier"
_DETAIL_COMPAT_UNRESOLVED: Final[str] = "compat:unresolved_layout_t"


def _normalize_layout_t(layout_t: str) -> str:
    return layout_t.strip()


def _sprite_path_from_content_asset(asset: GameContentAsset) -> str:
    logical = str(asset.logical_path).strip()
    if logical:
        return logical
    return str(asset.content_path).strip()


def _resolve_from_meta(
    layout_t: str,
    *,
    import_batch_id: int | None,
) -> ProjectedSpriteRef | None:
    qs = AssetMetaReference.objects.select_related("content_asset").filter(
        logical_path=layout_t,
    )
    if import_batch_id is not None:
        qs = qs.filter(import_batch_id=int(import_batch_id))
    meta = qs.order_by("source_row_index").first()
    if meta is None:
        return None
    asset = meta.content_asset
    sprite_path = str(meta.logical_path).strip() or _sprite_path_from_content_asset(asset)
    return ProjectedSpriteRef(
        layout_t=layout_t,
        sprite_path=sprite_path,
        canonical_id=meta.canonical_id,
        source_kind=ProjectionSourceKind.GAME_DATA_CANON,
        source_detail=f"{_DETAIL_GAME_DATA_META}:{meta.meta_stable_id}",
    )


def _resolve_from_content_asset(
    layout_t: str,
    *,
    import_batch_id: int | None,
) -> ProjectedSpriteRef | None:
    base = GameContentAsset.objects.filter(content_kind=GameContentAsset.ContentKind.SPRITE)
    if import_batch_id is not None:
        base = base.filter(import_batch_id=int(import_batch_id))
    for field in ("logical_path", "content_path"):
        asset = base.filter(**{field: layout_t}).order_by("source_row_index").first()
        if asset is not None:
            return ProjectedSpriteRef(
                layout_t=layout_t,
                sprite_path=_sprite_path_from_content_asset(asset),
                canonical_id=asset.canonical_id,
                source_kind=ProjectionSourceKind.GAME_DATA_CANON,
                source_detail=f"{_DETAIL_GAME_DATA_CONTENT}:{field}={asset.canonical_id}",
            )
    return None


def _compat_sprite_ref(layout_t: str) -> ProjectedSpriteRef:
    from django_apps.asteroid_lab.admin_lab_sprites import lab_sprite_relpath_from_tile_type
    from django_apps.shapez_core.services.lab_sprite_identifier_service import (
        get_lab_sprite_relpath_for_value,
    )

    rel = lab_sprite_relpath_from_tile_type(layout_t)
    if rel:
        return ProjectedSpriteRef(
            layout_t=layout_t,
            sprite_path=rel,
            canonical_id=None,
            source_kind=ProjectionSourceKind.TEMPORARY_COMPAT,
            source_detail=f"{_DETAIL_COMPAT_IDENTIFIER}:{layout_t}",
        )
    identifier_rel = get_lab_sprite_relpath_for_value(layout_t)
    if identifier_rel:
        return ProjectedSpriteRef(
            layout_t=layout_t,
            sprite_path=identifier_rel,
            canonical_id=None,
            source_kind=ProjectionSourceKind.TEMPORARY_COMPAT,
            source_detail=f"{_DETAIL_COMPAT_IDENTIFIER}:value={layout_t}",
        )
    return ProjectedSpriteRef(
        layout_t=layout_t,
        sprite_path=layout_t,
        canonical_id=None,
        source_kind=ProjectionSourceKind.TEMPORARY_COMPAT,
        source_detail=f"{_DETAIL_COMPAT_UNRESOLVED}:{layout_t}",
    )


def resolve_sprite_ref(
    layout_t: str,
    *,
    import_batch_id: int | None = None,
) -> ProjectedSpriteRef:
    """Resolve display sprite path for ``layout_t`` (output-only; not solver input)."""

    normalized = _normalize_layout_t(layout_t)
    if not normalized:
        return _compat_sprite_ref(layout_t)

    resolved = _resolve_from_meta(normalized, import_batch_id=import_batch_id)
    if resolved is not None:
        return resolved
    resolved = _resolve_from_content_asset(normalized, import_batch_id=import_batch_id)
    if resolved is not None:
        return resolved
    return _compat_sprite_ref(normalized)


__all__ = ["resolve_sprite_ref"]
