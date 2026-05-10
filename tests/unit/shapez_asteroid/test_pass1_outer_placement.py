"""Canonical P1-A: outer-first Pass1 placement MVP uses ``try_commit_pass1_bundle`` only."""

from __future__ import annotations

from functools import wraps
from unittest.mock import patch

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.boundary import (
    cells_touching_void,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass1_outer_placement as p1,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass1_outer_placement import (  # noqa: E501
    mineable_outer_first_order,
    run_pass1_outer_placement_mvp,
    try_place_pass1_outer_bundle,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_bundle_commit import (  # noqa: E501
    Pass12LayoutScratch,
    try_commit_pass1_bundle,
)


def test_mineable_outer_first_partition_matches_void_touch() -> None:
    """Order is sorted perimeter (mineable ∩ touching_void) then sorted inner."""

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
    ordered = mineable_outer_first_order(mine, ast)
    perimeter = mine & frozenset(cells_touching_void(set(ast)))
    inner = mine - perimeter
    k = len(perimeter)
    assert ordered[:k] == tuple(sorted(perimeter, key=lambda c: (c[0], c[1])))
    assert ordered[k:] == tuple(sorted(inner, key=lambda c: (c[0], c[1])))
    assert set(ordered) == mine


def test_pass1_places_at_least_one_outer_on_simple_map() -> None:
    asteroid = frozenset({(-1, 0), (1, 0)})
    mineable = asteroid
    scratch = Pass12LayoutScratch()
    is_ext = lambda c: c not in asteroid  # noqa: E731

    n = run_pass1_outer_placement_mvp(
        mineable_cells=mineable,
        asteroid_cells=asteroid,
        scratch=scratch,
        is_external=is_ext,
    )
    assert n >= 1
    assert len(scratch.blocked_cells) >= 1
    assert scratch.transport_cells


def test_route_impossible_leaves_no_residue() -> None:
    asteroid = frozenset({(-1, 0)})
    mineable = asteroid
    scratch = Pass12LayoutScratch()
    is_ext = lambda c: c[0] >= 50  # noqa: E731

    before_t, before_b = set(scratch.transport_cells), set(scratch.blocked_cells)
    n = run_pass1_outer_placement_mvp(
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


def test_try_commit_pass1_bundle_is_invoked_not_bypassed() -> None:
    asteroid = frozenset({(-1, 0), (1, 0)})
    mineable = asteroid
    scratch = Pass12LayoutScratch()
    is_ext = lambda c: c not in asteroid  # noqa: E731

    commit_calls: list[int] = []

    @wraps(try_commit_pass1_bundle)
    def wrapped(*args, **kwargs):  # type: ignore[no-untyped-def]
        commit_calls.append(1)
        return try_commit_pass1_bundle(*args, **kwargs)

    with patch.object(p1, "try_commit_pass1_bundle", wrapped):
        run_pass1_outer_placement_mvp(
            mineable_cells=mineable,
            asteroid_cells=asteroid,
            scratch=scratch,
            is_external=is_ext,
        )
    assert sum(commit_calls) >= 1


def test_p1_commit_via_cheap_escape_adds_only_stub_transport() -> None:
    mineable = frozenset({(-1, 0)})
    scratch = Pass12LayoutScratch()
    # Envelope margin is ~3..7 tiles; external must lie inside cheap void for this map.
    is_ext = lambda c: c[0] >= 2  # noqa: E731
    assert try_place_pass1_outer_bundle(
        extractor_cell=(-1, 0),
        mineable_cells=mineable,
        asteroid_cells=mineable,
        scratch=scratch,
        is_external=is_ext,
    )
    assert scratch.transport_cells == {(1, 0)}
    assert scratch.extractor_output_dirs


def test_cheap_escape_unreachable_still_no_residue() -> None:
    mineable = frozenset({(-1, 0)})
    asteroid = mineable
    scratch = Pass12LayoutScratch()
    is_ext = lambda c: False  # noqa: E731
    assert not try_place_pass1_outer_bundle(
        extractor_cell=(-1, 0),
        mineable_cells=mineable,
        asteroid_cells=asteroid,
        scratch=scratch,
        is_external=is_ext,
    )
    assert scratch.transport_cells == set()
    assert scratch.blocked_cells == set()
    assert scratch.extractor_output_dirs == {}


def test_dead_end_emits_bundle_reject_no_route() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
        trace_run_scope,
    )

    rejected: list[str] = []

    def capture_event(location: str, message: str, data: dict | None = None) -> None:
        if message == "bundle_reject_no_route":
            rejected.append(location)

    asteroid = frozenset({(-1, 0)})
    mineable = asteroid
    scratch = Pass12LayoutScratch()
    is_ext = lambda c: c[0] >= 50  # noqa: E731

    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace.trace_event",
        capture_event,
    ):
        with patch(
            "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace.trace_enabled",
            return_value=True,
        ):
            with trace_run_scope():
                run_pass1_outer_placement_mvp(
                    mineable_cells=mineable,
                    asteroid_cells=asteroid,
                    scratch=scratch,
                    is_external=is_ext,
                )
    assert rejected
    assert all(x.endswith("try_commit_pass1_bundle") for x in rejected)
