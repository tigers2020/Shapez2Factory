"""Crystal generator fill, adjacency, cluster discovery, and shatter helpers.

Rules align with ``documents/game_rules/crystal_mechanics.md``. Adjacency used for
cluster/shatter is a solver approximation until fully verified against the game.
"""

from __future__ import annotations

from collections import deque

from django_apps.shapez_core.domain.shape import EMPTY_PART, Shape, ShapeLayer, ShapePart
from django_apps.shapez_core.domain.shape_catalog import COLOR_KINDS

type LayerQuad = tuple[int, int]


def highest_used_layer_index(shape: Shape) -> int:
    """Top layer index that still has any non-empty quadrant."""

    for i in range(len(shape.layers) - 1, -1, -1):
        if not shape.layers[i].is_empty():
            return i
    return 0


def crystal_fill_gaps_and_pins(shape: Shape, color_code: str) -> Shape:
    """Fill empty quadrants and pins with crystal (``kind='c'``) up to highest used layer."""

    _validate_paint_color(color_code)
    crystal_part = ShapePart(kind="c", color=color_code, material="crystal")
    max_z = highest_used_layer_index(shape)
    new_layers: list[ShapeLayer] = []
    for z, layer in enumerate(shape.layers):
        if z > max_z:
            new_layers.append(layer)
            continue
        quads: list[ShapePart] = []
        for part in layer.quadrants:
            if part.is_empty or part.is_pin:
                quads.append(crystal_part)
            else:
                quads.append(part)
        new_layers.append(ShapeLayer(quadrants=(quads[0], quads[1], quads[2], quads[3])))
    return Shape(layers=tuple(new_layers)).strip_top_empty_layers()


def _validate_paint_color(color_code: str) -> None:
    kind = COLOR_KINDS.get(color_code)
    if kind is None or kind.empty:
        raise ValueError(f"invalid crystal color code {color_code!r}")


def iter_adjacent_layer_quads(shape: Shape, layer_z: int, quad_index: int) -> list[LayerQuad]:
    """Neighbors for cluster BFS: same-layer perimeter + same quad above/below."""

    out: list[LayerQuad] = []
    out.append((layer_z, (quad_index - 1) % 4))
    out.append((layer_z, (quad_index + 1) % 4))
    if layer_z > 0:
        out.append((layer_z - 1, quad_index))
    if layer_z + 1 < len(shape.layers):
        out.append((layer_z + 1, quad_index))
    return out


def _crystal_bfs_candidate(
    shape: Shape, seen: set[LayerQuad], nz: int, nq: int
) -> LayerQuad | None:
    """Return ``(nz, nq)`` if it is an unseen in-bounds crystal cell, else ``None``."""

    if (nz, nq) in seen:
        return None
    if not (0 <= nz < len(shape.layers) and 0 <= nq < 4):
        return None
    if not shape.layers[nz].quadrants[nq].is_crystal:
        return None
    return (nz, nq)


def connected_crystal_cluster(shape: Shape, start_z: int, start_q: int) -> frozenset[LayerQuad]:
    """BFS over crystal cells using :func:`iter_adjacent_layer_quads`."""

    if not (0 <= start_z < len(shape.layers) and 0 <= start_q < 4):
        return frozenset()
    root = shape.layers[start_z].quadrants[start_q]
    if not root.is_crystal:
        return frozenset()

    seen: set[LayerQuad] = {(start_z, start_q)}
    dq: deque[LayerQuad] = deque([(start_z, start_q)])
    while dq:
        z, q = dq.popleft()
        for nz, nq in iter_adjacent_layer_quads(shape, z, q):
            nxt = _crystal_bfs_candidate(shape, seen, nz, nq)
            if nxt is None:
                continue
            seen.add(nxt)
            dq.append(nxt)
    return frozenset(seen)


def shatter_crystal_cluster(shape: Shape, cluster: frozenset[LayerQuad]) -> Shape:
    """Replace every cell in ``cluster`` with empty quadrants."""

    if not cluster:
        return shape
    mutable: list[list[ShapePart]] = [list(layer.quadrants) for layer in shape.layers]
    for z, q in cluster:
        mutable[z][q] = EMPTY_PART
    return Shape(
        layers=tuple(
            ShapeLayer(quadrants=(layer[0], layer[1], layer[2], layer[3])) for layer in mutable
        )
    ).strip_top_empty_layers()


def shatter_at_touch(shape: Shape, touch_z: int, touch_q: int) -> Shape:
    """Remove the crystal cluster containing ``(touch_z, touch_q)`` if it is crystal."""

    cluster = connected_crystal_cluster(shape, touch_z, touch_q)
    return shatter_crystal_cluster(shape, cluster)
