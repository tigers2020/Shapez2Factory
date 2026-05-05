"""Preview scene for recipe graph nodes with ``source_carrier=fluid`` (single tank glTF)."""

from __future__ import annotations

from django_apps.shapez_core.domain.shape_pattern import NormalizedShapePattern, QuadrantPosition
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_core.services.shape_render_scene import (
    ShapeRenderCell,
    ShapeRenderScene,
    build_shape_render_scene,
)
from django_apps.shapez_solver.services.fluid_semantics import pure_fluid_color

FLUID_CARRIER_MESH_KEY = "default_fluid_tank_filled"


def build_fluid_carrier_preview_scene(pattern: NormalizedShapePattern) -> ShapeRenderScene:
    """One centered tank mesh when the pattern is a valid pure-fluid shape; else quadrant scene."""

    try:
        shape = shape_from_pattern(pattern)
        ink = pure_fluid_color(shape)
    except ValueError:
        return build_shape_render_scene(pattern)

    ref = next(
        (c for layer in pattern.layers for c in layer.cells if c.shape_code != "-"),
        None,
    )
    if ref is None:
        return build_shape_render_scene(pattern)

    cell = ShapeRenderCell(
        layer_index=0,
        quadrant_index=0,
        position=QuadrantPosition.SW,
        shape_code="C",
        color_code=ink,
        shape_kind=ref.shape_kind,
        color_kind=ref.color_kind,
        mesh_key=FLUID_CARRIER_MESH_KEY,
        material_key=ink,
        transform_key="SW:L0",
    )
    return ShapeRenderScene(normalized_code=pattern.normalized_code, cells=(cell,))


__all__ = ["FLUID_CARRIER_MESH_KEY", "build_fluid_carrier_preview_scene"]
