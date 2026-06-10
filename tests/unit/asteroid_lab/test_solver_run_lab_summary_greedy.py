"""Lab summary cards for integrated rim greedy."""

from __future__ import annotations

from django_apps.asteroid_lab.services.solver_run_lab_summary import (
    lab_run_summary_from_solver_summary,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_04_INNER_PATTERN_FILL,
    LAYER_05_TRANSPORT_ROUTING,
)


def test_greedy_layer03_shows_completed_with_greedy_highlights() -> None:
    row = lab_run_summary_from_solver_summary(
        run_id=1,
        status="completed",
        solver_summary={
            "stack_run_status": "success",
            "completed_layer_slugs": [
                "layer_01_reconstruction",
                "layer_02_exterior_transport",
                LAYER_03_RIM_GREEDY_PLACEMENT,
            ],
            "rim_anchor_count": 81,
            "rim_greedy_committed_count": 12,
            "rim_greedy_rejected_count": 40,
            "rim_greedy_winning_variant_id": "CW_TL",
            "rim_greedy_pass2_score": 18.5,
            "field_route_cell_count_total": 120,
            "rim_greedy_total_route_length": 90,
            "layer03_skip_reason": "none",
            "layer03_reject_reason_counts": [("EQUIPMENT_COLLISION", 25), ("DPS_UNREACHABLE", 15)],
            "layer04_selected_count": 12,
        },
    )
    layers = {layer["layer_slug"]: layer for layer in row["layer_summaries"]}
    l3 = layers[LAYER_03_RIM_GREEDY_PLACEMENT]
    assert l3["outcome"] == "completed"
    assert l3["title"] == "Rim greedy placement"
    labels = {h["label"]: h["value"] for h in l3["highlights"]}
    assert labels["Committed placements"] == "12"
    assert labels["Top reject reasons"] == "EQUIPMENT COLLISION: 25; DPS UNREACHABLE: 15"
    assert "Layer skip reason" not in labels
    assert "Total route length" not in labels

    l4 = layers[LAYER_04_INNER_PATTERN_FILL]
    assert l4["outcome"] == "pending"
    assert l4["title"] == "Inner pattern fill"
    l5 = layers[LAYER_05_TRANSPORT_ROUTING]
    assert l5["outcome"] == "pending"
    assert l5["title"] == "Transport routing"


def test_greedy_layer04_inner_fill_highlights_read_nested_cli_layer_summaries() -> None:
    row = lab_run_summary_from_solver_summary(
        run_id=3,
        status="completed",
        solver_summary={
            "stack_run_status": "success",
            "completed_layer_slugs": [
                LAYER_03_RIM_GREEDY_PLACEMENT,
                LAYER_04_INNER_PATTERN_FILL,
            ],
            "rim_greedy_winning_variant_id": "CW_TL",
            "layer_summaries": [
                {
                    "layer_slug": LAYER_04_INNER_PATTERN_FILL,
                    "outcome": "completed",
                    "metrics": {
                        "interior_occupied_cell_count": 9,
                        "coverage_ratio": 0.692,
                        "interior_candidate_count": 13,
                        "layer_skip_reason": "none",
                    },
                }
            ],
        },
    )
    l4 = {layer["layer_slug"]: layer for layer in row["layer_summaries"]}[
        LAYER_04_INNER_PATTERN_FILL
    ]
    assert l4["outcome"] == "completed"
    labels = {h["label"]: h["value"] for h in l4["highlights"]}
    assert labels["Interior occupied cells"] == "9"
    assert labels["Coverage ratio"] == "69.2%"
    assert labels["Interior candidates"] == "13"
    assert "Macro-only mode" not in labels
    assert "Layer skip reason" not in labels


def test_greedy_layer04_transport_completed_highlights() -> None:
    row = lab_run_summary_from_solver_summary(
        run_id=2,
        status="completed",
        solver_summary={
            "stack_run_status": "success",
            "completed_layer_slugs": [
                "layer_01_reconstruction",
                "layer_02_exterior_transport",
                LAYER_03_RIM_GREEDY_PLACEMENT,
                LAYER_05_TRANSPORT_ROUTING,
            ],
            "layer_summaries": [
                {
                    "layer_slug": LAYER_05_TRANSPORT_ROUTING,
                    "outcome": "completed",
                    "metrics": {
                        "transport_kind": "space_belt",
                        "source_count": 12,
                        "routed_source_count": 11,
                        "failed_source_count": 1,
                        "route_count": 11,
                        "group_count": 3,
                        "transport_tile_count": 84,
                        "total_route_cells": 120,
                        "failure_reasons": ["capacity_overflow"],
                    },
                },
            ],
        },
    )
    l5 = {layer["layer_slug"]: layer for layer in row["layer_summaries"]}[
        LAYER_05_TRANSPORT_ROUTING
    ]
    assert l5["outcome"] == "completed"
    labels = {h["label"]: h["value"] for h in l5["highlights"]}
    assert labels["Transport kind"] == "space belt"
    assert labels["Sources routed"] == "11 / 12"
    assert labels["Transport tiles"] == "84"
    assert labels["Failure reasons"] == "Capacity overflow"
