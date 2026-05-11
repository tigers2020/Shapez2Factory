"""Preserve-first seed: multi-miner existing layouts block unrouted bundles on hard gate."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_bundle_commit import (
    Pass12LayoutScratch,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_merged_layout_seed import (
    seed_pass12_scratch_from_merged_existing,
)


def test_seed_drops_unrouted_miners_without_adjacent_stub_when_existing_fluid_layout() -> None:
    """Hard gate + multi-miner: unrouted bundles with no adjacent pipe/belt are not preserved."""

    mineable: frozenset[Coord] = frozenset({(1, 1), (2, 1), (1, 2), (2, 2), (3, 1), (3, 2)})
    rows: list[dict[str, object]] = [
        {
            "x": 1,
            "y": 1,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 0,
            "surface": "fluid",
        },
        {"x": 2, "y": 1, "role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
        {
            "x": 3,
            "y": 1,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 0,
            "surface": "fluid",
        },
        {"x": 3, "y": 2, "role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
    ]
    scratch = Pass12LayoutScratch(transport_kind="fluid_pipe")
    stats = seed_pass12_scratch_from_merged_existing(
        rows,
        mineable=mineable,
        scratch=scratch,
        existing_layout_source_kind="existing_fluid_layout",
    )
    assert (1, 1) not in scratch.blocked_cells
    assert (3, 1) not in scratch.blocked_cells
    assert stats["pass12_preserved_bundle_extractor_cells"] == 0
    assert stats["pass12_preserved_bundle_extension_cells"] == 0
    assert stats["pass12_preserved_missing_stub_drop_extractor_count"] == 2
    details = stats["pass12_preserved_missing_stub_drop_details"]
    assert len(details) == 2
    dropped = {tuple(d["miner_cell"]) for d in details}
    assert dropped == {(1, 1), (3, 1)}
    assert all(d["reason"] == "no_adjacent_matching_stub" for d in details)
    assert all(d["transport_kind"] == "fluid_pipe" for d in details)
    assert all(d["expected_stub_role"] == "pipe" for d in details)
    assert all(d["adjacent_transport_cells"] == [] for d in details)
