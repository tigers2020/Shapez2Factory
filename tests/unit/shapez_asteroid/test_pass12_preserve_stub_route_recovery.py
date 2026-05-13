"""Pass12 NEAR_TRANSPORT stub-route recovery (inferred stub → same-kind trunk BFS)."""

from __future__ import annotations

import copy

from django.test import override_settings

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import output_offset_r
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass1_timeline_integration as p12_tl,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass12_bundle_commit,
    pass12_merged_layout_seed,
    pass12_preserve_stub_route_recovery,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
    make_placement_id,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    EXTRACTORS_FLUID,
    EXTRACTORS_SHAPE,
    collect_routing_jobs,
    layout_kind,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize import (
    PRESERVE_QUALITY_SCORE_VERSION,
    preserve_quality_bundle_from_pass12,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_merge_routing import (
    run_step4_merge_aware_routing,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
    final_validation as final_val,
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
    """Inferred output stub + pipe trunk within hop cap → provisional seed; STEP4 confirms route."""

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
    assert stats["pass12_preserved_missing_stub_route_recovery_queue_rounds"] >= 0
    assert isinstance(stats.get("pass12_preserved_recovered_stub_samples"), list)
    assert len(stats["pass12_preserved_recovered_stub_samples"]) >= 1
    assert (5, 4) in scratch.transport_cells
    assert (5, 3) in scratch.transport_cells
    for _pid, rec in scratch.placement_records.items():
        assert rec.state == PlacementCommitState.PROVISIONAL_PLACED
    traces = stats.get("pass12_preserved_recovery_traces") or []
    assert traces
    psr0 = traces[0].get("preserve_stub_recovery")
    assert isinstance(psr0, dict)
    assert psr0.get("accepted") is True
    lastp = psr0.get("stub_route_probe_last")
    assert isinstance(lastp, dict)
    assert lastp.get("bfs_failure") is None
    assert int(lastp.get("reachable_same_kind_goals_under_edge_cap_512") or 0) >= 1
    assert lastp.get("start_cell") == lastp.get("stub_start_cell")
    assert isinstance(lastp.get("goal_sample"), list)
    assert psr0.get("goal_count") == lastp.get("goal_count")


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


def test_try_preserve_rejects_invalid_transport_kind() -> None:
    res = try_preserve_stub_route_recovery(
        miner=(1, 1),
        extensions=frozenset(),
        transport_kind="bogus_kind",
        cells={(2, 0): {"role": "pipe"}},
        mineable=frozenset({(1, 1), (2, 0)}),
        scratch_transport_cells=frozenset({(2, 0)}),
        scratch_blocked_cells=frozenset(),
        nearest_same_kind_transport_hops=2,
        row_r_raw=0,
    )
    psr = res.trace["preserve_stub_recovery"]
    assert psr["rejected_reason"] == "rejected_by_invalid_want_role"
    assert psr["attempted"] is False
    assert psr["miner_cell"] == [1, 1]


def test_try_preserve_scratch_goal_counters_on_trace() -> None:
    cells = {
        (10, 10): {
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 0,
            "surface": "fluid",
        },
        (1, 0): {"role": "belt"},
        (2, 0): {"role": "pipe"},
    }
    scratch = frozenset({(1, 0), (2, 0), (99, 99)})
    res = try_preserve_stub_route_recovery(
        miner=(10, 10),
        extensions=frozenset(),
        transport_kind="fluid_pipe",
        cells=cells,
        mineable=frozenset(cells.keys()) | scratch,
        scratch_transport_cells=scratch,
        scratch_blocked_cells=frozenset(),
        nearest_same_kind_transport_hops=99,
        row_r_raw=0,
        nearest_same_kind_transport_cell=(2, 0),
    )
    psr = res.trace["preserve_stub_recovery"]
    assert psr["scratch_transport_input_count"] == 3
    assert psr["scratch_goal_without_map_row_count"] == 1
    assert psr["scratch_goal_wrong_role_excluded_count"] == 1
    assert psr["scratch_goal_count"] == 2
    assert psr["rejected_reason"] == "nearest_hops_over_cap"
    assert psr["miner_cell"] == [10, 10]
    assert psr.get("nearest_same_kind_transport_cell") == [2, 0]


def test_try_preserve_stub_route_recovery_attempts_hop_seven_candidate() -> None:
    """hop=7 후보는 cap에 잘리지 않고 실제 경로 probe까지 진행한다."""

    cells = {
        (5, 5): {
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 3,
            "surface": "fluid",
        },
        (6, 5): {"role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
        (5, 6): {"role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
        (5, 4): {"role": "inferred", "surface": "fluid"},
        (5, 3): {"role": "occupied", "layout_kind": "asteroid_field", "surface": "fluid"},
        (5, 2): {"role": "occupied", "layout_kind": "asteroid_field", "surface": "fluid"},
        (5, 1): {"role": "occupied", "layout_kind": "asteroid_field", "surface": "fluid"},
        (5, 0): {"role": "occupied", "layout_kind": "asteroid_field", "surface": "fluid"},
        (5, -1): {"role": "occupied", "layout_kind": "asteroid_field", "surface": "fluid"},
        (5, -2): {"role": "pipe", "surface": "fluid"},
    }
    mineable: frozenset[Coord] = frozenset(cells.keys())
    res = try_preserve_stub_route_recovery(
        miner=(5, 5),
        extensions=frozenset({(6, 5), (5, 6)}),
        transport_kind="fluid_pipe",
        cells=cells,
        mineable=mineable,
        scratch_transport_cells=frozenset({(5, -2)}),
        scratch_blocked_cells=frozenset(),
        nearest_same_kind_transport_hops=7,
        row_r_raw=3,
    )
    psr = res.trace["preserve_stub_recovery"]
    assert psr["attempted"] is True
    assert res.accepted is True
    assert psr["route_len_edges"] == 6
    assert psr["new_transport_cell_count"] == 6


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
    assert psr.get("miner_cell") == [3, 3]
    assert psr.get("transport_kind") == "fluid_pipe"
    assert psr.get("goal_transport_cell_count") >= 1
    probe = psr.get("stub_route_probe_last")
    assert isinstance(probe, dict)
    assert probe.get("bfs_failure") == "no_same_kind_route"
    assert int(probe.get("expanded_nodes") or 0) >= 1
    counts = probe.get("blocked_frontier_reason_counts")
    assert isinstance(counts, dict)
    assert counts.get("wrong_kind_transport", 0) >= 1
    assert isinstance(probe.get("local_neighbor_cells_around_stub"), list)
    assert isinstance(probe.get("last_frontier_sample"), list)
    assert probe.get("start_cell") == probe.get("stub_start_cell")
    assert probe.get("goal_count") == psr.get("goal_count")
    assert isinstance(probe.get("goal_sample"), list)
    assert probe.get("edge_cap") is not None
    assert psr.get("rejected_reason_subtype") == "wrong_kind_transport_near_stub"
    assert isinstance(psr.get("local_neighbor_cells_around_stub"), list)


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
    assert psr.get("extension_carve_considered") is True
    assert psr.get("stub_route_probe_last", {}).get("bfs_failure") == "no_bfs_attempt"
    assert psr.get("rejected_reason_subtype") is None
    assert isinstance(psr.get("local_neighbor_cells_around_stub"), list)


def test_try_preserve_no_same_kind_subtype_under_small_edge_cap() -> None:
    """Tight edge cap: goals exist in relaxed graph but shortest path exceeds BFS edge cap."""

    from unittest.mock import patch

    cells = {
        (5, 5): {
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 3,
            "surface": "fluid",
        },
        (6, 5): {"role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
        (5, 6): {"role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
        (5, 4): {"role": "inferred", "surface": "fluid"},
        (5, 3): {"role": "occupied", "layout_kind": "asteroid_field", "surface": "fluid"},
        (5, 2): {"role": "occupied", "layout_kind": "asteroid_field", "surface": "fluid"},
        (5, 1): {"role": "occupied", "layout_kind": "asteroid_field", "surface": "fluid"},
        (5, 0): {"role": "pipe", "surface": "fluid"},
    }
    mineable: frozenset[Coord] = frozenset(cells.keys())
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.placement."
        "pass12_preserve_stub_route_recovery.MAX_PASS12_STUB_ROUTE_RECOVERY_PATH_LEN",
        2,
    ):
        res = try_preserve_stub_route_recovery(
            miner=(5, 5),
            extensions=frozenset({(6, 5), (5, 6)}),
            transport_kind="fluid_pipe",
            cells=cells,
            mineable=mineable,
            scratch_transport_cells=frozenset({(5, 0)}),
            scratch_blocked_cells=frozenset(),
            nearest_same_kind_transport_hops=6,
            row_r_raw=3,
        )
    psr = res.trace["preserve_stub_recovery"]
    assert psr.get("rejected_reason") == "no_same_kind_route"
    assert psr.get("rejected_reason_subtype") == "same_kind_goal_unreachable_under_edge_cap"
    probe = psr.get("stub_route_probe_last")
    assert isinstance(probe, dict)
    assert int(probe.get("reachable_same_kind_goals_under_edge_cap_512") or 0) >= 1
    assert (probe.get("blocked_frontier_reason_counts") or {}).get("exceeds_max_edges_cap", 0) >= 1


def test_try_preserve_visit_cap_rejected_reason_has_no_subtype() -> None:
    """visit_cap rejection must not attach no_same_kind_route subtype."""

    from unittest.mock import patch

    cells = {
        (5, 5): {
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 3,
            "surface": "fluid",
        },
        (6, 5): {"role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
        (5, 6): {"role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
        (5, 4): {"role": "inferred", "surface": "fluid"},
        (5, 3): {"role": "occupied", "layout_kind": "asteroid_field", "surface": "fluid"},
        (5, 2): {"role": "pipe", "surface": "fluid"},
    }
    mineable: frozenset[Coord] = frozenset(cells.keys())

    def _fake_bfs(
        *_a: object,
        **_k: object,
    ) -> tuple[None, dict[str, object]]:
        return None, {
            "failure": "visit_cap",
            "visited": 99999,
            "expanded_nodes": 3,
            "blocked_frontier_reason_counts": {"wrong_kind_transport": 5},
            "last_frontier_sample": [[5, 4]],
        }

    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.placement."
        "pass12_preserve_stub_route_recovery._bfs_shortest_path",
        _fake_bfs,
    ):
        res = try_preserve_stub_route_recovery(
            miner=(5, 5),
            extensions=frozenset({(6, 5), (5, 6)}),
            transport_kind="fluid_pipe",
            cells=cells,
            mineable=mineable,
            scratch_transport_cells=frozenset({(5, 2)}),
            scratch_blocked_cells=frozenset(),
            nearest_same_kind_transport_hops=3,
            row_r_raw=3,
        )
    psr = res.trace["preserve_stub_recovery"]
    assert psr.get("rejected_reason") == "visit_cap"
    assert psr.get("rejected_reason_subtype") is None
    assert "commit_reason" not in res.trace
    assert "commit_reason" not in psr


def test_missing_stub_drop_detail_merges_stub_route_probe_neighbors() -> None:
    """Deferred/immediate drop rows merge preserve_stub_recovery; probe neighbors must surface."""

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
    psr = res.trace["preserve_stub_recovery"]
    detail = pass12_merged_layout_seed._missing_stub_drop_detail_row(
        miner=(3, 3),
        cells=cells,
        tk="fluid_pipe",
        row_m={"r": 3, "surface": "fluid", "layout_kind": "fluid_miner", "role": "occupied"},
        merged_seed_miner_count=1,
        nhops=4,
        ncell=(3, -2),
        neighbor_stub_coords=(),
        eff_r=3,
        stub_route_trace_for_drop={"preserve_stub_recovery": psr},
    )
    merged = detail.get("preserve_stub_recovery")
    assert isinstance(merged, dict)
    probe = merged.get("stub_route_probe_last")
    assert isinstance(probe, dict)
    nb = probe.get("local_neighbor_cells_around_stub")
    assert isinstance(nb, list) and len(nb) >= 1
    assert merged.get("rejected_reason_subtype") == "wrong_kind_transport_near_stub"
    assert probe.get("start") == probe.get("start_cell")
    assert isinstance(probe.get("goal_count"), int) and probe.get("goal_count", 0) >= 1
    assert isinstance(merged.get("goal_count"), int)


def test_missing_stub_drop_detail_backfills_probe_and_subtype_like_solver_summary() -> None:
    """Partial nested probe + mirrors (production-like): normalize + JSON-serialize."""

    import json

    cells = {
        (5, 5): {"role": "occupied", "layout_kind": "fluid_miner", "r": 0, "surface": "fluid"},
    }
    detail = pass12_merged_layout_seed._missing_stub_drop_detail_row(
        miner=(5, 5),
        cells=cells,
        tk="fluid_pipe",
        row_m={"r": 0, "surface": "fluid", "layout_kind": "fluid_miner", "role": "occupied"},
        merged_seed_miner_count=2,
        nhops=3,
        ncell=(10, 10),
        neighbor_stub_coords=(),
        eff_r=0,
        stub_route_trace_for_drop={
            "preserve_stub_recovery": {
                "accepted": False,
                "attempted": True,
                "rejected_reason": "no_same_kind_route",
                "rejected_reason_subtype": None,
                "goal_transport_cell_count": 82,
                "start_cell": [5, 4],
                "stub_start_cell": [5, 4],
                "goal_count": 82,
                "stub_route_probe_last": {
                    "bfs_failure": "no_same_kind_route",
                    "reachable_same_kind_goals_under_edge_cap_512": 82,
                    "blocked_frontier_reason_counts": {"exceeds_max_edges_cap": 5},
                    "local_neighbor_cells_around_stub": [{"cell": [5, 6], "role": None}],
                },
            },
        },
    )
    psr = detail["preserve_stub_recovery"]
    probe = psr["stub_route_probe_last"]
    assert psr["rejected_reason_subtype"] == "same_kind_goal_unreachable_under_edge_cap"
    assert probe["start_cell"] == [5, 4]
    assert probe["start"] == [5, 4]
    assert probe["stub_start_cell"] == [5, 4]
    assert probe["goal_count"] == 82
    assert "commit_reason" not in detail
    assert "commit_reason" not in psr
    json.dumps(detail, default=str)
    solver_summary_fragment = {
        "pass12_preserved_missing_stub_drop_extractor_count": 1,
        "pass12_preserved_missing_stub_drop_details": [detail],
    }
    assert isinstance(solver_summary_fragment["pass12_preserved_missing_stub_drop_details"], list)
    json.dumps(solver_summary_fragment, default=str)


def test_missing_stub_drop_detail_stub_trace_none_includes_extension_carve_defaults() -> None:
    """stub_route_trace_for_drop 없을 때도 preserve_stub_recovery에 carve 스키마가 있다."""

    cells = {
        (5, 5): {"role": "occupied", "layout_kind": "fluid_miner", "r": 0, "surface": "fluid"},
    }
    detail = pass12_merged_layout_seed._missing_stub_drop_detail_row(
        miner=(5, 5),
        cells=cells,
        tk="fluid_pipe",
        row_m={"r": 0, "surface": "fluid", "layout_kind": "fluid_miner", "role": "occupied"},
        merged_seed_miner_count=2,
        nhops=3,
        ncell=(10, 10),
        neighbor_stub_coords=(),
        eff_r=0,
        stub_route_trace_for_drop=None,
    )
    psr = detail["preserve_stub_recovery"]
    assert psr["extension_carve_considered"] is False
    assert psr["extension_carve_candidate_cells"] == []
    assert psr["extension_carve_attempted"] is False
    assert "extension_carve_applied" in psr
    assert "post_carve_rejected_reason" in psr


def test_missing_stub_drop_detail_partial_psr_gets_extension_carve_defaults() -> None:
    """부분 ``preserve_stub_recovery``만 있어도 extension carve 스키마가 채워진다."""

    cells = {
        (5, 5): {"role": "occupied", "layout_kind": "fluid_miner", "r": 0, "surface": "fluid"},
    }
    detail = pass12_merged_layout_seed._missing_stub_drop_detail_row(
        miner=(5, 5),
        cells=cells,
        tk="fluid_pipe",
        row_m={"r": 0, "surface": "fluid", "layout_kind": "fluid_miner", "role": "occupied"},
        merged_seed_miner_count=2,
        nhops=3,
        ncell=(10, 10),
        neighbor_stub_coords=(),
        eff_r=0,
        stub_route_trace_for_drop={
            "preserve_stub_recovery": {"accepted": False, "attempted": True},
        },
    )
    psr = detail["preserve_stub_recovery"]
    assert psr["extension_carve_considered"] is False
    assert psr["extension_carve_candidate_cells"] == []
    assert psr["extension_carve_attempted"] is False


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
    assert "commit_reason" not in res.trace
    assert "commit_reason" not in (res.trace.get("preserve_stub_recovery") or {})


@override_settings(SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY=True)
def test_preserve_quality_bundle_includes_stub_route_counters() -> None:
    bundle, score = preserve_quality_bundle_from_pass12(
        {
            "pass12_merged_seed_miner_count": 4,
            "pass12_preserved_bundle_extractor_cells": 3,
            "pass12_preserved_missing_stub_drop_extractor_count": 1,
            "pass12_preserved_recovery_success_count": 1,
            "pass12_preserved_rotation_recovery_count": 0,
            "pass12_preserved_missing_stub_route_recovery_attempted_count": 2,
            "pass12_preserved_missing_stub_route_recovery_success_count": 1,
        }
    )
    assert bundle["stub_route_recovery_attempted_count"] == 2
    assert bundle["stub_route_recovery_success_count"] == 1
    assert bundle["recovered_stub_count"] == 1
    assert bundle["recovered_rotation_count"] == 0
    assert bundle["preserve_quality_score_version"] == PRESERVE_QUALITY_SCORE_VERSION
    assert score is not None


@override_settings(
    SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY=True,
    SHAPEZ_MINING_PASS2_FLUID_INTERNAL_FILL_ENABLED=False,
)
def test_integrate_pass12_stub_route_recovery_two_miners_missing_stub_zero() -> None:
    """Two fluid miners: stub-route recovery, missing_stub zero, no overlap, no belt/pipe mix."""

    mineable_cells = [
        (5, 3),
        (5, 4),
        (5, 5),
        (5, 6),
        (6, 5),
        (10, 10),
    ]
    fm = [
        {
            "x": x,
            "y": y,
            "role": "occupied",
            "layout_kind": "asteroid_field",
            "surface": "fluid",
        }
        for x, y in mineable_cells
    ]
    wm = [
        {
            "x": 5,
            "y": 5,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 3,
            "surface": "fluid",
            "t": "Layout_FluidMiner",
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
            "t": "Layout_FluidMiner",
        },
        {"x": 11, "y": 10, "role": "pipe", "surface": "fluid"},
    ]
    _m1, m2, stats = p12_tl.integrate_pass12_placement_into_working_map(
        working_map=wm,
        final_mining_map=fm,
        is_external=lambda _c: True,
        existing_layout_analysis={
            "source_kind": "existing_fluid_layout",
            "equipment": {"miner_count": 2, "extension_count": 0},
            "transport": {},
            "issues": [],
        },
        suppress_pass1_pass2_loops=True,
    )
    report = final_val.validate_final_mining_layout(m2)
    assert report.missing_stub_count == 0
    assert stats["pass12_preserved_missing_stub_route_recovery_success_count"] >= 1
    bundle, _bscore = preserve_quality_bundle_from_pass12(stats)
    assert bundle["recovered_stub_count"] > 0
    cells = final_val.cells_dict_from_mining_map(m2)
    extractors = {
        c for c, r in cells.items() if layout_kind(r) in EXTRACTORS_SHAPE | EXTRACTORS_FLUID
    }
    transport_cells = {c for c, r in cells.items() if r.get("role") in ("belt", "pipe")}
    assert not (extractors & transport_cells)
    belt_cells = {c for c, r in cells.items() if r.get("role") == "belt"}
    pipe_cells = {c for c, r in cells.items() if r.get("role") == "pipe"}
    assert not (belt_cells & pipe_cells)


def test_merge_restamps_baseline_stub_after_mineable_shell_overwrite() -> None:
    """Mineable shell must not erase a baseline stub still in ``scratch.transport_cells``."""

    mineable: frozenset[Coord] = frozenset({(5, 2), (5, 3), (5, 4), (5, 5), (5, 6), (6, 5)})
    working_map: list[dict[str, object]] = [
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
        {"x": 5, "y": 4, "role": "pipe", "surface": "fluid"},
        {"x": 5, "y": 3, "role": "occupied", "layout_kind": "asteroid_field", "surface": "fluid"},
        {"x": 5, "y": 2, "role": "pipe", "surface": "fluid"},
    ]
    final_mining_map: list[dict[str, object]] = [
        {
            "x": x,
            "y": y,
            "role": "inferred" if (x, y) == (5, 4) else "occupied",
            "layout_kind": "asteroid_field",
            "surface": "fluid",
        }
        for x, y in sorted(mineable, key=lambda p: (p[1], p[0]))
    ]
    scratch, transport_init, blocked_init = p12_tl.scratch_from_working_map(
        working_map, mineable_coords=mineable
    )
    scratch.transport_kind = "fluid_pipe"
    scratch.blocked_cells.update({(5, 5), (6, 5), (5, 6)})
    scratch.extractor_cells.add((5, 5))
    scratch.extractor_output_dirs[(5, 5)] = output_offset_r(3)
    scratch.transport_cells.update({(5, 4), (5, 2)})
    pid = make_placement_id("pass1", 1)
    scratch.placement_records[pid] = PlacementCommitRecord(
        placement_id=pid,
        placement_pass="pass1",
        extractor_cell=(5, 5),
        extension_cells=((5, 6), (6, 5)),
        stub_cell=(5, 4),
        transport_kind="fluid_pipe",
        state=PlacementCommitState.PROVISIONAL_PLACED,
        route_id="preserve_stub_route_recovery",
    )
    scratch.next_placement_seq = 1
    is_ext = final_val.external_predicate_for_mining_map([dict(r) for r in final_mining_map])
    merged, _stamp = p12_tl._merge_pass1_into_rows(
        working_map,
        final_mining_map,
        scratch,
        transport_init,
        blocked_init,
        mineable,
        "fluid",
        is_external=is_ext,
    )
    cells = final_val.cells_dict_from_mining_map(merged)
    assert cells[(5, 4)]["role"] == "pipe"
    jobs = collect_routing_jobs(cells)
    assert any(ext == (5, 5) for ext, *_ in jobs)


def test_tier_b_bundle_rollback_opens_route_after_tier_a_fails() -> None:
    """Bounded 1-extension rollback (tier B) can succeed when tier A exhausts free-stub probes."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
        final_validation as fv,
    )

    def ext() -> dict[str, object]:
        return {"role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"}

    def ast(x: int, y: int) -> dict[str, object]:
        return {"role": "occupied", "layout_kind": "asteroid_field", "surface": "fluid"}

    cells = fv.cells_dict_from_mining_map(
        [
            {
                "x": 8,
                "y": 8,
                "role": "occupied",
                "layout_kind": "fluid_miner",
                "r": 0,
                "surface": "fluid",
            },
            {"x": 9, "y": 8, **ext()},
            {"x": 8, "y": 9, **ext()},
            {"x": 7, "y": 8, **ext()},
            {"x": 8, "y": 7, **ext()},
            {"x": 8, "y": 3, "role": "pipe", "surface": "fluid"},
        ]
    )
    for y in range(4, 8):
        cells[(9, y)] = ast(9, y)
    for p in ((10, 8), (9, 9), (9, 7), (10, 9), (10, 7), (11, 8)):
        cells[p] = ast(p[0], p[1])
    for x in range(4, 7):
        cells[(x, 8)] = ast(x, 8)
    for y in range(4, 7):
        cells[(9, y)] = ast(9, y)
    mineable: frozenset[Coord] = frozenset((x, y) for x in range(4, 13) for y in range(0, 12))
    ex = frozenset({(9, 8), (8, 9), (7, 8), (8, 7)})
    res = try_preserve_stub_route_recovery(
        miner=(8, 8),
        extensions=ex,
        transport_kind="fluid_pipe",
        cells=cells,
        mineable=mineable,
        scratch_transport_cells=frozenset({(8, 3)}),
        scratch_blocked_cells=frozenset(),
        nearest_same_kind_transport_hops=8,
        row_r_raw=0,
    )
    assert res.accepted is True
    psr = res.trace["preserve_stub_recovery"]
    assert "B" in (psr.get("recovery_tier_attempted") or [])
    assert psr.get("bounded_bundle_rollback_success") is True
    assert psr.get("extension_carve_applied") is True
    rb = psr.get("bounded_bundle_rollback_cells") or []
    assert rb and all(tuple(c) in ex for c in rb)


def test_tier_c_two_cell_cardinal_bundle_opens_route_after_tier_b_dead_end() -> None:
    """Tier C: two-cell cardinal bundle opens corridor when Tier B 1-cell carve is stuck.

    Production ``tier_c_success_count`` is often zero because Tier C pairs are **cardinal**
    neighbors in the same extension bundle; diagonal-only L shapes enumerate no pair.
    """

    cells: dict[Coord, dict[str, object]] = {
        (10, 10): {
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 0,
            "surface": "fluid",
        },
        (11, 10): {"role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
        (12, 10): {"role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
        (15, 10): {"role": "pipe", "surface": "fluid"},
        (11, 9): {"role": "occupied", "layout_kind": "asteroid_field", "surface": "fluid"},
        (11, 11): {"role": "occupied", "layout_kind": "asteroid_field", "surface": "fluid"},
    }
    base = frozenset((x, y) for x in range(9, 18) for y in range(8, 14))
    mineable = base - {(11, 9), (11, 11)}
    ex = frozenset({(11, 10), (12, 10)})
    snap = copy.deepcopy(cells)
    res = try_preserve_stub_route_recovery(
        miner=(10, 10),
        extensions=ex,
        transport_kind="fluid_pipe",
        cells=cells,
        mineable=mineable,
        scratch_transport_cells=frozenset({(15, 10)}),
        scratch_blocked_cells=frozenset(),
        nearest_same_kind_transport_hops=8,
        row_r_raw=0,
    )
    assert cells == snap
    assert res.accepted is True
    assert res.carved_extension_cells == ex
    psr = res.trace["preserve_stub_recovery"]
    assert psr.get("tier_c_success") is True
    assert psr.get("tier_c_attempted") is True
    assert psr.get("tier_b_success") is False
    assert psr.get("tier_b_attempted") is True
    assert "C" in (psr.get("recovery_tier_attempted") or [])
    assert psr.get("bounded_bundle_rollback_success") is True
    pc = psr.get("path_cells") or []
    assert any(c == [15, 10] for c in pc)
    assert psr.get("tier_c_pair_generation_mode") == "cardinal_same_bundle_only"
    assert int(psr.get("tier_c_candidate_pair_count") or 0) > 0
    assert psr.get("tier_c_direct_stub_blocker_cells") == [[11, 10]]
    assert psr.get("tier_c_same_bundle_cardinal_neighbor_cells") == [[12, 10]]
    sample = psr.get("tier_c_candidate_pair_sample") or []
    assert isinstance(sample, list) and len(sample) >= 1
    assert len(res.carved_extension_cells) == 2


def test_tier_c_skipped_diagonal_only_extension_cluster_sets_diagnostic() -> None:
    """No cardinal same-component pair; diagonal-only extension sets diagnostic flag."""

    cells: dict[Coord, dict[str, object]] = {
        (10, 10): {
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 0,
            "surface": "fluid",
        },
        (11, 10): {"role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
        (12, 11): {"role": "occupied", "layout_kind": "fluid_extension", "surface": "fluid"},
        (15, 10): {"role": "pipe", "surface": "fluid"},
        (11, 9): {"role": "occupied", "layout_kind": "asteroid_field", "surface": "fluid"},
        (11, 11): {"role": "occupied", "layout_kind": "asteroid_field", "surface": "fluid"},
        (12, 10): {"role": "occupied", "layout_kind": "asteroid_field", "surface": "fluid"},
    }
    base = frozenset((x, y) for x in range(9, 18) for y in range(8, 14))
    mineable = base - {(11, 9), (11, 11), (12, 10)}
    ex = frozenset({(11, 10), (12, 11)})
    res = try_preserve_stub_route_recovery(
        miner=(10, 10),
        extensions=ex,
        transport_kind="fluid_pipe",
        cells=cells,
        mineable=mineable,
        scratch_transport_cells=frozenset({(15, 10)}),
        scratch_blocked_cells=frozenset(),
        nearest_same_kind_transport_hops=8,
        row_r_raw=0,
    )
    assert res.accepted is False
    psr = res.trace["preserve_stub_recovery"]
    assert psr.get("tier_c_success") is False
    assert psr.get("tier_c_skip_reason") == "tier_c_skipped_no_candidate_pairs"
    assert int(psr.get("tier_c_candidate_pair_count") or 0) == 0
    assert psr.get("tier_c_pair_generation_mode") == "cardinal_same_bundle_only"
    nd = psr.get("tier_c_no_pair_diagnostic")
    assert isinstance(nd, dict)
    assert nd.get("stub_blocker_count") == 1
    assert nd.get("blocker_has_only_diagonal_neighbors") is True
    assert nd.get("same_bundle_cardinal_neighbor_count_by_blocker", {}).get("[11,10]") == 0


def test_extension_carve_disabled_failure_preserves_telemetry_schema() -> None:
    """No free stub tier: failure path still exposes tier + rollback trace keys for NDJSON."""

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
    psr = res.trace["preserve_stub_recovery"]
    assert psr.get("rejected_reason") == "extension_carve_disabled"
    assert isinstance(psr.get("recovery_tier_attempted"), list)
    assert psr.get("output_reorientation_attempted") is False
    assert psr.get("output_reorientation_success") is False
    assert psr.get("bounded_bundle_rollback_success") is False
    assert psr.get("bounded_bundle_rollback_attempted") is True
    rb = psr.get("bounded_bundle_rollback_cells") or []
    assert isinstance(rb, list)
    ex = frozenset({(4, 3), (2, 3), (3, 2), (3, 4)})
    assert all(tuple(c) in ex for c in rb)
    last = psr.get("stub_route_probe_last")
    assert isinstance(last, dict)
    assert last.get("bfs_failure") == "no_bfs_attempt"


def test_bounded_bundle_rollback_cells_never_include_scratch_blocked() -> None:
    """Rollback cells are extensions only; scratch_blocked corridor coords are never popped."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
        final_validation as fv,
    )

    cells = fv.cells_dict_from_mining_map(
        [
            {
                "x": 8,
                "y": 8,
                "role": "occupied",
                "layout_kind": "fluid_miner",
                "r": 0,
                "surface": "fluid",
            },
            {
                "x": 9,
                "y": 8,
                "role": "occupied",
                "layout_kind": "fluid_extension",
                "surface": "fluid",
            },
            {
                "x": 8,
                "y": 9,
                "role": "occupied",
                "layout_kind": "fluid_extension",
                "surface": "fluid",
            },
            {"x": 8, "y": 3, "role": "pipe", "surface": "fluid"},
        ]
    )
    mineable: frozenset[Coord] = frozenset((x, y) for x in range(6, 12) for y in range(2, 12))
    blocked = frozenset({(8, 6)})
    ex = frozenset({(9, 8), (8, 9)})
    res = try_preserve_stub_route_recovery(
        miner=(8, 8),
        extensions=ex,
        transport_kind="fluid_pipe",
        cells=cells,
        mineable=mineable,
        scratch_transport_cells=frozenset({(8, 3)}),
        scratch_blocked_cells=blocked,
        nearest_same_kind_transport_hops=8,
        row_r_raw=0,
    )
    psr = res.trace["preserve_stub_recovery"]
    for pair in psr.get("bounded_bundle_rollback_cells") or []:
        assert tuple(pair) not in blocked
        assert tuple(pair) in ex
    if res.new_transport_coords:
        assert blocked.isdisjoint(res.new_transport_coords)


def test_try_preserve_stub_route_recovery_does_not_mutate_cells_dict() -> None:
    """Probe leaves caller ``cells`` unchanged; STEP4 owns materialized placement."""

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
    snap = copy.deepcopy(cells)
    _ = try_preserve_stub_route_recovery(
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
    assert cells == snap


def test_merge_strips_orphan_pipe_island_not_reaching_external() -> None:
    """Scratch/working orphan pipes must not survive merge when not external-reachable."""

    mineable: frozenset[Coord] = frozenset(
        {
            (5, 2),
            (5, 4),
            (5, 5),
            (5, 6),
            (6, 5),
            (10, 5),
        }
    )
    working_map: list[dict[str, object]] = [
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
        {"x": 5, "y": 4, "role": "pipe", "surface": "fluid"},
        {"x": 5, "y": 3, "role": "pipe", "surface": "fluid"},
        {"x": 5, "y": 2, "role": "pipe", "surface": "fluid"},
        # Inside layout bbox but 4-disconnected from trunk (not adjacent to external margin).
        {"x": 8, "y": 5, "role": "pipe", "surface": "fluid"},
        {"x": 9, "y": 5, "role": "pipe", "surface": "fluid"},
    ]
    final_mining_map: list[dict[str, object]] = [
        {
            "x": x,
            "y": y,
            "role": "inferred" if (x, y) == (10, 5) else "occupied",
            "layout_kind": "asteroid_field",
            "surface": "fluid",
        }
        for x, y in sorted(mineable, key=lambda p: (p[1], p[0]))
    ]
    scratch, transport_init, blocked_init = p12_tl.scratch_from_working_map(
        working_map, mineable_coords=mineable
    )
    scratch.transport_kind = "fluid_pipe"
    scratch.blocked_cells.update({(5, 5), (6, 5), (5, 6)})
    scratch.extractor_cells.add((5, 5))
    scratch.extractor_output_dirs[(5, 5)] = output_offset_r(3)
    pid = make_placement_id("pass1", 1)
    scratch.placement_records[pid] = PlacementCommitRecord(
        placement_id=pid,
        placement_pass="pass1",
        extractor_cell=(5, 5),
        extension_cells=((5, 6), (6, 5)),
        stub_cell=(5, 4),
        transport_kind="fluid_pipe",
        state=PlacementCommitState.PROVISIONAL_PLACED,
        route_id="preserve_stub_route_recovery",
    )
    scratch.next_placement_seq = 1
    combined_rows = [dict(r) for r in working_map] + [dict(r) for r in final_mining_map]
    is_ext = final_val.external_predicate_for_mining_map(combined_rows)
    merged, _stamp = p12_tl._merge_pass1_into_rows(
        working_map,
        final_mining_map,
        scratch,
        transport_init,
        blocked_init,
        mineable,
        "fluid",
        is_external=is_ext,
    )
    cells = final_val.cells_dict_from_mining_map(merged)
    assert cells[(5, 4)]["role"] == "pipe"
    assert cells.get((8, 5), {}).get("role") != "pipe"
    assert cells.get((9, 5), {}).get("role") != "pipe"
    om = final_val.orphan_transport_metrics_from_cells(cells)
    assert om["orphan_transport_count"] == 0


@override_settings(
    SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY=True,
    SHAPEZ_MINING_PASS2_FLUID_INTERNAL_FILL_ENABLED=False,
)
def test_integrate_pass12_stub_recovery_then_step4_complete_and_stub_coverage() -> None:
    """After preserve stub-route recovery, STEP4 reports full commit and stub coverage telemetry."""

    mineable_cells = [
        (5, 3),
        (5, 4),
        (5, 5),
        (5, 6),
        (6, 5),
        (10, 10),
        (6, 2),
        (7, 2),
        (8, 2),
        (9, 2),
        (10, 2),
        (10, 3),
        (10, 4),
        (10, 5),
        (10, 6),
        (10, 7),
        (10, 8),
        (10, 9),
    ]
    fm = [
        {
            "x": x,
            "y": y,
            "role": "occupied",
            "layout_kind": "asteroid_field",
            "surface": "fluid",
        }
        for x, y in mineable_cells
    ]
    wm = [
        {
            "x": 5,
            "y": 5,
            "role": "occupied",
            "layout_kind": "fluid_miner",
            "r": 3,
            "surface": "fluid",
            "t": "Layout_FluidMiner",
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
            "t": "Layout_FluidMiner",
        },
        {"x": 11, "y": 10, "role": "pipe", "surface": "fluid"},
        *[
            {"x": x, "y": y, "role": "pipe", "surface": "fluid"}
            for x, y in [
                (6, 2),
                (7, 2),
                (8, 2),
                (9, 2),
                (10, 2),
                (10, 3),
                (10, 4),
                (10, 5),
                (10, 6),
                (10, 7),
                (10, 8),
                (10, 9),
            ]
        ],
    ]
    is_ext = final_val.external_predicate_for_mining_map([dict(r) for r in wm])
    _m1, m2, stats = p12_tl.integrate_pass12_placement_into_working_map(
        working_map=wm,
        final_mining_map=fm,
        is_external=is_ext,
        existing_layout_analysis={
            "source_kind": "existing_fluid_layout",
            "equipment": {"miner_count": 2, "extension_count": 0},
            "transport": {},
            "issues": [],
        },
        suppress_pass1_pass2_loops=True,
    )
    assert stats["pass12_preserved_missing_stub_route_recovery_success_count"] >= 1
    pr = stats.get("placement_records")
    r = run_step4_merge_aware_routing(
        m2,
        final_mining_map=fm,
        is_external=is_ext,
        placement_records=pr,
    )
    assert r.complete_routing_success
    assert r.trunk_load.get("step4_stub_coverage_ok") is True
    assert r.trunk_load.get("step4_placement_fsm_finalized") is True
    rep = final_val.validate_final_mining_layout(r.map_after_routing)
    assert rep.missing_stub_count == 0
    assert rep.provisional_placed_row_count == 0
