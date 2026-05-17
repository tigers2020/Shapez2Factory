"""Deterministic linear bundle pattern compiler (Phase 2, local only)."""

from __future__ import annotations

from django_apps.shapez_asteroid.optimization.coords import Coord, cardinal_unit_toward
from django_apps.shapez_asteroid.optimization.enums import CardinalDirection
from django_apps.shapez_asteroid.optimization.pattern_dto import (
    BundlePattern,
    Direction,
    ExtensionAttachment,
)

_THROUGHPUT_BY_EXT: tuple[int, ...] = (4, 8, 12, 16)

_DIR_LETTER: dict[CardinalDirection, str] = {
    CardinalDirection.NORTH: "n",
    CardinalDirection.EAST: "e",
    CardinalDirection.SOUTH: "s",
    CardinalDirection.WEST: "w",
}


def _mat(d: CardinalDirection) -> tuple[tuple[int, int], tuple[int, int]]:
    """Row-major: x' = a11*x + a12*y, y' = a21*x + a22*y (maps canonical +x chain to ``d``)."""

    if d is CardinalDirection.EAST:
        return ((1, 0), (0, 1))
    if d is CardinalDirection.NORTH:
        return ((0, 1), (-1, 0))
    if d is CardinalDirection.SOUTH:
        return ((0, -1), (1, 0))
    if d is CardinalDirection.WEST:
        return ((-1, 0), (0, -1))
    raise ValueError(f"unsupported direction {d!r}")


def _apply_rot_from_east(d: CardinalDirection, p: Coord) -> Coord:
    (a11, a12), (a21, a22) = _mat(d)
    return Coord(a11 * p.x + a12 * p.y, a21 * p.x + a22 * p.y)


def _pattern_id(d: CardinalDirection, extension_count: int) -> str:
    return f"lin_{_DIR_LETTER[d]}_len{extension_count}"


def _throughput_factor(extension_count: int) -> int:
    if extension_count < 0 or extension_count > 3:
        raise ValueError("extension_count must be in 0..3")
    return _THROUGHPUT_BY_EXT[extension_count]


def _linear_chain_offsets_east(extension_count: int) -> tuple[Coord, ...]:
    return tuple(Coord(i + 1, 0) for i in range(extension_count))


def build_linear_patterns() -> tuple[BundlePattern, ...]:
    """Canonical EAST-only linear patterns (extension_count 0..3)."""

    out: list[BundlePattern] = []
    for n in range(4):
        out.append(_canonical_linear_east(n))
    return tuple(out)


def _canonical_linear_east(extension_count: int) -> BundlePattern:
    ex = Coord(0, 0)
    ext_offsets = _linear_chain_offsets_east(extension_count)
    occupied = frozenset((ex, *ext_offsets))
    last = ext_offsets[-1] if ext_offsets else ex
    stub = Coord(last.x + 1, last.y)
    if stub in occupied:
        raise AssertionError("output_stub must not overlap occupied_offsets")
    attachments = _attachments_linear_east(ex, ext_offsets)
    return BundlePattern(
        pattern_id=_pattern_id(CardinalDirection.EAST, extension_count),
        extension_count=extension_count,
        occupied_offsets=occupied,
        extractor_offset=ex,
        extension_offsets=ext_offsets,
        attachments=attachments,
        output_dir=CardinalDirection.EAST,
        output_stub_offset=stub,
        throughput_factor=_throughput_factor(extension_count),
        topology_kind="linear",
    )


def _attachments_linear_east(
    extractor: Coord, extension_offsets: tuple[Coord, ...]
) -> tuple[ExtensionAttachment, ...]:
    at: list[ExtensionAttachment] = []
    for i, ext in enumerate(extension_offsets):
        parent = extractor if i == 0 else extension_offsets[i - 1]
        facing = cardinal_unit_toward(ext, parent)
        at.append(
            ExtensionAttachment(
                extension_offset=ext,
                parent_offset=parent,
                required_facing=facing,
            )
        )
    return tuple(at)


def rotate_pattern(pattern: BundlePattern, output_dir: Direction) -> BundlePattern:
    """Rotate a canonical EAST pattern to ``output_dir`` (offsets + stub + attachments)."""

    if pattern.output_dir is not CardinalDirection.EAST:
        raise ValueError(
            "rotate_pattern only accepts canonical EAST patterns from build_linear_patterns"
        )
    if output_dir is CardinalDirection.EAST:
        return pattern
    ex = pattern.extractor_offset
    if ex != Coord(0, 0):
        raise ValueError("canonical pattern extractor_offset must be (0,0)")
    ext_offsets = tuple(_apply_rot_from_east(output_dir, p) for p in pattern.extension_offsets)
    stub = _apply_rot_from_east(output_dir, pattern.output_stub_offset)
    occupied = frozenset(_apply_rot_from_east(output_dir, p) for p in pattern.occupied_offsets)
    if stub in occupied:
        raise AssertionError("rotated output_stub must not overlap occupied_offsets")
    attachments = _attachments_linear_east(ex, ext_offsets)
    for att in attachments:
        if cardinal_unit_toward(att.extension_offset, att.parent_offset) is not att.required_facing:
            raise AssertionError("attachment facing must match cardinal_unit_toward after rotation")
    return BundlePattern(
        pattern_id=_pattern_id(output_dir, pattern.extension_count),
        extension_count=pattern.extension_count,
        occupied_offsets=occupied,
        extractor_offset=ex,
        extension_offsets=ext_offsets,
        attachments=attachments,
        output_dir=output_dir,
        output_stub_offset=stub,
        throughput_factor=pattern.throughput_factor,
        topology_kind=pattern.topology_kind,
    )


def build_pattern_library() -> tuple[BundlePattern, ...]:
    """All linear 0..3 extension patterns × four rotations (deterministic order)."""

    canon = build_linear_patterns()
    out: list[BundlePattern] = []
    order_dirs = (
        CardinalDirection.NORTH,
        CardinalDirection.EAST,
        CardinalDirection.SOUTH,
        CardinalDirection.WEST,
    )
    for p in canon:
        for d in order_dirs:
            out.append(rotate_pattern(p, d))
    return tuple(out)
