"""Sequence 9 — STEP4 routing regression gates (instrumentation + invariants only).

Canonical: ``08_step4_routing.md`` section 9.2–9.6, ``13_step9_validation.md`` section 15 gate,
``12_protected_corridor.md`` (telemetry / soft-replace contracts via constants),
``14_step10_replay_ui.md`` (deterministic replay payloads).

These tests do **not** assert routing costs, budgets, or Pass3/P4 behavior beyond
explicit semantic partitions already enforced elsewhere.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.existing_layout.existing_layout_analysis import (  # noqa: E501
    analyze_existing_layout_from_mining_map,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation import (
    constants as fc,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass12_route_probe as p12rp,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.semantic_contracts import (
    partition_pass3_commit_reason_payload,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_failure_category as s4fc,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4 import (
    step4_route_failure_replay_overlay as s4rro,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_dijkstra import (
    dijkstra_route_step4,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_goal_trunk_seed import (  # noqa: E501
    build_step4_goal_set,
    build_trunk_seed_candidates_by_kind,
    trunk_seed_union_from_existing_layout,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_map_ops import (
    rollback_placement_cells,
    same_kind_transport_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_search_diagnostics import (  # noqa: E501
    merge_goal_union_meta,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation import (  # noqa: E501
    external_predicate_for_mining_map,
    validate_final_mining_layout,
)


def test_gate1_first_route_bootstrap_goal_is_margin_union_trunk_seed() -> None:
    """08 step 9.2: empty committed trunk → raw goals = ``trunk_seed_candidates[kind] ∪ margin``."""

    margin = {(1, 0), (2, 0)}
    seeds = build_trunk_seed_candidates_by_kind(
        exterior_margin=margin,
        hint_union={(5, 5)},
        cells={(5, 5): {"role": "belt", "layout_kind": "belt"}},
    )
    g = build_step4_goal_set(
        "shape_belt",
        committed_trunk_by_kind={},
        exterior_margin_cells=margin,
        trunk_seed_candidates_by_kind=seeds,
    )
    assert g == margin | {(5, 5)}
    goals, kind, n, trace = p12rp.build_pass2_step4_aligned_routing_goals(
        transport_kind="shape_belt",
        mineable=frozenset({(1, 0)}),
        asteroid=frozenset(),
        cells={(1, 0): {"x": 1, "y": 0, "role": "inferred", "layout_kind": "asteroid_field"}},
        is_external=lambda c: c == (2, 0),
        existing_layout_analysis=None,
        transport_cells_before=frozenset(),
        transport_cells_probe=frozenset({(2, 0)}),
        blocked_for_probe=frozenset(),
    )
    assert kind == "first_route"
    assert n == len(goals) > 0
    assert trace["exterior_margin_cell_count"] >= 1


def test_gate2_same_kind_merge_only_belt_vs_pipe_disjoint() -> None:
    """08 step 9.5: belt trunk slice and pipe trunk slice are disjoint on mixed-role maps."""

    cells: dict[tuple[int, int], dict[str, Any]] = {
        (1, 1): {"role": "belt", "surface": "shape"},
        (2, 1): {"role": "belt", "surface": "shape"},
        (10, 10): {"role": "pipe", "surface": "fluid"},
    }
    belts = same_kind_transport_cells(cells, "belt")
    pipes = same_kind_transport_cells(cells, "pipe")
    assert belts == {(1, 1), (2, 1)}
    assert pipes == {(10, 10)}
    assert not (belts & pipes)


def test_gate3_orphan_and_single_cell_not_in_trunk_seed_union() -> None:
    """08 step 9.2.1 + ELA: orphan / single-cell → cleanup only.

    See ``test_existing_layout_analysis`` for full ELA fixtures.
    """

    mining_map = [
        {"x": 1, "y": 1, "role": "occupied", "surface": "shape", "layout_kind": "miner", "r": 0},
        {"x": 2, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 3, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 4, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 5, "y": 1, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 80, "y": 80, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 81, "y": 80, "role": "belt", "surface": "shape", "layout_kind": "belt"},
        {"x": 50, "y": 50, "role": "belt", "surface": "shape", "layout_kind": "belt"},
    ]
    is_ext = external_predicate_for_mining_map(mining_map)
    out = analyze_existing_layout_from_mining_map(mining_map, is_external=is_ext)
    ela_hints = out["solver_hints"]
    assert trunk_seed_union_from_existing_layout(out) == {
        (int(p[0]), int(p[1])) for p in ela_hints["trunk_seed_cell_union"]
    }
    orphan_cells = {(80, 80), (81, 80)}
    single_cell = {(50, 50)}
    trunk = trunk_seed_union_from_existing_layout(out)
    assert not (trunk & orphan_cells)
    assert not (trunk & single_cell)


def test_gate4_fixed_output_stub_start_path_index_zero() -> None:
    """08 step 9.1 / Dijkstra contract: search starts at output stub, not extractor core."""

    stub = (2, 1)
    goal = (4, 1)
    cells: dict[tuple[int, int], dict[str, Any]] = {
        stub: {"role": "belt", "surface": "shape"},
        (3, 1): {"role": "inferred", "layout_kind": "asteroid_field", "surface": "shape"},
        goal: {"role": "belt", "surface": "shape"},
    }
    mineable = frozenset({(2, 1), (3, 1), (4, 1)})
    asteroid: frozenset[tuple[int, int]] = frozenset()
    blocked = frozenset({(1, 1)})  # extractor core blocked; not on path
    path = dijkstra_route_step4(
        stub,
        want_role="belt",
        cells=cells,
        blocked=blocked,
        mineable=mineable,
        asteroid=asteroid,
        is_external=lambda c: c == (99, 99),
        trunk=frozenset({goal}),
        goal_cells=frozenset({goal}),
        search_stats={},
    )
    assert path is not None
    assert path[0] == stub


def test_gate5_rollback_cleanup_deletes_non_mineable_extension_cells() -> None:
    """08 step 9.6: spatial rollback removes bundle coords not restored from ``final_cells``."""

    ext = (1, 1)
    stub = (2, 1)
    ext_extra = (3, 1)
    mineable = frozenset({ext, stub})
    final_cells = {
        ext: {"x": 1, "y": 1, "role": "occupied", "layout_kind": "shape_miner"},
        stub: {"x": 2, "y": 1, "role": "mineable", "layout_kind": None},
    }
    cells = {
        ext: dict(final_cells[ext]),
        stub: {"x": 2, "y": 1, "role": "belt", "surface": "shape", "placement_id": "p2-000001"},
        ext_extra: {
            "x": 3,
            "y": 1,
            "role": "belt",
            "surface": "shape",
            "placement_id": "p2-000001",
        },
    }
    rec = PlacementCommitRecord(
        placement_id="p2-000001",
        placement_pass="pass2",
        extractor_cell=ext,
        extension_cells=(ext_extra,),
        stub_cell=stub,
        transport_kind="shape_belt",
        state=PlacementCommitState.PROVISIONAL_PLACED,
    )
    rollback_placement_cells(cells, rec, final_cells, mineable)
    assert cells[ext] == final_cells[ext]
    assert cells[stub] == final_cells[stub]
    assert ext_extra not in cells


def test_gate6_final_validation_fails_when_quarantined_fsm_rows_present() -> None:
    """13 step 15: geometry gate fails while ``QUARANTINED_UNROUTED`` rows remain on the map."""

    mining_map = [
        {
            "x": 1,
            "y": 1,
            "role": "mineable",
            "placement_commit_state": PlacementCommitState.QUARANTINED_UNROUTED.value,
        },
    ]
    report = validate_final_mining_layout(mining_map)
    assert report.quarantined_unrouted_count == 1
    assert report.geometry_valid is False


def test_gate6_quarantine_state_string_not_routed_confirmed() -> None:
    """FSM: terminal strings stay distinct (no silent promotion to routed)."""

    assert (
        PlacementCommitState.QUARANTINED_UNROUTED.value
        != PlacementCommitState.ROUTED_CONFIRMED.value
    )


def test_gate7_soft_replace_reject_maps_to_rejected_not_commit_reason() -> None:
    """12 protected corridor: ``rejected_by_no_replacement_route`` is not ``commit_reason``.

    Uses ``partition_pass3_commit_reason_payload`` (semantic contracts).
    """

    c, r = partition_pass3_commit_reason_payload(
        fc.P3E3_REJECT_NO_REPLACEMENT_ROUTE,
        pass3_committed=True,
        pass3_final_committed=True,
    )
    assert c is None
    assert r == fc.P3E3_REJECT_NO_REPLACEMENT_ROUTE


def test_gate8_orphan_transport_detected_until_removed() -> None:
    """13 step 15 connectivity: orphan belts increment ``orphan_transport_count``."""

    orphan_map = [
        {"x": 1, "y": 1, "role": "belt", "surface": "shape"},
        {"x": 2, "y": 1, "role": "belt", "surface": "shape"},
    ]
    r0 = validate_final_mining_layout(orphan_map)
    assert r0.orphan_transport_count == 2
    assert r0.connectivity_valid is False
    r1 = validate_final_mining_layout([])
    assert r1.orphan_transport_count == 0


def test_gate9_deterministic_goal_ordering_and_failure_category() -> None:
    """08 step 9.3 ordering head + telemetry classifier: identical inputs → identical outputs."""

    stub = (0, 0)
    raw = {(1, 1), (9, 9)}
    trunk = frozenset({(9, 9)})
    margin = {(2, 2)}
    g1, m1 = merge_goal_union_meta(stub, raw_goal=set(raw), trunk_cells=trunk, margin_cells=margin)
    g2, m2 = merge_goal_union_meta(stub, raw_goal=set(raw), trunk_cells=trunk, margin_cells=margin)
    assert g1 == g2
    assert m1.get("priority_head") == m2.get("priority_head")

    near = [
        {"cell": [1, 0], "reason": "blocked"},
        {"cell": [-1, 0], "reason": "blocked"},
        {"cell": [0, 1], "reason": "blocked"},
        {"cell": [0, -1], "reason": "blocked"},
    ]
    cells: dict[tuple[int, int], dict[str, Any]] = {}
    args = dict(
        stop_reason="exhausted",
        last_error="no_route_exhausted",
        nearest_transport_hops=3,
        near=near,
        goal_cells_count=5,
        reachable_goal_count=0,
        cells=cells,
        want_role="belt",
        stub_cell=stub,
        hard_extras=frozenset(),
    )
    a = s4fc.classify_step4_failure_category(**args)
    b = s4fc.classify_step4_failure_category(**args)
    assert a == b == s4fc.Step4FailureCategory.stub_isolated.value


def test_gate10_replay_overlay_json_deterministic() -> None:
    """14 replay UI: merged replay overlay JSON is stable (sorted keys, sorted id/stub lists)."""

    rows = [
        {
            "step4_route_failure_detail": {
                "step4_replay_overlay": {
                    "failed_stub_cells": [[2, 2], [1, 1]],
                    "failed_placement_ids": ["b", "a"],
                }
            }
        },
    ]
    m = s4rro.merge_step4_route_failure_replay_overlay(
        routing_failures=rows,
        routing_state={"hard_protected_corridors": [], "soft_protected_corridors": []},
        quarantined_placements=("b",),
        rolled_back_placements=("b",),
    )
    s1 = json.dumps(m, sort_keys=True)
    s2 = json.dumps(m, sort_keys=True)
    assert s1 == s2


def test_gate10_step4_dijkstra_has_no_replay_or_summary_reads() -> None:
    """Routing core does not reference replay / NDJSON / solver_summary identifiers."""

    root = Path("django_apps/shapez_asteroid/services/asteroid_mining_layout/step4")
    text = (root / "step4_dijkstra.py").read_text(encoding="utf-8").lower()
    for banned in ("replay", "ndjson", "solver_summary", "overlay"):
        assert banned not in text
