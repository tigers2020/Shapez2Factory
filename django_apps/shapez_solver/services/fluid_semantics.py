"""Pure color fluid encoded as a Shape (uniform ink on paintable parts).

Used by COLOR_MIXER (fluid + fluid) and PAINTER (shape + fluid wire).
"""

from __future__ import annotations

from django_apps.shapez_core.domain.shape import Shape, ShapeLayer, ShapePart


def infer_uniform_paint_color(shape: Shape) -> str | None:
    """Non-empty, non-pin quadrants must share one color; else ``None``."""

    colors: list[str] = []
    for layer in shape.layers:
        for part in layer.quadrants:
            if part.is_empty or part.is_pin:
                continue
            colors.append(part.color)
    if not colors:
        return None
    first = colors[0]
    if any(c != first for c in colors):
        return None
    return first


def pure_fluid_color(shape: Shape) -> str:
    """Return the single fluid color letter for a pure-fluid carrier shape."""

    for part in shape.non_empty_parts():
        if part.is_crystal:
            raise ValueError("pure fluid shape cannot contain crystal parts")
    color = infer_uniform_paint_color(shape)
    if color is None:
        raise ValueError(
            "pure fluid requires a uniform paint color on all non-empty, non-pin quadrants",
        )
    return color


def uniform_fluid_output_from_template(template: Shape, ink_color: str) -> Shape:
    """Recolor every paintable (non-empty, non-pin) quadrant; pins and empties unchanged."""

    new_layers: list[ShapeLayer] = []
    for layer in template.layers:
        quads: list[ShapePart] = []
        for part in layer.quadrants:
            if part.is_empty or part.is_pin:
                quads.append(part)
            else:
                quads.append(ShapePart(kind=part.kind, color=ink_color, material=part.material))
        new_layers.append(ShapeLayer(quadrants=(quads[0], quads[1], quads[2], quads[3])))
    return Shape(layers=tuple(new_layers)).strip_top_empty_layers()


__all__ = [
    "infer_uniform_paint_color",
    "pure_fluid_color",
    "uniform_fluid_output_from_template",
]
