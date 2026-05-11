"""Preserve-first seed: multi-miner existing layouts block unrouted bundles on hard gate."""

from __future__ import annotations

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass1_timeline_integration as p12_tl,
)
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
    assert stats["pass12_merged_seed_miner_count"] == 2
    assert stats["pass12_preserve_drop_reason_counts"] == {"ORPHAN_COMPONENT": 2}
    details = stats["pass12_preserved_missing_stub_drop_details"]
    assert len(details) == 2
    dropped = {tuple(d["miner_cell"]) for d in details}
    assert dropped == {(1, 1), (3, 1)}
    assert all(d["reason"] == "ORPHAN_COMPONENT" for d in details)
    assert all(d["preserve_drop_reason"] == "ORPHAN_COMPONENT" for d in details)
    assert all(d["transport_kind"] == "fluid_pipe" for d in details)
    assert all(d["expected_stub_role"] == "pipe" for d in details)
    assert all(d["adjacent_transport_cells"] == [] for d in details)
    assert all(d["nearest_same_kind_transport_hops"] is None for d in details)
    assert all(d["pass12_merged_seed_miner_count"] == 2 for d in details)
    assert stats["pass12_preserved_recovery_success_count"] == 0
    assert stats["pass12_preserved_recovery_traces"] == []


def test_seed_normalizes_ext_r_to_parent_facing_for_unrouted_preserve() -> None:
    """Unrouted preserve override must rewrite ext ``r`` to face the BFS parent miner."""

    mineable: frozenset[Coord] = frozenset({(1, 1), (2, 1), (1, 2), (-1, 1)})
    rows: list[dict[str, object]] = [
        {
            "x": 1,
            "y": 1,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 0,
            "surface": "fluid",
        },
        {
            "x": 2,
            "y": 1,
            "role": "occupied",
            "layout_kind": "fluid_extension",
            "r": 0,
            "surface": "fluid",
        },
    ]
    scratch = Pass12LayoutScratch(transport_kind="fluid_pipe")
    seed_pass12_scratch_from_merged_existing(
        rows,
        mineable=mineable,
        scratch=scratch,
        existing_layout_source_kind="existing_fluid_layout",
    )
    ext_override = scratch.preserved_mining_row_overrides.get((2, 1))
    assert ext_override is not None
    assert ext_override["r"] == 2
    assert scratch.extension_facings.get((2, 1)) == (-1, 0)


def test_seed_orphan_extension_parent_prefers_extractor_neighbor() -> None:
    """Orphan ext loop must pick an adjacent extractor over an adjacent extension."""

    mineable: frozenset[Coord] = frozenset({(2, 2), (2, 1), (1, 2), (5, 5)})
    rows: list[dict[str, object]] = [
        {
            "x": 2,
            "y": 2,
            "role": "occupied",
            "layout_kind": "fluid_extension",
            "r": 0,
            "surface": "fluid",
        },
        {
            "x": 2,
            "y": 1,
            "role": "occupied",
            "layout_kind": "fluid_extension",
            "r": 0,
            "surface": "fluid",
        },
        {
            "x": 1,
            "y": 2,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 0,
            "surface": "fluid",
        },
        {
            "x": 5,
            "y": 5,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 0,
            "surface": "fluid",
        },
    ]
    scratch = Pass12LayoutScratch(transport_kind="fluid_pipe")
    seed_pass12_scratch_from_merged_existing(
        rows,
        mineable=mineable,
        scratch=scratch,
        existing_layout_source_kind="existing_fluid_layout",
    )
    assert (1, 2) not in scratch.extractor_cells
    assert scratch.extension_facings.get((2, 2)) == (-1, 0)


def test_seed_emits_preserved_topology_observation_fields() -> None:
    """Preserve seed must expose extension-count histogram, average, and orphan count."""

    mineable: frozenset[Coord] = frozenset({(1, 1), (2, 1), (3, 1), (5, 5), (6, 5)})
    rows: list[dict[str, object]] = [
        {
            "x": 1,
            "y": 1,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 3,
            "surface": "fluid",
        },
        {
            "x": 2,
            "y": 1,
            "role": "occupied",
            "layout_kind": "fluid_extension",
            "r": 0,
            "surface": "fluid",
        },
        {
            "x": 3,
            "y": 1,
            "role": "occupied",
            "layout_kind": "fluid_extension",
            "r": 0,
            "surface": "fluid",
        },
        {"x": 1, "y": 0, "role": "pipe", "surface": "fluid"},
        {
            "x": 6,
            "y": 5,
            "role": "occupied",
            "layout_kind": "fluid_extension",
            "r": 0,
            "surface": "fluid",
        },
    ]
    scratch = Pass12LayoutScratch(transport_kind="fluid_pipe")
    stats = seed_pass12_scratch_from_merged_existing(
        rows,
        mineable=mineable,
        scratch=scratch,
        existing_layout_source_kind="existing_fluid_layout",
    )
    assert stats["pass12_preserved_bundle_extension_count_histogram"] == {2: 1}
    assert stats["pass12_preserved_extension_per_extractor_avg"] == 2.0
    assert stats["pass12_preserved_orphan_extension_count"] == 1


def test_integrate_pass12_unrouted_preserve_emits_parent_facing_ext_r() -> None:
    """Integration: blueprint ext with wrong ``r`` → merged map row aligned to parent-facing."""

    fm = [
        {
            "x": 1,
            "y": 1,
            "role": "occupied",
            "layout_kind": "asteroid_field",
            "surface": "fluid",
        },
        {
            "x": 2,
            "y": 1,
            "role": "occupied",
            "layout_kind": "asteroid_field",
            "surface": "fluid",
        },
    ]
    wm = [
        {
            "x": 1,
            "y": 1,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 0,
            "surface": "fluid",
            "t": "Layout_FluidMiner",
        },
        {
            "x": 2,
            "y": 1,
            "role": "occupied",
            "layout_kind": "fluid_extension",
            "r": 0,
            "surface": "fluid",
            "t": "Layout_FluidMinerExtension",
        },
    ]
    ela = {
        "source_kind": "existing_fluid_layout",
        "equipment": {"miner_count": 1, "extension_count": 1},
        "transport": {},
        "issues": [],
    }
    _m1, m2, _stats = p12_tl.integrate_pass12_placement_into_working_map(
        working_map=wm,
        final_mining_map=fm,
        is_external=lambda c: c[0] > 5,
        existing_layout_analysis=ela,
        suppress_pass1_pass2_loops=True,
    )
    by_xy = {(int(r["x"]), int(r["y"])): r for r in m2}
    ext_row = by_xy.get((2, 1))
    assert ext_row is not None
    assert ext_row.get("layout_kind") == "fluid_extension"
    assert ext_row.get("r") == 2
