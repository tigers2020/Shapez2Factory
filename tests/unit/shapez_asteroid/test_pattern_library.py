"""Sequence 2 — deterministic linear pattern library."""

from __future__ import annotations

from django_apps.shapez_asteroid.optimization.coords import Coord, cardinal_unit_toward
from django_apps.shapez_asteroid.optimization.enums import CardinalDirection
from django_apps.shapez_asteroid.optimization.pattern_dto import BundlePattern, Direction
from django_apps.shapez_asteroid.optimization.pattern_library import (
    build_linear_patterns,
    build_pattern_library,
    rotate_pattern,
)


def test_build_pattern_library_generates_linear_0_to_3_extensions() -> None:
    lib = build_pattern_library()
    assert len(lib) == 16
    by_ext: dict[int, list[BundlePattern]] = {}
    for p in lib:
        by_ext.setdefault(p.extension_count, []).append(p)
    for n in range(4):
        assert len(by_ext[n]) == 4


def test_pattern_ids_deterministic() -> None:
    a = tuple(p.pattern_id for p in build_pattern_library())
    b = tuple(p.pattern_id for p in build_pattern_library())
    assert a == b
    assert a[0] == "lin_n_len0"


def test_output_stub_not_occupied() -> None:
    for p in build_pattern_library():
        assert p.output_stub_offset not in p.occupied_offsets


def test_extractor_offset_unique_and_in_occupied() -> None:
    for p in build_pattern_library():
        assert p.extractor_offset == Coord(0, 0)
        assert sum(1 for c in p.occupied_offsets if c == p.extractor_offset) == 1


def test_extension_count_and_occupied_contents() -> None:
    for p in build_pattern_library():
        assert 0 <= p.extension_count <= 3
        assert len(p.occupied_offsets) == 1 + p.extension_count
        assert p.occupied_offsets == frozenset((p.extractor_offset, *p.extension_offsets))


def test_throughput_factor_mapping() -> None:
    for p in build_pattern_library():
        assert p.throughput_factor in {4, 8, 12, 16}
        assert p.throughput_factor == 4 * (1 + p.extension_count)


def test_canonical_east_patterns_exist() -> None:
    canon = build_linear_patterns()
    assert len(canon) == 4
    assert all(p.output_dir is CardinalDirection.EAST for p in canon)
    ids = [p.pattern_id for p in canon]
    assert ids == ["lin_e_len0", "lin_e_len1", "lin_e_len2", "lin_e_len3"]


def test_rotations_deterministic_on_server_grid() -> None:
    lib = build_pattern_library()
    for p in lib:
        for c in p.occupied_offsets:
            assert isinstance(c.x, int) and isinstance(c.y, int)
        assert isinstance(p.output_stub_offset.x, int)


def test_rotation_preserves_attachment_validity() -> None:
    for p in build_pattern_library():
        assert len(p.attachments) == p.extension_count
        for att in p.attachments:
            assert (
                cardinal_unit_toward(att.extension_offset, att.parent_offset) is att.required_facing
            )


def test_attachment_chain_deterministic() -> None:
    p = next(x for x in build_linear_patterns() if x.extension_count == 2)
    assert p.extension_offsets == (Coord(1, 0), Coord(2, 0))
    assert p.attachments[0].parent_offset == Coord(0, 0)
    assert p.attachments[1].parent_offset == Coord(1, 0)


def test_rotate_pattern_only_from_canonical_east() -> None:
    p = build_linear_patterns()[1]
    assert p.output_dir is CardinalDirection.EAST
    q = rotate_pattern(p, CardinalDirection.SOUTH)
    assert q.output_dir is CardinalDirection.SOUTH
    assert q.pattern_id == "lin_s_len1"


def test_direction_alias_matches_cardinal() -> None:
    assert Direction.EAST is CardinalDirection.EAST
