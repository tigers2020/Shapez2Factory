"""Pass2-A internal fill: inner-first sweep, ``try_commit_pass2_bundle`` only."""

from __future__ import annotations

from functools import wraps
from unittest.mock import patch

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.boundary import (
    cells_touching_void,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass2_internal_placement as p2,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass2_internal_placement import (  # noqa: E501
    mineable_inner_first_order,
    run_pass2_internal_placement_mvp,
    try_place_pass2_internal_bundle,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_bundle_commit import (  # noqa: E501
    Pass12LayoutScratch,
    try_commit_pass2_bundle,
)


def test_mineable_inner_first_partition_matches_complement() -> None:
    """Order is sorted inner, then sorted perimeter (mineable ∩ touching_void)."""

    ast = frozenset(
        {
            (-2, -1),
            (-2, 0),
            (-2, 1),
            (-1, -1),
            (-1, 0),
            (-1, 1),
            (1, -1),
            (1, 0),
            (1, 1),
            (2, -1),
            (2, 0),
            (2, 1),
        }
    )
    mine = ast
    ordered = mineable_inner_first_order(mine, ast)
    perimeter = mine & frozenset(cells_touching_void(set(ast)))
    inner = mine - perimeter
    k = len(inner)
    assert ordered[:k] == tuple(sorted(inner, key=lambda c: (c[0], c[1])))
    assert ordered[k:] == tuple(sorted(perimeter, key=lambda c: (c[0], c[1])))
    assert set(ordered) == mine


def test_pass2_places_when_free_cell_exists() -> None:
    asteroid = frozenset({(-1, 0), (1, 0)})
    mineable = asteroid
    scratch = Pass12LayoutScratch()
    is_ext = lambda c: c not in asteroid  # noqa: E731

    n = run_pass2_internal_placement_mvp(
        mineable_cells=mineable,
        asteroid_cells=asteroid,
        scratch=scratch,
        is_external=is_ext,
    )
    assert n >= 1
    assert scratch.extractor_cells
    assert scratch.transport_cells


def test_try_commit_pass2_bundle_is_invoked_not_bypassed() -> None:
    asteroid = frozenset({(-1, 0), (1, 0)})
    mineable = asteroid
    scratch = Pass12LayoutScratch()
    is_ext = lambda c: c not in asteroid  # noqa: E731

    commit_calls: list[int] = []

    @wraps(try_commit_pass2_bundle)
    def wrapped(*args, **kwargs):  # type: ignore[no-untyped-def]
        commit_calls.append(1)
        return try_commit_pass2_bundle(*args, **kwargs)

    with patch.object(p2, "try_commit_pass2_bundle", wrapped):
        run_pass2_internal_placement_mvp(
            mineable_cells=mineable,
            asteroid_cells=asteroid,
            scratch=scratch,
            is_external=is_ext,
        )
    assert sum(commit_calls) >= 1


def test_pass2_route_impossible_leaves_no_residue() -> None:
    asteroid = frozenset({(-1, 0)})
    mineable = asteroid
    scratch = Pass12LayoutScratch()
    is_ext = lambda c: c[0] >= 50  # noqa: E731

    before_t, before_b = set(scratch.transport_cells), set(scratch.blocked_cells)
    n = run_pass2_internal_placement_mvp(
        mineable_cells=mineable,
        asteroid_cells=asteroid,
        scratch=scratch,
        is_external=is_ext,
    )
    assert n == 0
    assert scratch.transport_cells == before_t
    assert scratch.blocked_cells == before_b
    assert scratch.extractor_cells == set()
    assert scratch.extension_facings == {}
    assert scratch.extractor_output_dirs == {}


def test_pass2_skips_pass1_extractor_body() -> None:
    scratch = Pass12LayoutScratch()
    scratch.blocked_cells = {(-1, 0)}
    scratch.extractor_cells = {(-1, 0)}
    scratch.transport_cells = {(1, 0)}
    scratch.extractor_output_dirs = {(-1, 0): (1, 0)}
    mineable = frozenset({(-1, 0), (2, 0)})
    asteroid = mineable
    is_ext = lambda c: c not in mineable  # noqa: E731

    n = run_pass2_internal_placement_mvp(
        mineable_cells=mineable,
        asteroid_cells=asteroid,
        scratch=scratch,
        is_external=is_ext,
    )
    assert n == 1
    assert (-1, 0) in scratch.extractor_cells
    assert (2, 0) in scratch.extractor_cells


def test_pass2_skips_pass1_extension_cell() -> None:
    scratch = Pass12LayoutScratch()
    scratch.blocked_cells = {(-1, 0), (1, 0)}
    scratch.extractor_cells = {(-1, 0)}
    scratch.transport_cells = {(2, 0)}
    scratch.extractor_output_dirs = {(-1, 0): (1, 0)}
    scratch.extension_facings = {(1, 0): (-1, 0)}
    mineable = frozenset({(-1, 0), (1, 0), (-1, 1)})
    asteroid = frozenset({(-1, 0), (1, 0), (2, 0), (-1, 1), (-2, 0)})
    is_ext = lambda c: c not in asteroid  # noqa: E731

    n = run_pass2_internal_placement_mvp(
        mineable_cells=mineable,
        asteroid_cells=asteroid,
        scratch=scratch,
        is_external=is_ext,
    )
    assert n >= 1
    assert (1, 0) not in scratch.extractor_cells


def test_pass2_skips_committed_transport_stub_slot() -> None:
    scratch = Pass12LayoutScratch()
    scratch.transport_cells = {(1, 0)}
    mineable = frozenset({(1, 0), (-1, 0)})
    asteroid = mineable
    is_ext = lambda c: c not in asteroid  # noqa: E731

    n = run_pass2_internal_placement_mvp(
        mineable_cells=mineable,
        asteroid_cells=asteroid,
        scratch=scratch,
        is_external=is_ext,
    )
    assert n == 1
    assert (-1, 0) in scratch.extractor_cells


def test_pass2_respects_hard_barrier_cells() -> None:
    scratch = Pass12LayoutScratch()
    mineable = frozenset({(-1, 0), (1, 0)})
    asteroid = mineable
    is_ext = lambda c: c not in asteroid  # noqa: E731
    barriers = frozenset({(-1, 0)})

    n = run_pass2_internal_placement_mvp(
        mineable_cells=mineable,
        asteroid_cells=asteroid,
        scratch=scratch,
        is_external=is_ext,
        hard_barrier_cells=barriers,
    )
    assert n == 1
    assert (-1, 0) not in scratch.extractor_cells
    assert (1, 0) in scratch.extractor_cells


def _square_asteroid_with_inner_and_perimeter() -> frozenset[tuple[int, int]]:
    """Blueprint 격자(x=0 제외) 6x5 사각형 — inner 12셀, perimeter 18셀.

    inner: x ∈ {-2,-1,1,2}, |y| ≤ 1, perimeter: 외곽.
    """

    return frozenset((x, y) for x in (-3, -2, -1, 1, 2, 3) for y in (-2, -1, 0, 1, 2))


def test_mineable_inner_first_priority_seeds_none_matches_baseline() -> None:
    """``priority_seeds=None`` / ``frozenset()``는 기본 호출과 byte-equal (OFF identity)."""

    asteroid = _square_asteroid_with_inner_and_perimeter()
    mineable = asteroid
    baseline = mineable_inner_first_order(mineable, asteroid)
    assert mineable_inner_first_order(mineable, asteroid, priority_seeds=None) == baseline
    assert mineable_inner_first_order(mineable, asteroid, priority_seeds=frozenset()) == baseline


def test_mineable_inner_first_priority_seeds_promotes_within_groups() -> None:
    """ON soft priority: 시드 인접 셀이 그룹 선두로 이동, inner > perimeter 보전."""

    asteroid = _square_asteroid_with_inner_and_perimeter()
    mineable = asteroid
    seeds = frozenset({(2, 0)})
    ordered = mineable_inner_first_order(mineable, asteroid, priority_seeds=seeds)

    perimeter = mineable & frozenset(cells_touching_void(set(asteroid)))
    inner = mineable - perimeter
    inner_part = ordered[: len(inner)]
    perim_part = ordered[len(inner) :]

    assert set(inner_part) == inner
    assert set(perim_part) == perimeter

    expected_inner_priority = {(1, 0), (2, -1), (2, 1)}
    assert set(inner_part[: len(expected_inner_priority)]) == expected_inner_priority
    assert inner_part[: len(expected_inner_priority)] == tuple(
        sorted(expected_inner_priority, key=lambda c: (c[0], c[1]))
    )

    assert (3, 0) in perim_part
    assert perim_part[0] == (3, 0)


def test_mineable_inner_first_priority_seeds_deterministic() -> None:
    """ON 결정론: 같은 입력 두 번 호출 시 결과 동일."""

    asteroid = _square_asteroid_with_inner_and_perimeter()
    seeds = frozenset({(2, 0), (-2, 0)})
    a = mineable_inner_first_order(asteroid, asteroid, priority_seeds=seeds)
    b = mineable_inner_first_order(asteroid, asteroid, priority_seeds=seeds)
    assert a == b


def test_run_pass2_internal_placement_priority_seeds_arg_is_optional() -> None:
    """Runner는 ``priority_seeds`` 미지정 시 기존 호출과 동일한 결과를 낸다."""

    asteroid = frozenset({(-1, 0), (1, 0)})
    mineable = asteroid
    is_ext = lambda c: c not in asteroid  # noqa: E731

    s_default = Pass12LayoutScratch()
    n_default = run_pass2_internal_placement_mvp(
        mineable_cells=mineable, asteroid_cells=asteroid, scratch=s_default, is_external=is_ext
    )

    s_explicit = Pass12LayoutScratch()
    n_explicit = run_pass2_internal_placement_mvp(
        mineable_cells=mineable,
        asteroid_cells=asteroid,
        scratch=s_explicit,
        is_external=is_ext,
        priority_seeds=None,
    )
    assert n_default == n_explicit
    assert s_default.extractor_cells == s_explicit.extractor_cells
    assert s_default.transport_cells == s_explicit.transport_cells


def test_try_place_pass2_stub_blocked_skips_direction() -> None:
    """When every cardinal stub slot is blocked, placement fails without partial commit."""

    scratch = Pass12LayoutScratch()
    scratch.transport_cells = {(1, 0), (-2, 0), (-1, -1), (-1, 1)}
    mineable = frozenset({(-1, 0)})
    is_ext = lambda c: True  # noqa: E731

    assert not try_place_pass2_internal_bundle(
        extractor_cell=(-1, 0),
        mineable_cells=mineable,
        scratch=scratch,
        is_external=is_ext,
        hard_barrier_cells=frozenset(),
    )
    assert scratch.extractor_cells == set()
