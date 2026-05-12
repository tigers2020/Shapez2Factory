"""Pass12 NEAR_TRANSPORT stub-route recovery (inferred stub → same-kind trunk BFS)."""

from __future__ import annotations

from django.test import override_settings

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass12_bundle_commit,
    pass12_merged_layout_seed,
    pass12_preserve_stub_route_recovery,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize import (
    PRESERVE_QUALITY_SCORE_VERSION,
    preserve_quality_bundle_from_pass12,
)

try_preserve_stub_route_recovery = (
    pass12_preserve_stub_route_recovery.try_preserve_stub_route_recovery
)
goal_transport_cells = pass12_preserve_stub_route_recovery.goal_transport_cells

Pass12LayoutScratch = pass12_bundle_commit.Pass12LayoutScratch
seed_pass12_scratch_from_merged_existing = (
    pass12_merged_layout_seed.seed_pass12_scratch_from_merged_existing
)


@override_settings(SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY=True)
def test_stub_route_recovery_success_mvp() -> None:
    """Inferred output stub + pipe trunk within hop cap → ROUTED_CONFIRMED, drop avoided."""

    mineable: frozenset[Coord] = frozenset(
        {
            (5, 2),
            (5, 3),
            (5, 4),
            (5, 5),
            (5, 6),
            (6, 5),
            (10, 10),
            (11, 10),
        }
    )
    rows: list[dict[str, object]] = [
        {
            "x": 5,
            "y": 5,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 3,
            "surface": "fluid",
        },
        {"x": 6, "y": 5, "role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
        {"x": 5, "y": 6, "role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
        {"x": 5, "y": 4, "role": "inferred", "surface": "fluid"},
        {"x": 5, "y": 3, "role": "occupied", "layout_kind": "asteroid_field", "surface": "fluid"},
        {"x": 5, "y": 2, "role": "pipe", "surface": "fluid"},
        {
            "x": 10,
            "y": 10,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 0,
            "surface": "fluid",
        },
        {"x": 11, "y": 10, "role": "pipe", "surface": "fluid"},
    ]
    scratch = Pass12LayoutScratch(transport_kind="fluid_pipe")
    scratch.transport_cells.update({(5, 2), (11, 10)})
    stats = seed_pass12_scratch_from_merged_existing(
        rows,
        mineable=mineable,
        scratch=scratch,
        existing_layout_source_kind="existing_fluid_layout",
    )
    assert stats["pass12_preserved_missing_stub_route_recovery_success_count"] >= 1
    assert stats["pass12_preserved_missing_stub_drop_extractor_count"] == 0
    assert stats["pass12_preserved_routed_placement_records"] == 2
    assert (5, 4) in scratch.transport_cells
    assert (5, 3) in scratch.transport_cells


def test_goal_transport_cells_filters_scratch_by_opposite_role() -> None:
    """Scratch may aggregate belt+pipe coords; pipe BFS goals must not treat belt rows as goals."""

    cells = {
        (1, 0): {"role": "belt"},
        (2, 0): {"role": "pipe"},
    }
    scratch = frozenset({(1, 0), (2, 0), (9, 9)})
    goals = goal_transport_cells(cells=cells, want_wr="pipe", scratch_transport_cells=scratch)
    assert (1, 0) not in goals
    assert (2, 0) in goals
    assert (9, 9) in goals


def test_stub_route_recovery_rejects_mixed_kind_trunk() -> None:
    """Belt on corridor blocks pipe BFS → no_same_kind_route."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
        final_validation as fv,
    )

    cells = fv.cells_dict_from_mining_map(
        [
            {
                "x": 3,
                "y": 3,
                "role": "occupied",
                "layout_kind": "fluid_miner",
                "r": 3,
                "surface": "fluid",
            },
            {
                "x": 4,
                "y": 3,
                "role": "occupied",
                "layout_kind": "fluid_extension",
                "surface": "fluid",
            },
            {"x": 3, "y": 2, "role": "inferred", "surface": "fluid"},
            {
                "x": 3,
                "y": 1,
                "role": "occupied",
                "layout_kind": "asteroid_field",
                "surface": "fluid",
            },
            {"x": 3, "y": 0, "role": "belt", "surface": "shape"},
            {
                "x": 3,
                "y": -1,
                "role": "occupied",
                "layout_kind": "asteroid_field",
                "surface": "fluid",
            },
            {"x": 3, "y": -2, "role": "pipe", "surface": "fluid"},
        ]
    )
    mineable: frozenset[Coord] = frozenset(cells.keys())
    res = try_preserve_stub_route_recovery(
        miner=(3, 3),
        extensions=frozenset({(4, 3)}),
        transport_kind="fluid_pipe",
        cells=cells,
        mineable=mineable,
        scratch_transport_cells=frozenset({(3, -2)}),
        scratch_blocked_cells=frozenset(),
        nearest_same_kind_transport_hops=4,
        row_r_raw=3,
    )
    assert res.accepted is False
    psr = res.trace.get("preserve_stub_recovery")
    assert isinstance(psr, dict)
    assert psr.get("rejected_reason") == "no_same_kind_route"


def test_stub_route_recovery_extension_carve_disabled() -> None:
    """When stub cell is occupied by extension for every rotation, probe ends extension_carve."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
        final_validation as fv,
    )

    cells = fv.cells_dict_from_mining_map(
        [
            {
                "x": 3,
                "y": 3,
                "role": "occupied",
                "layout_kind": "fluid_miner",
                "r": 0,
                "surface": "fluid",
            },
            {
                "x": 4,
                "y": 3,
                "role": "occupied",
                "layout_kind": "fluid_extension",
                "surface": "fluid",
            },
            {
                "x": 2,
                "y": 3,
                "role": "occupied",
                "layout_kind": "fluid_extension",
                "surface": "fluid",
            },
            {
                "x": 3,
                "y": 2,
                "role": "occupied",
                "layout_kind": "fluid_extension",
                "surface": "fluid",
            },
            {
                "x": 3,
                "y": 4,
                "role": "occupied",
                "layout_kind": "fluid_extension",
                "surface": "fluid",
            },
            {"x": 3, "y": 5, "role": "pipe", "surface": "fluid"},
        ]
    )
    mineable: frozenset[Coord] = frozenset(cells.keys()) | {(10, 10), (11, 10)}
    res = try_preserve_stub_route_recovery(
        miner=(3, 3),
        extensions=frozenset({(4, 3), (2, 3), (3, 2), (3, 4)}),
        transport_kind="fluid_pipe",
        cells=cells,
        mineable=mineable,
        scratch_transport_cells=frozenset({(3, 5), (11, 10)}),
        scratch_blocked_cells=frozenset(),
        nearest_same_kind_transport_hops=2,
        row_r_raw=0,
    )
    assert res.accepted is False
    psr = res.trace.get("preserve_stub_recovery")
    assert isinstance(psr, dict)
    assert psr.get("rejected_reason") == "extension_carve_disabled"


@override_settings(SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY=True)
def test_stub_route_recovery_new_transport_cap_reject() -> None:
    """Shortest path needs more new transport cells than cap → new_transport_cells bucket."""

    from unittest.mock import patch

    mineable: frozenset[Coord] = frozenset(
        {(5, 5), (6, 5), (5, 4), (5, 3), (5, 2), (5, 1), (10, 10), (11, 10)}
    )
    cells_list: list[dict[str, object]] = [
        {
            "x": 5,
            "y": 5,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 3,
            "surface": "fluid",
        },
        {"x": 6, "y": 5, "role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
        {"x": 5, "y": 6, "role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
        {"x": 5, "y": 4, "role": "inferred", "surface": "fluid"},
        {
            "x": 10,
            "y": 10,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 0,
            "surface": "fluid",
        },
        {"x": 11, "y": 10, "role": "pipe", "surface": "fluid"},
    ]
    for y in (3, 2):
        cells_list.append(
            {
                "x": 5,
                "y": y,
                "role": "occupied",
                "layout_kind": "asteroid_field",
                "surface": "fluid",
            }
        )
    cells_list.append({"x": 5, "y": 1, "role": "pipe", "surface": "fluid"})
    scratch = Pass12LayoutScratch(transport_kind="fluid_pipe")
    scratch.transport_cells.update({(11, 10), (5, 1)})
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.placement."
        "pass12_preserve_stub_route_recovery.MAX_PASS12_STUB_ROUTE_RECOVERY_NEW_TRANSPORT_CELLS",
        1,
    ):
        stats = seed_pass12_scratch_from_merged_existing(
            cells_list,
            mineable=mineable,
            scratch=scratch,
            existing_layout_source_kind="existing_fluid_layout",
        )
    assert (
        stats["pass12_preserved_missing_stub_route_recovery_rejected_by_new_transport_cells_count"]
        >= 1
    )


def test_try_preserve_stub_route_recovery_pure_no_scratch_mutation() -> None:
    """Probe uses frozenset inputs; reject path does not alter caller-owned sets."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
        final_validation as fv,
    )

    cells = fv.cells_dict_from_mining_map(
        [
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
                "surface": "fluid",
            },
            {"x": 1, "y": 0, "role": "inferred", "surface": "fluid"},
            {
                "x": 1,
                "y": -1,
                "role": "occupied",
                "layout_kind": "asteroid_field",
                "surface": "fluid",
            },
            {"x": 3, "y": 1, "role": "belt", "surface": "shape"},
        ]
    )
    mineable: frozenset[Coord] = frozenset({(1, 1), (2, 1), (1, 0), (1, -1), (3, 1)})
    tr = frozenset({(3, 1)})
    bl: frozenset[Coord] = frozenset()
    res = try_preserve_stub_route_recovery(
        miner=(1, 1),
        extensions=frozenset({(2, 1)}),
        transport_kind="fluid_pipe",
        cells=cells,
        mineable=mineable,
        scratch_transport_cells=tr,
        scratch_blocked_cells=bl,
        nearest_same_kind_transport_hops=3,
        row_r_raw=3,
    )
    assert res.accepted is False
    assert tr == frozenset({(3, 1)})


@override_settings(SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY=True)
def test_preserve_quality_bundle_includes_stub_route_counters() -> None:
    bundle, score = preserve_quality_bundle_from_pass12(
        {
            "pass12_merged_seed_miner_count": 4,
            "pass12_preserved_bundle_extractor_cells": 3,
            "pass12_preserved_missing_stub_drop_extractor_count": 1,
            "pass12_preserved_recovery_success_count": 1,
            "pass12_preserved_missing_stub_route_recovery_attempted_count": 2,
            "pass12_preserved_missing_stub_route_recovery_success_count": 1,
        }
    )
    assert bundle["stub_route_recovery_attempted_count"] == 2
    assert bundle["stub_route_recovery_success_count"] == 1
    assert bundle["preserve_quality_score_version"] == PRESERVE_QUALITY_SCORE_VERSION
    assert score is not None
