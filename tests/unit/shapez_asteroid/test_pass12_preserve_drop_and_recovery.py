"""Preserve-first drop taxonomy, optional relaxed stub recovery, and finalize quality bundle."""

from __future__ import annotations

import pytest
from django.test import override_settings

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    MAX_PASS12_RECOVERY_BFS_HOPS,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass12_bundle_commit,
    pass12_merged_layout_seed,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline import (
    pass12_ab_metrics,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize import (
    PRESERVE_QUALITY_SCORE_VERSION,
    preserve_quality_bundle_from_pass12,
)

Pass12LayoutScratch = pass12_bundle_commit.Pass12LayoutScratch
seed_pass12_scratch_from_merged_existing = (
    pass12_merged_layout_seed.seed_pass12_scratch_from_merged_existing
)


def test_preserve_drop_mixed_kind_vs_orphan_histogram() -> None:
    """Wrong-kind cardinal transport → MIXED_KIND; no transport anywhere → ORPHAN."""

    mineable: frozenset[Coord] = frozenset(
        {
            (1, 0),
            (1, 1),
            (2, 1),
            (5, 1),
            (6, 1),
        }
    )
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
        {"x": 1, "y": 0, "role": "belt", "surface": "shape"},
        {
            "x": 5,
            "y": 1,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 0,
            "surface": "fluid",
        },
        {"x": 6, "y": 1, "role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
    ]
    scratch = Pass12LayoutScratch(transport_kind="fluid_pipe")
    stats = seed_pass12_scratch_from_merged_existing(
        rows,
        mineable=mineable,
        scratch=scratch,
        existing_layout_source_kind="existing_fluid_layout",
    )
    assert stats["pass12_preserved_missing_stub_drop_extractor_count"] == 2
    counts = stats["pass12_preserve_drop_reason_counts"]
    assert counts.get("MIXED_KIND_CONFLICT") == 1
    assert counts.get("ORPHAN_COMPONENT") == 1
    rcc = stats["pass12_recoverability_class_counts"]
    assert rcc.get("NEEDS_REROUTE") == 1
    assert rcc.get("UNRECOVERABLE") == 1
    for row in stats["pass12_preserved_missing_stub_drop_details"]:
        assert "recoverability_class" in row


@override_settings(SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY=True)
def test_relaxed_stub_recovery_routes_one_miner_when_flag_enabled() -> None:
    """Relaxed layout_kind stub match recovers ROUTED_CONFIRMED for one bundle (flag ON)."""

    mineable: frozenset[Coord] = frozenset(
        {
            (1, 0),
            (1, 1),
            (2, 1),
            (5, 1),
        }
    )
    rows: list[dict[str, object]] = [
        {
            "x": 1,
            "y": 1,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 2,
            "surface": "fluid",
        },
        {"x": 2, "y": 1, "role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
        {
            "x": 1,
            "y": 0,
            "role": "occupied",
            "layout_kind": "fluid_pipe",
            "surface": "fluid",
        },
        {
            "x": 5,
            "y": 1,
            "role": "occupied",
            "layout_kind": "fluid_miner",
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
    assert stats["pass12_preserved_recovery_success_count"] == 1
    assert len(stats["pass12_preserved_recovery_traces"]) == 1
    assert stats["pass12_preserved_missing_stub_drop_extractor_count"] == 1
    assert stats["pass12_preserved_routed_placement_records"] == 1
    assert (1, 1) in scratch.extractor_cells


def test_recoverability_class_mapping_table() -> None:
    """Static v1 mapping: hops band + reason → class."""

    fn = pass12_merged_layout_seed.recoverability_class_for_preserve_drop_detail
    assert (
        fn(
            {
                "preserve_drop_reason": "NO_MATCHING_STUB",
                "nearest_same_kind_transport_hops": 1,
            },
            max_recovery_bfs_hops=MAX_PASS12_RECOVERY_BFS_HOPS,
        ).value
        == "TRIVIAL"
    )
    assert (
        fn(
            {
                "preserve_drop_reason": "NO_MATCHING_STUB",
                "nearest_same_kind_transport_hops": 5,
            },
            max_recovery_bfs_hops=MAX_PASS12_RECOVERY_BFS_HOPS,
        ).value
        == "NEAR_TRANSPORT"
    )
    assert (
        fn(
            {
                "preserve_drop_reason": "NO_MATCHING_STUB",
                "nearest_same_kind_transport_hops": MAX_PASS12_RECOVERY_BFS_HOPS + 1,
            },
            max_recovery_bfs_hops=MAX_PASS12_RECOVERY_BFS_HOPS,
        ).value
        == "NEEDS_REROUTE"
    )
    assert fn({"preserve_drop_reason": "ORPHAN_COMPONENT"}).value == "UNRECOVERABLE"
    assert fn({"preserve_drop_reason": "MIXED_KIND_CONFLICT"}).value == "NEEDS_REROUTE"
    assert (
        fn(
            {
                "preserve_drop_reason": "NO_VALID_ROTATION",
                "expected_stub_role": "pipe",
                "adjacent_cardinal_cells": [{"role": "pipe"}],
            }
        ).value
        == "TRIVIAL"
    )
    assert (
        fn(
            {
                "preserve_drop_reason": "NO_VALID_ROTATION",
                "expected_stub_role": "pipe",
                "adjacent_cardinal_cells": [{"role": "occupied"}],
            }
        ).value
        == "LOCAL_ROTATION"
    )


def test_preserve_quality_bundle_and_score() -> None:
    bundle, score = preserve_quality_bundle_from_pass12(
        {
            "pass12_merged_seed_miner_count": 10,
            "pass12_preserved_bundle_extractor_cells": 7,
            "pass12_preserved_missing_stub_drop_extractor_count": 2,
            "pass12_preserved_recovery_success_count": 2,
            "pass12_preserved_missing_stub_route_recovery_attempted_count": 0,
            "pass12_preserved_missing_stub_route_recovery_success_count": 0,
        }
    )
    assert bundle["stub_route_recovery_attempted_count"] == 0
    assert bundle["stub_route_recovery_success_count"] == 0
    assert bundle["original_extractor_count"] == 10
    assert bundle["preserved_valid_count"] == 7
    assert bundle["dropped_invalid_count"] == 2
    assert bundle["recovered_stub_count"] == 2
    assert bundle["preserve_quality_score_version"] == PRESERVE_QUALITY_SCORE_VERSION
    assert score is not None
    assert score == pytest.approx(0.6, rel=0, abs=1e-6)


def test_recoverability_ab_outcome_join_and_rate() -> None:
    """OFF drop detail class + ON recovery trace miner_cell → recovered_by_class / rate."""

    b_off = {
        "pass12_preserved_missing_stub_drop_extractor_count": 3,
        "pass12_recoverability_class_counts": {"TRIVIAL": 2, "LOCAL_ROTATION": 1},
        "pass12_preserved_missing_stub_drop_details": [
            {
                "miner_cell": [1, 1],
                "recoverability_class": "TRIVIAL",
            },
            {
                "miner_cell": [5, 1],
                "recoverability_class": "TRIVIAL",
            },
            {
                "miner_cell": [9, 9],
                "recoverability_class": "LOCAL_ROTATION",
            },
        ],
        "pass12_preserved_recovery_traces": [],
    }
    b_on = {
        "pass12_recoverability_class_counts": {},
        "pass12_preserved_missing_stub_drop_details": [],
        "pass12_preserved_recovery_traces": [
            {"miner_cell": [1, 1]},
            {"miner_cell": [9, 9]},
        ],
    }
    out = pass12_ab_metrics.recoverability_ab_outcome_bundle(b_off, b_on)
    oc = out["recoverability_outcome_counts"]
    assert oc["dropped_off"] == {"LOCAL_ROTATION": 1, "TRIVIAL": 2}
    assert oc["recovered_by_class"] == {"LOCAL_ROTATION": 1, "TRIVIAL": 1}
    assert oc["orphan_on_recovery_trace_count"] == 0
    assert out["recovery_rate_by_class"]["TRIVIAL"] == pytest.approx(1.0 / 2.0, rel=0, abs=1e-6)
    assert out["recovery_rate_by_class"]["LOCAL_ROTATION"] == pytest.approx(1.0, rel=0, abs=1e-6)
    byc = out["recoverability_outcome_by_class"]
    assert byc["TRIVIAL"]["dropped"] == 2
    assert byc["TRIVIAL"]["recovered"] == 1
    assert byc["TRIVIAL"]["recovery_rate"] == pytest.approx(0.5, rel=0, abs=1e-6)
    assert out["recovery_candidate_fraction"] == pytest.approx(1.0, rel=0, abs=1e-6)
    assert out["recovery_candidate_count"] == 3
    assert out["recovery_candidate_denominator"] == 3


def test_recoverability_ab_recovery_candidate_excludes_unrecoverable() -> None:
    b_off = {
        "pass12_preserved_missing_stub_drop_extractor_count": 4,
        "pass12_recoverability_class_counts": {"TRIVIAL": 1, "UNRECOVERABLE": 3},
        "pass12_preserved_missing_stub_drop_details": [],
        "pass12_preserved_recovery_traces": [],
    }
    b_on = {
        "pass12_recoverability_class_counts": {},
        "pass12_preserved_missing_stub_drop_details": [],
        "pass12_preserved_recovery_traces": [],
    }
    out = pass12_ab_metrics.recoverability_ab_outcome_bundle(b_off, b_on)
    assert out["recovery_candidate_denominator"] == 4
    assert out["recovery_candidate_count"] == 1
    assert out["recovery_candidate_fraction"] == pytest.approx(0.25, rel=0, abs=1e-6)


def test_recoverability_ab_outcome_orphan_on_trace() -> None:
    b_off = {
        "pass12_preserved_missing_stub_drop_extractor_count": 1,
        "pass12_recoverability_class_counts": {"TRIVIAL": 1},
        "pass12_preserved_missing_stub_drop_details": [
            {"miner_cell": [1, 1], "recoverability_class": "TRIVIAL"},
        ],
        "pass12_preserved_recovery_traces": [],
    }
    b_on = {
        "pass12_recoverability_class_counts": {},
        "pass12_preserved_missing_stub_drop_details": [],
        "pass12_preserved_recovery_traces": [{"miner_cell": [99, 99]}],
    }
    out = pass12_ab_metrics.recoverability_ab_outcome_bundle(b_off, b_on)
    assert out["recoverability_outcome_counts"]["orphan_on_recovery_trace_count"] == 1
    assert out["recoverability_outcome_counts"]["recovered_by_class"] == {}
    assert out["recovery_candidate_fraction"] == pytest.approx(1.0, rel=0, abs=1e-6)


def test_preserve_quality_bundle_zero_miners_still_has_score_version() -> None:
    bundle, score = preserve_quality_bundle_from_pass12(
        {
            "pass12_merged_seed_miner_count": 0,
            "pass12_preserved_bundle_extractor_cells": 0,
            "pass12_preserved_missing_stub_drop_extractor_count": 0,
            "pass12_preserved_recovery_success_count": 0,
        }
    )
    assert bundle["preserve_quality_score_version"] == PRESERVE_QUALITY_SCORE_VERSION
    assert score is None
