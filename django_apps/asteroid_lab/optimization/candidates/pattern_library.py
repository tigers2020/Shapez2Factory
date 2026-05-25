"""SYNTHETIC TEST-ONLY linear bundle patterns (lin_*).

Production RTTP uses ``adapters.catalog_candidate_placements.build_catalog_placement_specs``.
Do not call ``build_pattern_library()`` from ``candidate_generator`` or pipeline code.
"""

from __future__ import annotations

from django_apps.asteroid_lab.optimization.candidates.bundle_pattern import BundlePattern
from django_apps.asteroid_lab.optimization.coords import Coord

_DIRECTIONS: tuple[str, ...] = ("N", "E", "S", "W")
_DIR_LETTER: dict[str, str] = {"N": "n", "E": "e", "S": "s", "W": "w"}
_THROUGHPUT_BY_EXT: tuple[int, ...] = (4, 8, 12, 16)


def _rotation_matrix(direction: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """Row-major rotation mapping canonical +x chain to ``direction``."""

    if direction == "E":
        return ((1, 0), (0, 1))
    if direction == "N":
        return ((0, 1), (-1, 0))
    if direction == "S":
        return ((0, -1), (1, 0))
    if direction == "W":
        return ((-1, 0), (0, -1))
    msg = f"unsupported direction {direction!r}"
    raise ValueError(msg)


def _rotate_point(direction: str, point: Coord) -> Coord:
    (a11, a12), (a21, a22) = _rotation_matrix(direction)
    return (a11 * point[0] + a12 * point[1], a21 * point[0] + a22 * point[1])


def _pattern_id(direction: str, extension_count: int) -> str:
    return f"lin_{_DIR_LETTER[direction]}_len{extension_count}"


def _throughput_factor(extension_count: int) -> int:
    if extension_count < 0 or extension_count > 3:
        msg = "extension_count must be in 0..3"
        raise ValueError(msg)
    return _THROUGHPUT_BY_EXT[extension_count]


def _linear_chain_offsets_east(extension_count: int) -> tuple[Coord, ...]:
    return tuple((index + 1, 0) for index in range(extension_count))


def _canonical_linear_east(extension_count: int) -> BundlePattern:
    extractor = (0, 0)
    extension_offsets = _linear_chain_offsets_east(extension_count)
    occupied = frozenset((extractor, *extension_offsets))
    fixed_output_transport_offset = (1, 0)
    if extension_count == 0:
        occupied = frozenset({extractor})
        output_stub_offset = (2, 0)
    else:
        last = extension_offsets[-1]
        output_stub_offset = (last[0] + 1, last[1])
    if output_stub_offset in occupied:
        raise AssertionError("output_stub must not overlap occupied_offsets")
    return BundlePattern(
        pattern_id=_pattern_id("E", extension_count),
        extension_count=extension_count,
        occupied_offsets=occupied,
        extractor_offset=extractor,
        extension_offsets=extension_offsets,
        output_dir="E",
        fixed_output_transport_offset=fixed_output_transport_offset,
        output_stub_offset=output_stub_offset,
        throughput_factor=_throughput_factor(extension_count),
        topology_kind="linear",
    )


def _rotate_pattern(pattern: BundlePattern, direction: str) -> BundlePattern:
    if pattern.output_dir != "E":
        msg = "rotate_pattern only accepts canonical EAST patterns"
        raise ValueError(msg)
    if direction == "E":
        return pattern
    if pattern.extractor_offset != (0, 0):
        msg = "canonical pattern extractor_offset must be (0, 0)"
        raise ValueError(msg)

    extension_offsets = tuple(
        _rotate_point(direction, offset) for offset in pattern.extension_offsets
    )
    stub = _rotate_point(direction, pattern.output_stub_offset)
    fot = _rotate_point(direction, pattern.fixed_output_transport_offset)
    occupied = frozenset(_rotate_point(direction, offset) for offset in pattern.occupied_offsets)
    if stub in occupied:
        raise AssertionError("rotated output_stub must not overlap occupied_offsets")
    return BundlePattern(
        pattern_id=_pattern_id(direction, pattern.extension_count),
        extension_count=pattern.extension_count,
        occupied_offsets=occupied,
        extractor_offset=pattern.extractor_offset,
        extension_offsets=extension_offsets,
        output_dir=direction,
        fixed_output_transport_offset=fot,
        output_stub_offset=stub,
        throughput_factor=pattern.throughput_factor,
        topology_kind=pattern.topology_kind,
    )


def build_pattern_library() -> tuple[BundlePattern, ...]:
    """All linear 0..3 extension patterns × four rotations (deterministic order)."""

    patterns: list[BundlePattern] = []
    for extension_count in range(4):
        canonical = _canonical_linear_east(extension_count)
        for direction in _DIRECTIONS:
            patterns.append(_rotate_pattern(canonical, direction))
    return tuple(patterns)


__all__ = ["BundlePattern", "build_pattern_library"]
