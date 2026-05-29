"""Pattern bundle highlight wire — replay/UI artifact only."""

from __future__ import annotations

import django_apps.asteroid_lab.replay.pattern_bundle_highlight as pattern_bundle_highlight
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


def test_adjacent_line_never_reuses_neighbor_color() -> None:
    """Regression: greedy must not wrap ``pick % PALETTE_SIZE`` into a conflicting slot."""

    cells = tuple(frozenset({(i, 0)}) for i in range(6))
    indices = assign_bundle_color_indices(cells)
    for i in range(1, len(cells)):
        assert indices[i] != indices[i - 1]


def test_two_color_palette_colors_four_cell_line(monkeypatch) -> None:
    monkeypatch.setattr(pattern_bundle_highlight, "PALETTE_SIZE", 2)
    cells = tuple(frozenset({(i, 0)}) for i in range(4))
    indices = assign_bundle_color_indices(cells)
    assert indices == (0, 1, 0, 1)


def test_palette_exhaustion_keeps_color_index_in_range_and_deterministic(
    monkeypatch,
) -> None:
    """When greedy cannot avoid reuse, indices stay in palette range and are stable."""

    monkeypatch.setattr(pattern_bundle_highlight, "PALETTE_SIZE", 2)
    cell = frozenset({(0, 0)})
    bundles = (cell, cell, cell)
    first = assign_bundle_color_indices(bundles)
    second = assign_bundle_color_indices(bundles)
    assert first == second
    assert first == (0, 1, 0)
    for idx in first:
        assert 0 <= idx < pattern_bundle_highlight.PALETTE_SIZE

    wire = build_pattern_bundle_highlights_wire(
        (
            ("a", cell, None),
            ("b", cell, None),
            ("c", cell, None),
        )
    )
    for entry in wire["bundles"]:
        color_index = entry["color_index"]
        assert 0 <= color_index < pattern_bundle_highlight.PALETTE_SIZE


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
