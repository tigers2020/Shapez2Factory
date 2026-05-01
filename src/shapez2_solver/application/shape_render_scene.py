from __future__ import annotations

from dataclasses import dataclass

from shapez2_solver.domain.shape_pattern import NormalizedShapePattern, QuadrantPosition

SHAPE_MESH_KEYS = {
    "R": "default_rect",
    "C": "default_circle",
    "S": "default_star",
    "W": "default_diamond",
    "P": "default_pin",
    "c": "default_crystal",
}


@dataclass(frozen=True, slots=True)
class ShapeRenderCell:
    layer_index: int
    quadrant_index: int
    position: QuadrantPosition
    shape_code: str
    color_code: str
    shape_kind: str
    color_kind: str
    mesh_key: str
    material_key: str
    transform_key: str


@dataclass(frozen=True, slots=True)
class ShapeRenderScene:
    normalized_code: str
    cells: tuple[ShapeRenderCell, ...]


def build_shape_render_scene(pattern: NormalizedShapePattern) -> ShapeRenderScene:
    cells: list[ShapeRenderCell] = []

    for layer in pattern.layers:
        for cell in layer.cells:
            if cell.shape_code == "-":
                continue

            cells.append(
                ShapeRenderCell(
                    layer_index=layer.layer_index,
                    quadrant_index=cell.quadrant_index,
                    position=cell.position,
                    shape_code=cell.shape_code,
                    color_code=cell.color_code,
                    shape_kind=cell.shape_kind,
                    color_kind=cell.color_kind,
                    mesh_key=SHAPE_MESH_KEYS.get(cell.shape_code, "unknown"),
                    material_key=cell.color_code,
                    transform_key=_transform_key(cell.position, layer.layer_index),
                )
            )

    return ShapeRenderScene(normalized_code=pattern.normalized_code, cells=tuple(cells))


def _transform_key(position: QuadrantPosition, layer_index: int) -> str:
    return f"{position.value}:L{layer_index}"
