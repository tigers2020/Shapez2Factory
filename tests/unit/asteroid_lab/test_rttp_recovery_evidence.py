"""A0 — RTTP core recovery evidence extraction (read-only; not solver input)."""

from __future__ import annotations

from django_apps.asteroid_lab.services.rttp_recovery_evidence import (
    build_recovery_evidence_row,
    count_exterior_connected_route_cells,
    evaluate_gate_a_from_row,
    extract_overlay_connectivity_metrics,
)


def test_count_exterior_connected_route_cells_requires_trunk_touch() -> None:
    route = frozenset({(0, 0), (1, 0), (2, 0)})
    trunk = frozenset({(2, 0)})
    assert count_exterior_connected_route_cells(route, trunk) == 3


def test_count_exterior_connected_zero_when_route_disjoint_from_trunk() -> None:
    route = frozenset({(0, 0), (1, 0)})
    trunk = frozenset({(10, 10)})
    assert count_exterior_connected_route_cells(route, trunk) == 0


def test_extract_overlay_connectivity_metrics_from_commit_overlay() -> None:
    overlay = {
        "cells": [
            {
                "x": 1,
                "y": 2,
                "kind": "route.committed_path",
                "overlay_semantic_kind": "route.committed_path",
            },
            {
                "x": 2,
                "y": 2,
                "kind": "placement.confirmed_fixed_output_transport",
                "overlay_semantic_kind": "placement.confirmed_fixed_output_transport",
            },
        ]
    }
    trunk_overlay = {
        "cells": [
            {
                "x": 1,
                "y": 2,
                "kind": "route_domain.preferred",
                "overlay_semantic_kind": "route_domain.preferred",
            },
        ]
    }
    metrics = extract_overlay_connectivity_metrics(
        commit_overlay=overlay,
        route_domain_overlay=trunk_overlay,
    )
    assert metrics["committed_route_cell_count"] == 1
    assert metrics["committed_output_transport_cells"] == 1
    assert metrics["exterior_connected_route_count"] == 1


def test_build_recovery_evidence_row_from_solver_summary() -> None:
    summary = {
        "validation_passed": False,
        "confirmed_count": 23,
        "issue_codes": ["rttp_validation_failed"],
        "algorithm_steps": [
            {
                "step_id": "rttp.commit",
                "passed": False,
                "metrics": {
                    "committed_ids": ["a", "b"],
                    "visible_miner_cell_count": 23,
                    "visible_extension_cell_count": 0,
                },
            }
        ],
        "reconstruction_capacity": {"shape_field_cell_count": 583},
        "placement_goal_plan": {"placement_goal_count": 32},
    }
    row = build_recovery_evidence_row(
        slug="rttp-cert-candidate-recon-l0",
        project_id=1,
        solver_run_id=999,
        run_key="rttp-test",
        solver_summary=summary,
        trunk_mask_cells=frozenset(),
        replay_overlay_metrics={
            "committed_output_transport_cells": 0,
            "committed_route_cell_count": 0,
            "exterior_connected_route_count": 0,
            "trunk_mask_cell_count_overlay": 0,
        },
    )
    assert row["committed_extractor_count"] == 2
    assert row["installable_shape_field_cell_count"] == 583
    assert row["visible_extension_cell_count"] == 0
    assert row["validation_passed"] is False
    assert row["gate_a_passed"] is False
    assert row["first_failing_stage"] == "S2"
    assert "missing_extensions" in row["diagnostic_flags"]
    assert "route_materialization_missing" in row["diagnostic_flags"]


def test_gate_a_requires_transport_and_exterior_not_commit_count_only() -> None:
    row_high_commit_no_transport = {
        "committed_extractor_count": 23,
        "committed_output_transport_cells": 0,
        "committed_route_cell_count": 0,
        "exterior_connected_route_count": 0,
        "validation_passed": True,
    }
    assert evaluate_gate_a_from_row(row_high_commit_no_transport) is False
