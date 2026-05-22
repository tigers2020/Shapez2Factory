"""Atomic part sprite catalog and preview_scene helpers for recipe tile composition."""

from __future__ import annotations

import re
from collections.abc import Iterator

from django_apps.shapez_core.domain.shape_catalog import COLOR_KINDS, SHAPE_KINDS
from django_apps.shapez_core.domain.shape_pattern import quadrant_at_index
from django_apps.shapez_core.services.shape_render_scene import (
    SHAPE_MESH_KEYS,
    ShapeRenderCell,
    ShapeRenderScene,
    serialize_render_scene,
)

MESH_KEY_TO_SHAPE_CODE: dict[str, str] = {v: k for k, v in SHAPE_MESH_KEYS.items()}
"""Inverse of ``SHAPE_MESH_KEYS`` (game letter → glTF id)."""

PIN_MESH_KEY = SHAPE_MESH_KEYS["P"]

# Vendor ``defaultFluidTank.gltf`` (shape letter ``t``).
# Distinct from ``default_fluid_tank`` viewer paths.
TANK_VORTEX_MESH_KEY = SHAPE_MESH_KEYS["t"]

# Reserved DB row: pedestal-only bake (not a game mesh). See build_pedestal_only_preview_scene.
PEDESTAL_ONLY_MESH_KEY = "pedestal"


def atomic_layer_game_code(shape_code: str, color_code: str, quadrant_index: int) -> str:
    """One shape layer as 8 characters (four quadrant tokens), matching game shape-code notation."""
    slots = ["--", "--", "--", "--"]
    qi = quadrant_index
    if shape_code == "P":
        slots[qi] = "P-"
    else:
        slots[qi] = shape_code + color_code
    return "".join(slots)


def make_tank_vortex_sprite_key(color_code: str, renderer_version: str) -> str:
    """Manifest / file key aligned with glTF ``extras.script`` naming: ``color-{letter}:v``."""
    return f"color-{color_code}:{renderer_version}"


def make_sprite_key(
    shape_code: str,
    color_code: str,
    quadrant_index: int,
    renderer_version: str,
) -> str:
    """Stable manifest / DB key: ``{8-char layer}:{renderer_version}`` (e.g. ``Cr------:v1``)."""
    layer = atomic_layer_game_code(shape_code, color_code, quadrant_index)
    return f"{layer}:{renderer_version}"


_SHAPE_PART_SPRITE_UPLOAD_PREFIX = "assets/shape_part_sprites/"
_DJANGO_UPLOAD_HASH_SUFFIX_RE = re.compile(r"^(.+)_v(\d+)_[A-Za-z0-9]{5,}\.png$")


def sprite_key_to_storage_basename(sprite_key: str) -> str:
    """PNG basename for ``sprite_key`` (``:`` → ``_``; safe on Windows)."""

    return sprite_key.replace(":", "_") + ".png"


def sprite_key_from_storage_basename(basename: str) -> str | None:
    """Inverse of :func:`sprite_key_to_storage_basename`; ``None`` when not a baked part key."""

    name = basename.strip()
    if not name.lower().endswith(".png"):
        return None
    stem = name[:-4]
    if not stem:
        return None
    idx = stem.rfind("_v")
    if idx < 1:
        return None
    version = stem[idx + 1 :]
    if not version.startswith("v") or not version[1:].isdigit():
        return None
    return f"{stem[:idx]}:{version}"


def canonical_shape_part_sprite_basename(basename: str) -> str:
    """Strip Django collision suffixes (``*_v1_Ab12cdE.png`` → ``*_v1.png``)."""

    m = _DJANGO_UPLOAD_HASH_SUFFIX_RE.match(basename)
    if m:
        return f"{m.group(1)}_v{m.group(2)}.png"
    return basename


def shape_part_sprite_image_relpath(sprite_key: str) -> str:
    """Value for :class:`~django_apps.web.models.ShapePartSprite` ``image`` field."""

    return _SHAPE_PART_SPRITE_UPLOAD_PREFIX + sprite_key_to_storage_basename(sprite_key)


def iter_atomic_sprite_specs(
    *,
    limit: int | None = None,
) -> Iterator[tuple[str, str, str, int]]:
    """Enumerate finite mesh × non-empty color × quadrant for offline sprite baking."""
    mesh_keys = sorted({mk for mk in SHAPE_MESH_KEYS.values() if mk != "unknown"})
    color_codes = sorted(code for code, ck in COLOR_KINDS.items() if not ck.empty)
    n = 0
    for mesh_key in mesh_keys:
        palette = ("-",) if mesh_key == PIN_MESH_KEY else tuple(color_codes)
        quadrants = (0,) if mesh_key == TANK_VORTEX_MESH_KEY else tuple(range(4))
        for color_code in palette:
            material_key = color_code
            for quadrant_index in quadrants:
                if limit is not None and n >= limit:
                    return
                yield mesh_key, color_code, material_key, quadrant_index
                n += 1


def make_pedestal_sprite_key(renderer_version: str) -> str:
    return f"pedestal:{renderer_version}"


def build_pedestal_only_preview_scene() -> dict[str, object]:
    """Empty layer, pedestal on; for transparent tile underlay."""
    scene = ShapeRenderScene(normalized_code="--------", cells=())
    out = serialize_render_scene(scene)
    out["include_pedestal"] = True
    out["transparent_background"] = True
    return out


def build_atomic_preview_scene(
    mesh_key: str,
    color_code: str,
    material_key: str,
    quadrant_index: int,
) -> dict[str, object]:
    shape_code = MESH_KEY_TO_SHAPE_CODE.get(mesh_key)
    if shape_code is None:
        msg = f"unknown mesh_key for atomic sprite: {mesh_key!r}"
        raise ValueError(msg)
    sk = SHAPE_KINDS.get(shape_code)
    ck = COLOR_KINDS.get(color_code)
    if sk is None or ck is None:
        msg = f"invalid shape/color for atomic sprite: {shape_code!r} / {color_code!r}"
        raise ValueError(msg)
    if mesh_key == TANK_VORTEX_MESH_KEY:
        quadrant_index = 0
    pos = quadrant_at_index(quadrant_index)
    layer_index = 0
    cell = ShapeRenderCell(
        layer_index=layer_index,
        quadrant_index=quadrant_index,
        position=pos,
        shape_code=shape_code,
        color_code=color_code,
        shape_kind=sk.solver_kind,
        color_kind=ck.solver_kind,
        mesh_key=mesh_key,
        material_key=material_key,
        transform_key=f"{pos.value}:L{layer_index}",
    )
    layer_code = atomic_layer_game_code(shape_code, color_code, quadrant_index)
    scene = ShapeRenderScene(normalized_code=layer_code, cells=(cell,))
    out = serialize_render_scene(scene)
    out["include_pedestal"] = False
    out["transparent_background"] = True
    return out


__all__ = [
    "MESH_KEY_TO_SHAPE_CODE",
    "PEDESTAL_ONLY_MESH_KEY",
    "PIN_MESH_KEY",
    "TANK_VORTEX_MESH_KEY",
    "atomic_layer_game_code",
    "build_atomic_preview_scene",
    "build_pedestal_only_preview_scene",
    "canonical_shape_part_sprite_basename",
    "iter_atomic_sprite_specs",
    "make_pedestal_sprite_key",
    "make_sprite_key",
    "make_tank_vortex_sprite_key",
    "shape_part_sprite_image_relpath",
    "sprite_key_from_storage_basename",
    "sprite_key_to_storage_basename",
]
