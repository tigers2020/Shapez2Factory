"""Canonical P1-B: extension topology enumeration (pure generator)."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.extension_topology import (  # noqa: E501
    enumerate_extension_topologies,
    rotation_r_for_extension_facing_parent,
)


def test_no_extension_on_output_stub_cell() -> None:
    extractor = (-1, 0)
    output_east = (1, 0)
    stub = (1, 0)
    mineable = frozenset(
        {
            extractor,
            stub,
            (-2, 0),
            (-1, 1),
            (-1, -1),
        }
    )
    blocked: frozenset[tuple[int, int]] = frozenset()
    transport: frozenset[tuple[int, int]] = frozenset()
    tops = enumerate_extension_topologies(
        extractor,
        output_east,
        mineable,
        blocked,
        transport,
        max_extensions=3,
    )
    for t in tops:
        assert stub not in t.extension_cells


def test_three_sides_adjacent_to_extractor_are_used() -> None:
    ex = (-1, 0)
    out_dir = (1, 0)
    mineable = frozenset({ex, (-2, 0), (-1, 1), (-1, -1), (1, 0)})
    tops = enumerate_extension_topologies(ex, out_dir, mineable, frozenset(), frozenset())
    triple = next((t for t in tops if t.extension_count == 3), None)
    assert triple is not None
    assert triple.extension_cells == frozenset({(-2, 0), (-1, 1), (-1, -1)})


def test_extension_faces_parent_cardinal() -> None:
    ex = (-1, 0)
    out_dir = (1, 0)
    mineable = frozenset({ex, (-2, 0), (-1, 1)})
    tops = enumerate_extension_topologies(ex, out_dir, mineable, frozenset(), frozenset())
    single = next(t for t in tops if t.extension_cells == frozenset({(-2, 0)}))
    facings = {c: (dx, dy) for c, dx, dy in single.facings}
    assert facings[(-2, 0)] == (1, 0)


def test_extension_to_extension_chain_allowed() -> None:
    ex = (-1, 0)
    out_dir = (1, 0)
    mineable = frozenset({ex, (-2, 0), (-3, 0), (-4, 0)})
    tops = enumerate_extension_topologies(ex, out_dir, mineable, frozenset(), frozenset())
    chain = next(
        (t for t in tops if t.extension_cells == frozenset({(-2, 0), (-3, 0), (-4, 0)})),
        None,
    )
    assert chain is not None


def test_max_three_extensions_enforced() -> None:
    ex = (-1, 0)
    out_dir = (1, 0)
    mineable = frozenset(
        {
            ex,
            (-2, 0),
            (-1, 1),
            (-1, -1),
            (-2, 1),
            (-2, -1),
            (-3, 0),
        }
    )
    tops = enumerate_extension_topologies(ex, out_dir, mineable, frozenset(), frozenset())
    assert max(t.extension_count for t in tops) <= 3


def test_deduplicated_canonical_signatures() -> None:
    ex = (-1, 0)
    out_dir = (1, 0)
    mineable = frozenset({ex, (-2, 0), (-1, 1)})
    tops = enumerate_extension_topologies(ex, out_dir, mineable, frozenset(), frozenset())
    sigs = [t.facings for t in tops]
    assert len(sigs) == len(set(sigs))


def test_rotation_r_for_extension_facing_parent_inverse_of_output_offset() -> None:
    assert rotation_r_for_extension_facing_parent((1, 0)) == 0
    assert rotation_r_for_extension_facing_parent((0, 1)) == 1
    assert rotation_r_for_extension_facing_parent((-1, 0)) == 2
    assert rotation_r_for_extension_facing_parent((0, -1)) == 3


def test_try_place_pass1_commits_extractor_with_three_extensions_when_route_ok() -> None:
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass1_outer_placement import (  # noqa: E501
        try_place_pass1_outer_bundle,
    )
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_bundle_commit import (  # noqa: E501
        Pass12LayoutScratch,
    )

    mineable = frozenset({(-1, 0), (-2, 0), (-1, 1), (-1, -1)})
    scratch = Pass12LayoutScratch()
    is_ext = lambda c: c not in mineable  # noqa: E731

    ok = try_place_pass1_outer_bundle(
        extractor_cell=(-1, 0),
        mineable_cells=mineable,
        asteroid_cells=mineable,
        scratch=scratch,
        is_external=is_ext,
        bundle_hint={"pass": "test"},
    )
    assert ok
    assert scratch.extractor_cells == {(-1, 0)}
    assert len(scratch.extension_facings) == 3
