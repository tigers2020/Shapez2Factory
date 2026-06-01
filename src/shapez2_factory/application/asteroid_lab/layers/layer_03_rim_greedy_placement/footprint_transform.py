"""Full-footprint D4 transform contract (spec §T / Amendment 6).

A direction/mirror variant is a **rigid transform of the entire miner-relative
footprint**, never an orientation-only mutation. Every equipment item's local
coordinate ``(dx, dy)`` AND building rotation ``R`` are rotated/reflected together
(T1). Mirror is a *separate* transform from rotation (T3): for asymmetric layouts a
mirror is geometrically distinct from every rotation, while symmetric layouts collapse
after full normalization.

Solver frame is **y-down** (+x East, +y South); the canonical base orientation is East
(``R = 0``). Rotation ``k`` counts clockwise quarter-turns.
"""

from __future__ import annotations

from dataclasses import dataclass

Coord = tuple[int, int]
# A transformed equipment cell: (dx, dy, R) relative to the miner anchor.
Cell = tuple[int, int, int]

# Mirror's effect on building rotation R (0=E, 1=S, 2=W, 3=N in the y-down frame).
_MIRROR_R_X: dict[int, int] = {0: 2, 1: 1, 2: 0, 3: 3}  # vertical axis: E<->W
_MIRROR_R_Y: dict[int, int] = {0: 0, 1: 3, 2: 2, 3: 1}  # horizontal axis: N<->S


def rotate_xy(dx: int, dy: int, k: int) -> Coord:
    """Rotate a local ``(dx, dy)`` offset by ``k`` clockwise quarter-turns (y-down)."""

    k %= 4
    if k == 0:
        return (dx, dy)
    if k == 1:
        return (-dy, dx)
    if k == 2:
        return (-dx, -dy)
    return (dy, -dx)


def rotate_r(r: int, k: int) -> int:
    """Rotate a building rotation ``R`` by ``k`` clockwise quarter-turns."""

    return (r + k) % 4


def mirror_xy(dx: int, dy: int, axis: str) -> Coord:
    """Reflect ``(dx, dy)`` across ``axis`` (``"x"`` = vertical axis, ``"y"`` = horizontal axis)."""

    if axis == "x":
        return (-dx, dy)
    if axis == "y":
        return (dx, -dy)
    msg = f"unknown mirror axis: {axis!r}"
    raise ValueError(msg)


def mirror_r(r: int, axis: str) -> int:
    """Reflect a building rotation ``R`` across ``axis``."""

    if axis == "x":
        return _MIRROR_R_X[r % 4]
    if axis == "y":
        return _MIRROR_R_Y[r % 4]
    msg = f"unknown mirror axis: {axis!r}"
    raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class FootprintVariant:
    """One D4 variant of a gene footprint (canonical base ``R = 0``).

    ``orientation_k`` is the rotation component (0..3); ``mirrored`` marks whether the
    vertical-axis mirror generator was applied before rotation. ``extractor_cell`` and
    ``extension_cells`` are the transformed ``(dx, dy, R)`` cells relative to the miner
    anchor (extractor stays at the origin).
    """

    orientation_k: int
    mirrored: bool
    extractor_cell: Cell
    extension_cells: tuple[Cell, ...]

    @property
    def normalized_key(self) -> frozenset[Cell]:
        """Geometry+rotation identity used to deduplicate variants (T3)."""

        return frozenset((self.extractor_cell, *self.extension_cells))


def _transform_cell(dx: int, dy: int, r: int, *, mirrored: bool, k: int) -> Cell:
    if mirrored:
        dx, dy = mirror_xy(dx, dy, "x")
        r = mirror_r(r, "x")
    rx, ry = rotate_xy(dx, dy, k)
    return (rx, ry, rotate_r(r, k))


def enumerate_d4(
    *,
    extractor_offset: Coord,
    extension_offsets: tuple[Coord, ...],
    base_r: int = 0,
) -> tuple[FootprintVariant, ...]:
    """Enumerate the D4 variants of a footprint, deduplicated after normalization (T1/T3/T6).

    Generators are ``{identity, mirror_x} × {rotation 0..3}`` (8 candidates). Variants
    that share the same normalized ``(dx, dy, R)`` cell set (e.g. mirror == 180° for a
    symmetric layout) are collapsed; the first in the deterministic ``(mirrored,
    orientation_k)`` order is kept. Asymmetric/corner layouts keep all 8.
    """

    seen: set[frozenset[Cell]] = set()
    variants: list[FootprintVariant] = []
    for mirrored in (False, True):
        for k in (0, 1, 2, 3):
            extractor_cell = _transform_cell(
                extractor_offset[0], extractor_offset[1], base_r, mirrored=mirrored, k=k
            )
            extension_cells = tuple(
                sorted(
                    _transform_cell(ox, oy, base_r, mirrored=mirrored, k=k)
                    for ox, oy in extension_offsets
                )
            )
            variant = FootprintVariant(
                orientation_k=k,
                mirrored=mirrored,
                extractor_cell=extractor_cell,
                extension_cells=extension_cells,
            )
            if variant.normalized_key in seen:
                continue
            seen.add(variant.normalized_key)
            variants.append(variant)
    return tuple(variants)


__all__ = [
    "Cell",
    "Coord",
    "FootprintVariant",
    "enumerate_d4",
    "mirror_r",
    "mirror_xy",
    "rotate_r",
    "rotate_xy",
]
