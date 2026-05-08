"""Tests for blueprint → solver mask reconstruction."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_reconstruction import (
    gather_bp_entries_recursive,
    reconstruct_from_decoded,
)


def test_reconstruct_excludes_belt_pipe_from_mineable() -> None:
    decoded = {
        "BP": {
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_ShapeMiner"},
                {"X": 2, "Y": 0, "T": "belt"},
                {"X": -1, "Y": 0, "T": "something pipe row"},
            ]
        }
    }
    rec = reconstruct_from_decoded(decoded)
    assert rec is not None
    assert (1, 0) in rec.mineable_placement_cells
    assert (2, 0) in rec.blueprint_occupied_cells
    assert (2, 0) in rec.legacy_transport_cells
    assert (2, 0) not in rec.mineable_placement_cells
    assert (-1, 0) not in rec.mineable_placement_cells


def test_reconstruct_none_when_only_x_zero_entries() -> None:
    decoded = {"BP": {"Entries": [{"X": 0, "Y": 0, "T": "belt"}]}}
    assert reconstruct_from_decoded(decoded) is None


def test_gather_nested_building_entries() -> None:
    decoded = {
        "BP": {
            "Building": {"Entries": [{"X": 3, "Y": -1, "T": "Layout_ShapeMiner"}]},
            "Entries": [],
        }
    }
    ls = gather_bp_entries_recursive(decoded)
    xs = {(e["X"], e.get("Y", 0)) for e in ls}
    assert (3, -1) in xs
