"""Preserve-first seed: multi-miner existing layouts block unrouted bundles on hard gate."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_bundle_commit import (
    Pass12LayoutScratch,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_merged_layout_seed import (
    seed_pass12_scratch_from_merged_existing,
)


def test_seed_blocks_two_unrouted_miners_when_existing_fluid_layout() -> None:
    """Hard gate applies to ``existing_fluid_layout``: all unrouted miner bundles are blocked."""

    mineable: frozenset[Coord] = frozenset({(1, 1), (2, 1), (1, 2), (2, 2), (3, 1), (3, 2)})
    rows: list[dict[str, object]] = [
        {"x": 1, "y": 1, "role": "occupied", "layout_kind": "fluid_miner", "r": 0, "surface": "fluid"},
        {"x": 2, "y": 1, "role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
        {"x": 3, "y": 1, "role": "occupied", "layout_kind": "fluid_miner", "r": 0, "surface": "fluid"},
        {"x": 3, "y": 2, "role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
    ]
    scratch = Pass12LayoutScratch(transport_kind="fluid_pipe")
    stats = seed_pass12_scratch_from_merged_existing(
        rows,
        mineable=mineable,
        scratch=scratch,
        existing_layout_source_kind="existing_fluid_layout",
    )
    assert (1, 1) in scratch.blocked_cells
    assert (3, 1) in scratch.blocked_cells
    assert stats["pass12_preserved_bundle_extractor_cells"] == 2
    assert stats["pass12_preserved_bundle_extension_cells"] == 2
