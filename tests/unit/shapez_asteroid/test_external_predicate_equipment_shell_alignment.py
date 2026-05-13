"""§3.5 / §15: external shell axis bbox aligns with occupied equipment (not inferred-only span)."""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass12_route_probe as p12rp,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize import (
    build_final_solver_output,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_merge_routing import (
    step4_routing_skipped_result,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
    final_validation as finval,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation.final_validation_contracts import (  # noqa: E501
    FinalValidationReport,
)


def _shape_miner_row(x: int, y: int, r: int = 0) -> dict[str, Any]:
    return {
        "x": x,
        "y": y,
        "role": "occupied",
        "layout_kind": "miner",
        "surface": "shape",
        "r": r,
    }


def _inferred_row(x: int, y: int) -> dict[str, Any]:
    return {
        "x": x,
        "y": y,
        "role": "inferred",
        "layout_kind": "asteroid_field",
        "surface": "shape",
    }


def test_pass2_goals_positive_when_inferred_span_exceeds_equipment_shell() -> None:
    """Tight equipment bbox: universe edge neighbors true ``is_external``; margin and goals > 0."""

    rows: list[dict[str, Any]] = []
    cells: dict[tuple[int, int], dict[str, Any]] = {}
    mineable_set: set[tuple[int, int]] = set()
    for y in range(10, 31):
        c = (5, y)
        mineable_set.add(c)
        if y in (10, 25):
            row = _shape_miner_row(5, y)
        else:
            row = _inferred_row(5, y)
        rows.append(row)
        cells[c] = dict(row)

    mineable = frozenset(mineable_set)
    asteroid: frozenset[tuple[int, int]] = frozenset(mineable_set)
    is_external = finval.external_predicate_for_mining_map(rows)
    shell_bm = finval.external_bbox_margin_for_mining_map(rows)
    assert shell_bm is not None
    shell_bbox, shell_margin = shell_bm
    assert shell_bbox[2] == 10 and shell_bbox[3] == 25

    probe_transport = frozenset({(5, 30)})
    goals, kind, n, trace = p12rp.build_pass2_step4_aligned_routing_goals(
        transport_kind="shape_belt",
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        is_external=is_external,
        existing_layout_analysis=None,
        transport_cells_before=frozenset(),
        transport_cells_probe=probe_transport,
        blocked_for_probe=frozenset(),
        is_external_shell_bbox=shell_bbox,
        is_external_shell_margin=shell_margin,
    )
    assert kind == "first_route"
    assert n > 0
    assert trace["final_goal_count"] > 0
    assert trace["exterior_margin_cell_count"] > 0
    md = trace["pass2_external_margin_diagnostic"]
    assert int(md["sampled_neighbor_outside_universe_count"]) > 0
    br = md["sampled_neighbor_shell_breakdown"]
    assert int(br["sampled_neighbor_outside_expanded_mineable_bbox_count"]) > 0
    assert int(md["is_external_true_neighbor_sample_count"]) > 0


def test_orphan_prior_transport_not_promoted_when_external_unreachable() -> None:
    """Prior belt remains orphan under equipment shell; goals stay empty without island fallback."""

    cells: dict[tuple[int, int], dict[str, Any]] = {}
    for y in range(10, 26):
        c = (5, y)
        if y in (10, 25):
            cells[c] = dict(_shape_miner_row(5, y))
        elif y == 15:
            cells[c] = {
                "x": 5,
                "y": 15,
                "role": "belt",
                "layout_kind": "shape_belt",
                "surface": "shape",
            }
        else:
            cells[c] = dict(_inferred_row(5, y))
    mineable = frozenset((5, y) for y in range(10, 26))
    asteroid = mineable
    rows = list(cells.values())
    is_external = finval.external_predicate_for_mining_map(rows)
    shell_bm = finval.external_bbox_margin_for_mining_map(rows)
    assert shell_bm is not None
    shell_bbox, shell_margin = shell_bm
    before = frozenset({(5, 15)})
    probe = before
    goals, kind, n, trace = p12rp.build_pass2_step4_aligned_routing_goals(
        transport_kind="shape_belt",
        mineable=mineable,
        asteroid=asteroid,
        cells=cells,
        is_external=is_external,
        existing_layout_analysis=None,
        transport_cells_before=before,
        transport_cells_probe=probe,
        blocked_for_probe=frozenset(),
        is_external_shell_bbox=shell_bbox,
        is_external_shell_margin=shell_margin,
    )
    assert kind == "first_route"
    assert (5, 15) not in goals
    assert trace["external_reachable_transport_before_count"] == 0
    assert "fallback_goal_source" not in trace


def test_solver_summary_preserves_nested_pass2_external_margin_diagnostic() -> None:
    """pass12_stats → solver_summary copies ``pass2_probe_last_goal_trace`` including diagnostic."""

    empty: list[dict[str, Any]] = []
    routing_state: dict[str, Any] = {"hard_protected_corridors": []}
    step4 = step4_routing_skipped_result(empty)
    good = FinalValidationReport(
        geometry_valid=True,
        connectivity_valid=True,
        disconnected_stub_count=0,
        quarantined_unrouted_count=0,
        provisional_placed_row_count=0,
        orphan_transport_count=0,
        overlap_violation_count=0,
        missing_stub_count=0,
        missing_extractor_rotation_count=0,
        extractor_count=1,
        extension_count=0,
        transport_cell_count=0,
        transport_connectivity_ok=True,
    )
    diag = {
        "universe_scan_cell_count": 3,
        "sampled_neighbor_outside_universe_count": 1,
        "sampled_neighbor_shell_breakdown": {
            "sampled_neighbor_outside_expanded_mineable_bbox_count": 1,
        },
        "pass2_external_margin_diagnostic_contract": True,
    }
    pass12_stats: dict[str, Any] = {
        "pass12_merged_seed_miner_count": 1,
        "pass12_preserved_bundle_extractor_cells": 1,
        "pass12_preserved_missing_stub_drop_extractor_count": 0,
        "pass2_probe_last_goal_trace": {
            "final_goal_count": 2,
            "pass2_external_margin_diagnostic": diag,
        },
    }
    with patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline.finalize."
        "_validate_final_mining_layout",
        return_value=good,
    ):
        _out, summary = build_final_solver_output(
            run_id="ext-margin-diag-summary",
            map_timeline=[{"mining_map": empty}, {"mining_map": empty}],
            map_after_pass1=empty,
            map_after_pass2=empty,
            map_after_routing=empty,
            map_final=empty,
            pass12_status_fields={},
            pass12_stats=pass12_stats,
            pass12_phase="test",
            pass12_skipped=True,
            pre_counts={"extractors": 0, "extensions": 0, "transport_cells": 0},
            post_pass2_counts={"extractors": 0, "extensions": 0, "transport_cells": 0},
            step4_result=step4,
            routing_state_summary=routing_state,
            post_step4_counts={"extractors": 0, "extensions": 0, "transport_cells": 0},
            unfinalized_placement_count=0,
            pass3_summary={"after_internal_transport_count": 0, "pass3_skipped": True},
            existing_layout_analysis=None,
            step_hash_step4=None,
            step_hash_pass3=None,
            step_hash_p4=None,
            solver_state_hash=None,
            replay_events=[],
            debug_location="tests.unit.shapez_asteroid.test_external_predicate_equipment_shell",
        )
    gtrace = summary.get("pass2_probe_last_goal_trace") or {}
    assert isinstance(gtrace, dict)
    assert gtrace.get("pass2_external_margin_diagnostic") == diag
    assert _out["solver_summary"]["pass2_probe_last_goal_trace"]["pass2_external_margin_diagnostic"]
