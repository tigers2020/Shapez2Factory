"""Atomic part sprite catalog and preview_scene helpers for recipe tile composition."""

from __future__ import annotations

from collections.abc import Iterator

from django_apps.shapez_core.domain.shape_catalog import COLOR_KINDS, SHAPE_KINDS
from django_apps.shapez_core.domain.shape_pattern import quadrant_at_index
from django_apps.shapez_core.services.shape_render_scene import (
    SHAPE_MESH_KEYS,
    ShapeRenderCell,
    ShapeRenderScene,
)
from django_apps.shapez_solver.view_graph_serialization import serialize_render_scene

MESH_KEY_TO_SHAPE_CODE: dict[str, str] = {v: k for k, v in SHAPE_MESH_KEYS.items()}
"""Inverse of ``SHAPE_MESH_KEYS`` (game letter → glTF id)."""

PIN_MESH_KEY = SHAPE_MESH_KEYS["P"]

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


def make_sprite_key(
    shape_code: str,
    color_code: str,
    quadrant_index: int,
    renderer_version: str,
) -> str:
    """Stable manifest / DB key: ``{8-char layer}:{renderer_version}`` (e.g. ``Cr------:v1``)."""
    layer = atomic_layer_game_code(shape_code, color_code, quadrant_index)
    return f"{layer}:{renderer_version}"


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
        for color_code in palette:
            material_key = color_code
            for quadrant_index in range(4):
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
    "atomic_layer_game_code",
    "build_atomic_preview_scene",
    "build_pedestal_only_preview_scene",
    "iter_atomic_sprite_specs",
    "make_pedestal_sprite_key",
    "make_sprite_key",
]
