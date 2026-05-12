"""Preview scene for ``source_carrier=fluid`` (vortex tank glTF, sprites ``color-*``)."""

from __future__ import annotations

from django_apps.shapez_core.domain.shape_catalog import COLOR_KINDS
from django_apps.shapez_core.domain.shape_pattern import NormalizedShapePattern, QuadrantPosition
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_core.services.shape_render_scene import (
    SHAPE_MESH_KEYS,
    ShapeRenderCell,
    ShapeRenderScene,
    build_shape_render_scene,
)
from django_apps.shapez_solver.services.fluid_semantics import pure_fluid_color

FLUID_CARRIER_MESH_KEY = SHAPE_MESH_KEYS["t"]


def build_fluid_carrier_preview_scene(pattern: NormalizedShapePattern) -> ShapeRenderScene:
    """One centered vortex tank for valid pure-fluid patterns; else quadrant scene."""

    try:
        shape = shape_from_pattern(pattern)
        ink = pure_fluid_color(shape)
    except ValueError:
        return build_shape_render_scene(pattern)

    ref = next(
        (
            c
            for layer in pattern.layers
            for c in layer.cells
            if not (c.shape_code == "-" and c.color_code == "-")
        ),
        None,
    )
    if ref is None:
        return build_shape_render_scene(pattern)

    ck = COLOR_KINDS.get(ink)
    color_kind = ck.solver_kind if ck is not None else ref.color_kind
    cell = ShapeRenderCell(
        layer_index=0,
        quadrant_index=0,
        position=QuadrantPosition.SW,
        shape_code="t",
        color_code=ink,
        shape_kind="fluid_tank",
        color_kind=color_kind,
        mesh_key=FLUID_CARRIER_MESH_KEY,
        material_key=ink,
        transform_key="SW:L0",
    )
    return ShapeRenderScene(normalized_code=pattern.normalized_code, cells=(cell,))


__all__ = ["FLUID_CARRIER_MESH_KEY", "build_fluid_carrier_preview_scene"]
