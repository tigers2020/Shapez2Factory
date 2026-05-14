"""Preserve-first seed: multi-miner existing layouts block unrouted bundles on hard gate."""

from __future__ import annotations

from django.test import override_settings

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass1_timeline_integration as p12_tl,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass12_bundle_commit,
    pass12_merged_layout_seed,
    pass12_preserve_stub_route_recovery,
)

Pass12LayoutScratch = pass12_bundle_commit.Pass12LayoutScratch
seed_pass12_scratch_from_merged_existing = (
    pass12_merged_layout_seed.seed_pass12_scratch_from_merged_existing
)


def test_preserve_missing_stub_summary_includes_bounded_recovery_counts() -> None:
    """``preserve_missing_stub_summary.bounded_recovery`` rolls up per-drop tier telemetry."""

    details = [
        {
            "preserve_drop_reason": "NO_MATCHING_STUB",
            "preserve_stub_recovery": {
                "tier_a_attempted": True,
                "tier_a_success": False,
                "tier_b_attempted": True,
                "tier_b_success": False,
                "tier_b_failure_reason": "tier_b_failed_no_same_kind_route",
                "tier_c_attempted": True,
                "tier_c_success": True,
                "tier_c_skip_reason": None,
                "recovery_tier_attempted": ["A", "B", "C"],
                "rejected_reason": "no_same_kind_route",
                "rejected_reason_subtype": "occupied_neighbor_ring",
            },
        },
        {
            "preserve_drop_reason": "NO_MATCHING_STUB",
            "preserve_stub_recovery": {
                "tier_a_attempted": True,
                "tier_a_success": False,
                "tier_b_attempted": True,
                "tier_b_success": False,
                "tier_c_attempted": False,
                "tier_c_success": False,
                "tier_c_skip_reason": "tier_c_skipped_no_candidate_pairs",
                "tier_d_attempted": True,
                "tier_d_success": False,
                "tier_d_skip_reason": None,
                "tier_d_failure_reason": "tier_d_failed_no_same_kind_route",
                "recovery_tier_attempted": ["A", "B", "D"],
                "rejected_reason": "no_same_kind_route",
                "rejected_reason_subtype": "no_goal_relaxed",
            },
        },
    ]
    summary = pass12_merged_layout_seed._preserve_missing_stub_summary_from_details(details)
    br = summary.get("bounded_recovery")
    assert isinstance(br, dict)
    assert br["tier_a_attempted_count"] == 2
    assert br["tier_c_attempted_count"] == 1
    assert br["tier_c_success_count"] == 1
    assert br["tier_d_attempted_count"] == 1
    assert br["tier_d_success_count"] == 0
    assert br["tier_b_failure_reason_counts"].get("tier_b_failed_no_same_kind_route") == 1
    assert br["tier_c_skip_reason_counts"].get("tier_c_skipped_no_candidate_pairs") == 1
    assert br["tier_d_failure_reason_counts"].get("tier_d_failed_no_same_kind_route") == 1
    assert br["final_rejected_reason_subtype_counts"].get("occupied_neighbor_ring") == 1
    assert br["final_rejected_reason_subtype_counts"].get("no_goal_relaxed") == 1
    assert summary["unrecoverable_drop_count"] == 1
    assert summary["unrecoverable_reason_counts"].get("no_legal_same_kind_route_under_bounds") == 1


def test_preserve_missing_stub_summary_counts_tier_d_success_in_bounded_recovery() -> None:
    """Synthetic row: ``tier_d_success`` rolls into ``bounded_recovery`` (replay tooling)."""

    details = [
        {
            "preserve_drop_reason": "NO_MATCHING_STUB",
            "preserve_stub_recovery": {
                "tier_d_attempted": True,
                "tier_d_success": True,
                "tier_d_skip_reason": None,
                "tier_d_failure_reason": None,
                "rejected_reason": "no_same_kind_route",
            },
        },
    ]
    summary = pass12_merged_layout_seed._preserve_missing_stub_summary_from_details(details)
    br = summary["bounded_recovery"]
    assert br["tier_d_success_count"] == 1
    assert summary["unrecoverable_drop_count"] == 0


def test_preserve_missing_stub_summary_unrecoverable_reason_counts() -> None:
    """Diagonal-only Tier D skip and orphan rows bump ``unrecoverable_reason_counts``."""

    details = [
        {
            "preserve_drop_reason": "NO_MATCHING_STUB",
            "preserve_stub_recovery": {
                "tier_d_attempted": False,
                "tier_d_success": False,
                "tier_d_skip_reason": "tier_d_skipped_diagonal_only_extension_topology",
                "tier_d_failure_reason": None,
            },
        },
        {
            "preserve_drop_reason": "ORPHAN_COMPONENT",
            "preserve_stub_recovery": {"attempted": False},
        },
    ]
    summary = pass12_merged_layout_seed._preserve_missing_stub_summary_from_details(details)
    assert summary["unrecoverable_drop_count"] == 2
    ur = summary["unrecoverable_reason_counts"]
    assert ur.get("diagonal_only_extension_topology") == 1
    assert ur.get("orphan_or_invalid_no_preserve_trunk") == 1


def test_report_pass12_preserved_missing_stub_drop_details_shape() -> None:
    """Report helper is NDJSON-oriented and does not read files."""

    rows_in = [
        {
            "miner_cell": [1, 2],
            "transport_kind": "fluid_pipe",
            "nearest_same_kind_transport_hops": 2,
            "nearest_same_kind_transport_cell": [9, 9],
            "recoverability_class": "NEAR_TRANSPORT",
            "preserve_drop_reason": "NO_MATCHING_STUB",
            "adjacent_cardinal_cells": [],
            "rotation_probe_summary": [],
            "preserve_stub_recovery": {
                "rejected_reason": "no_same_kind_route",
                "rejected_reason_subtype": "occupied_neighbor_ring",
                "tier_d_attempted": True,
                "tier_d_success": False,
                "tier_d_skip_reason": None,
                "tier_d_failure_reason": "tier_d_failed_no_same_kind_route",
                "output_repack_candidate_count": 3,
                "output_repack_candidate_sample": [{"cand_r": 0}],
                "output_repack_selected_rotation": None,
                "stub_route_probe_last": {"blocked_frontier_reason_counts": {"x": 1}},
            },
        },
    ]
    out = pass12_merged_layout_seed.report_pass12_preserved_missing_stub_drop_details(rows_in)
    assert len(out) == 1
    r0 = out[0]
    assert r0["miner_cell"] == [1, 2]
    assert r0["blocked_frontier_reason_counts"] == {"x": 1}
    assert r0["pass12_remaining_drop_classification"] == "unrecoverable_by_design"
    assert (
        r0["pass12_unrecoverable_contract_reason_code"] == "no_legal_same_kind_route_under_bounds"
    )


@override_settings(SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY=True)
def test_merged_seed_applies_tier_d_extension_removal_and_placements() -> None:
    """Merged seed applies ``tier_d_extensions_removed`` / placements when probe returns Tier D."""

    from unittest.mock import patch

    def fluid_ext(x: int, y: int) -> dict[str, object]:
        return {
            "x": x,
            "y": y,
            "role": "occupied",
            "layout_kind": "fluid_extension",
            "surface": "fluid",
            "r": 0,
        }

    def inferred(x: int, y: int) -> dict[str, object]:
        return {
            "x": x,
            "y": y,
            "role": "inferred",
            "layout_kind": "asteroid_field",
            "surface": "fluid",
        }

    rows: list[dict[str, object]] = [
        {
            "x": 5,
            "y": 5,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "surface": "fluid",
            "r": 1,
        },
        fluid_ext(6, 5),
    ]
    for y in range(6, 10):
        rows.append(inferred(5, y))
    rows.append({"x": 5, "y": 10, "role": "pipe", "surface": "fluid"})
    rows.extend(
        [
            {
                "x": 30,
                "y": 30,
                "role": "occupied",
                "layout_kind": "fluid_miner",
                "surface": "fluid",
                "r": 0,
            },
            fluid_ext(29, 30),
            {"x": 31, "y": 30, "role": "pipe", "surface": "fluid"},
        ]
    )
    mineable = frozenset((x, y) for x in range(2, 40) for y in range(2, 40))
    scratch = Pass12LayoutScratch(transport_kind="fluid_pipe")
    orig_try = pass12_merged_layout_seed.try_preserve_stub_route_recovery

    def _tier_d_stub_for_miner_5_5(
        **kwargs: object,
    ) -> pass12_preserve_stub_route_recovery.StubRouteRecoveryResult:
        miner = kwargs["miner"]
        extensions = kwargs["extensions"]
        if miner == (5, 5) and extensions:
            psr = pass12_preserve_stub_route_recovery._empty_psr(3)
            psr["tier_d_attempted"] = True
            psr["tier_d_success"] = True
            psr["tier_d_skip_reason"] = None
            psr["tier_d_failure_reason"] = None
            psr["output_repack_candidate_count"] = 1
            psr["output_repack_candidate_sample"] = []
            psr["output_repack_selected_rotation"] = 1
            rem = sorted(extensions, key=lambda p: (p[1], p[0]))
            psr["output_repack_removed_extension_cells"] = [[int(c[0]), int(c[1])] for c in rem]
            psr["output_repack_replaced_extension_cells"] = [[4, 5]]
            psr["output_repack_preserved_extension_count"] = len(extensions)
            psr["output_repack_route_len_edges"] = 4
            psr["selected_r"] = 1
            psr["accepted"] = True
            ext_row = {
                "x": 4,
                "y": 5,
                "role": "occupied",
                "layout_kind": "fluid_extension",
                "surface": "fluid",
                "r": 0,
            }
            return pass12_preserve_stub_route_recovery.StubRouteRecoveryResult(
                accepted=True,
                trace={"preserve_stub_recovery": psr},
                new_transport_coords=frozenset(),
                chosen_r=1,
                stub_cell=(5, 6),
                carved_extension_cells=frozenset(),
                tier_d_extensions_removed=extensions,
                tier_d_extension_placements=(((4, 5), ext_row),),
                tier_d_final_extension_cells=frozenset({(4, 5)}),
            )
        return orig_try(**kwargs)

    with (
        patch.object(
            pass12_merged_layout_seed, "_attempt_preserve_stub_recovery", return_value=None
        ),
        patch.object(
            pass12_merged_layout_seed,
            "try_preserve_stub_route_recovery",
            side_effect=_tier_d_stub_for_miner_5_5,
        ),
    ):
        stats = seed_pass12_scratch_from_merged_existing(
            rows,
            mineable=mineable,
            scratch=scratch,
            existing_layout_source_kind="existing_fluid_layout",
        )
    assert stats["pass12_preserved_missing_stub_route_recovery_success_count"] >= 1
    assert (4, 5) in scratch.blocked_cells
    assert scratch.extension_facings.get((4, 5)) is not None
    assert any(
        rec.extractor_cell == (5, 5) and (4, 5) in rec.extension_cells
        for rec in scratch.placement_records.values()
    )
    assert scratch.preserved_mining_row_overrides.get((6, 5)) is None


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
