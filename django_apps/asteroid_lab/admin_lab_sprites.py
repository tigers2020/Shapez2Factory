"""Lab blueprint cell → static sprite relpath + display rotation (Admin mini-map).

Sprite paths come from :class:`~django_apps.shapez_core.models.ShapezGameIdentifier`
``sprite_static_relpath`` (``T`` = identifier ``value``). See
:mod:`django_apps.shapez_core.services.lab_sprite_identifier_service`.

**Contract:** ``T`` / ``cell_kind`` → asset relpath under ``web/assets/sprites/``;
domain ``R`` → quarter-turns for CSS ``rotate`` only
(see ``documents/ai/lab_map_rendering_contract.md``).
Resolve both via :func:`lab_sprite_resolve`.
"""

from __future__ import annotations

import math

from django_apps.shapez_core.lab_sprite_path import resolve_sprite_static_relpath
from django_apps.shapez_core.services.lab_sprite_identifier_service import (
    get_lab_sprite_relpath_for_value,
)

# ``cell_kind`` (unambiguous) → blueprint ``T`` string; then DB ``sprite_static_relpath``.
LAB_SPRITE_CELL_KIND_FALLBACK: dict[str, str] = {
    "fluid_miner": "Layout_FluidMiner",
    "fluid_miner_extension": "Layout_FluidMinerExtension",
    "shape_miner": "Layout_ShapeMiner",
    "shape_miner_extension": "Layout_ShapeMinerExtension",
}


def normalize_lab_rotation_q(value: object) -> int:
    """Mirror ``normalizeQuarterTurns`` in ``asteroid_miner_layout_lab.js`` (0..3)."""

    if value is None:
        return 0
    try:
        x = float(value)
    except (TypeError, ValueError):
        return 0
    if math.isnan(x) or math.isinf(x):
        return 0
    n = math.trunc(x)
    return (n % 4 + 4) % 4


def lab_sprite_relpath_from_tile_type(tile_type: str | None) -> str | None:
    """Identifier ``T`` → ``sprite_static_relpath`` when present in basedata import."""

    t = "" if tile_type is None else str(tile_type).strip()
    if not t:
        return None
    rel = resolve_sprite_static_relpath(t)
    if rel:
        return rel
    rel = get_lab_sprite_relpath_for_value(t)
    return rel if rel else None


def lab_sprite_relpath_from_cell_kind(cell_kind: str | None) -> str | None:
    ck = "" if cell_kind is None else str(cell_kind)
    if not ck:
        return None
    ident = LAB_SPRITE_CELL_KIND_FALLBACK.get(ck)
    if not ident:
        return None
    return lab_sprite_relpath_from_tile_type(ident)


def lab_sprite_resolve(
    *,
    tile_type: str,
    cell_kind: str,
    rotation: object,
) -> tuple[str | None, int]:
    """Return ``(sprite_static_relpath_or_none, display_rotation_quarters)``.

    Derived from ``T``, ``cell_kind``, and domain ``R``.
    """

    rel = lab_sprite_relpath_from_tile_type(tile_type or None)
    if rel is None:
        rel = lab_sprite_relpath_from_cell_kind(cell_kind or None)
    return rel, normalize_lab_rotation_q(rotation)


def lab_sprite_relpath_for_cell(*, tile_type: str, cell_kind: str) -> str | None:
    """Static relpath only (no ``R``). Prefer :func:`lab_sprite_resolve` for ``T``+``R`` wiring."""

    r, _ = lab_sprite_resolve(tile_type=tile_type, cell_kind=cell_kind, rotation=0)
    return r
