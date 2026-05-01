from __future__ import annotations

from html import escape

from shapez2_solver.domain.shape_pattern import (
    NormalizedShapeCell,
    NormalizedShapePattern,
    QuadrantPosition,
)

COLOR_HEX = {
    "u": "#f4f1ec",
    "r": "#ef4444",
    "g": "#22c55e",
    "b": "#3b82f6",
    "c": "#2ec4b6",
    "m": "#d946ef",
    "y": "#facc15",
    "w": "#ffffff",
    "-": "transparent",
}

STROKE = "#2b242c"
SHADOW = "#17121a"


def render_shape_pattern_svg(pattern: NormalizedShapePattern, size: int = 192) -> str:
    body: list[str] = [
        f'<svg class="shape-preview" width="{size}" height="{size}" '
        'viewBox="0 0 256 256" role="img" '
        f'aria-label="{escape(pattern.normalized_code)}" '
        'xmlns="http://www.w3.org/2000/svg">',
        f'<circle cx="128" cy="128" r="122" fill="{SHADOW}" opacity="0.95"/>',
    ]

    for layer in sorted(pattern.layers, key=lambda lyr: lyr.layer_index):
        scale = max(0.45, 1.0 - (layer.layer_index * 0.18))
        body.append(f'<g transform="translate(128 128) scale({scale:.2f}) translate(-128 -128)">')
        for cell in layer.cells:
            body.append(render_cell(cell))
        body.append("</g>")

    body.append(f'<circle cx="128" cy="128" r="6" fill="{STROKE}" opacity="0.85"/>')
    body.append("</svg>")
    return "".join(body)


def render_cell(cell: NormalizedShapeCell) -> str:
    if cell.shape_code == "-":
        return ""

    fill = COLOR_HEX.get(cell.color_code, "#ff00ff")

    if cell.shape_code == "R":
        path = rounded_rect_quadrant_path(cell.position)
        extra_attrs = ""
    elif cell.shape_code == "C":
        path = circle_quadrant_path(cell.position)
        extra_attrs = ""
    elif cell.shape_code == "S":
        path = spike_quadrant_path(cell.position)
        extra_attrs = ""
    elif cell.shape_code == "W":
        path = diamond_quadrant_path(cell.position)
        extra_attrs = ""
    elif cell.shape_code == "c":
        path = circle_quadrant_path(cell.position)
        extra_attrs = ' fill-opacity="0.86"'
    elif cell.shape_code == "P":
        return pin_svg(cell.position, fill)
    else:
        return ""

    return (
        f'<path d="{path}" fill="{fill}"{extra_attrs} stroke="{STROKE}" '
        'stroke-width="10" stroke-linejoin="round" stroke-linecap="round"/>'
    )


def rounded_rect_quadrant_path(position: QuadrantPosition) -> str:
    paths = {
        QuadrantPosition.NE: "M136 22 H224 Q234 22 234 32 V120 Q234 128 226 128 H136 Z",
        QuadrantPosition.SE: "M136 136 H226 Q234 136 234 144 V224 Q234 234 224 234 H136 Z",
        QuadrantPosition.SW: "M120 136 V234 H32 Q22 234 22 224 V144 Q22 136 30 136 Z",
        QuadrantPosition.NW: "M120 22 V128 H30 Q22 128 22 120 V32 Q22 22 32 22 Z",
    }
    return paths[position]


def circle_quadrant_path(position: QuadrantPosition) -> str:
    paths = {
        QuadrantPosition.NE: "M136 128 L136 54 Q202 56 202 120 Q202 128 194 128 Z",
        QuadrantPosition.SE: "M136 136 H194 Q202 136 202 144 Q200 202 136 202 Z",
        QuadrantPosition.SW: "M120 136 V202 Q56 200 54 144 Q54 136 62 136 Z",
        QuadrantPosition.NW: "M120 128 H62 Q54 128 54 120 Q56 56 120 54 Z",
    }
    return paths[position]


def spike_quadrant_path(position: QuadrantPosition) -> str:
    paths = {
        QuadrantPosition.NE: "M136 128 L178 82 L224 28 Q232 20 232 36 L178 118 Z",
        QuadrantPosition.SE: "M136 136 L178 138 L232 220 Q232 236 224 228 L178 174 Z",
        QuadrantPosition.SW: "M120 136 L78 174 L32 228 Q24 236 24 220 L78 138 Z",
        QuadrantPosition.NW: "M120 128 L78 118 L24 36 Q24 20 32 28 L78 82 Z",
    }
    return paths[position]


def diamond_quadrant_path(position: QuadrantPosition) -> str:
    paths = {
        QuadrantPosition.NE: "M136 128 L180 44 L232 128 Z",
        QuadrantPosition.SE: "M136 136 L232 136 L180 220 Z",
        QuadrantPosition.SW: "M120 136 L76 220 L24 136 Z",
        QuadrantPosition.NW: "M120 128 L24 128 L76 44 Z",
    }
    return paths[position]


def pin_svg(position: QuadrantPosition, fill: str) -> str:
    centers = {
        QuadrantPosition.NE: (176, 80),
        QuadrantPosition.SE: (176, 176),
        QuadrantPosition.SW: (80, 176),
        QuadrantPosition.NW: (80, 80),
    }
    cx, cy = centers[position]
    return (
        f'<circle cx="{cx}" cy="{cy}" r="28" fill="{fill}" '
        f'stroke="{STROKE}" stroke-width="10"/>'
    )
