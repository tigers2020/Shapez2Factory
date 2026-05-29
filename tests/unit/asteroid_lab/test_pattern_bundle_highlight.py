"""Pattern bundle highlight wire — replay/UI artifact only."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.pattern_bundle_highlight import (
    METRICS_KEY,
    assign_bundle_color_indices,
    build_pattern_bundle_highlights_wire,
    mining_occupied_from_rim_placement,
)


def test_adjacent_bundles_get_different_color_index() -> None:
    a = frozenset({(1, 0), (2, 0)})
    b = frozenset({(3, 0), (4, 0)})
    indices = assign_bundle_color_indices((a, b))
    assert indices[0] != indices[1]


def test_overlapping_footprints_get_different_color_index() -> None:
    cell = frozenset({(2, 2)})
    indices = assign_bundle_color_indices((cell, cell))
    assert indices[0] != indices[1]


def test_non_adjacent_bundles_may_share_color_index() -> None:
    a = frozenset({(1, 0)})
    b = frozenset({(10, 0)})
    indices = assign_bundle_color_indices((a, b))
    assert indices == (0, 0)


def test_wire_excludes_empty_and_has_version() -> None:
    wire = build_pattern_bundle_highlights_wire(
        (
            ("k1", frozenset({(1, 0)}), "miner_seed_m0e_01"),
            ("k2", frozenset({(5, 0)}), "miner_seed_m1e_01"),
        )
    )
    assert wire["version"] == 1
    bundles = wire["bundles"]
    assert len(bundles) == 2
    assert bundles[0]["bundle_key"] == "k1"
    assert bundles[0]["gene_key"] == "miner_seed_m0e_01"
    assert "color_index" in bundles[0]
    assert bundles[0]["outline_loops"]


def test_wire_empty_when_no_entries() -> None:
    assert build_pattern_bundle_highlights_wire(()) == {}


def test_wire_uses_metrics_key_constant() -> None:
    wire = build_pattern_bundle_highlights_wire((("k1", frozenset({(1, 0)}), None),))
    assert METRICS_KEY == "pattern_bundle_highlights"
    assert wire


def test_mining_occupied_from_rim_placement_excludes_stub() -> None:
    extractor = frozenset({(1, 0)})
    extension = frozenset({(1, 1)})
    stub = frozenset({(2, 0)})

    class _Placement:
        extractor_cells = extractor
        extension_cells = extension
        output_stub_cells = stub

    occupied = mining_occupied_from_rim_placement(_Placement())
    assert occupied == extractor | extension
    assert stub.isdisjoint(occupied)
