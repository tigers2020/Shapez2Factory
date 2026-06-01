"""Lab summary cards for integrated rim greedy."""

from __future__ import annotations

from django_apps.asteroid_lab.services.solver_run_lab_summary import (
    lab_run_summary_from_solver_summary,
)
from shapez2_factory.application.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_03_RIM_GREEDY_PLACEMENT,
    LAYER_04_RIM_BUNDLE_PLACEMENT,
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
    assert labels["Top reject reasons"] == "EQUIPMENT_COLLISION: 25; DPS_UNREACHABLE: 15"

    l4 = layers[LAYER_04_RIM_BUNDLE_PLACEMENT]
    assert l4["outcome"] == "superseded"
