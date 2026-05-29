"""L3/L4 rim stack runtime merge tests."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import (
    Layer03ExpansionMetrics,
    Layer03SkipReason,
)
from django_apps.asteroid_lab.layers.contracts.layer_slugs import (
    LAYER_03_RIM_MINING_BUNDLES,
    LAYER_04_RIM_BUNDLE_PLACEMENT,
)
from django_apps.asteroid_lab.layers.contracts.provisional_overlay import (
    ProvisionalLayoutOverlay,
)
from django_apps.asteroid_lab.layers.contracts.rim_placement import (
    build_layer04_rim_placement_result,
)
from django_apps.asteroid_lab.services.solver_runtime_rim_stack import (
    merge_rim_stack_into_solver_summary,
)


def test_merge_rim_stack_into_solver_summary() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import (
        build_rim_bundle_candidate_set,
    )

    layer03 = build_rim_bundle_candidate_set(
        normal_candidates=(),
        diagnostic_rejected_candidates=(),
        metrics=Layer03ExpansionMetrics(
            rim_anchor_count=81,
            seed_projection_attempt_count=0,
            local_geometry_rejected_count=0,
            route_probe_attempt_count=90,
            route_probe_succeeded_count=45,
            route_probe_failed_count=0,
            dedupe_duplicate_count=0,
            normal_candidate_count=0,
            diagnostic_rejected_count=0,
            budget_skipped_count=0,
            layer_skip_reason=Layer03ExpansionMetrics.empty().layer_skip_reason,
        ),
    )
    overlay = ProvisionalLayoutOverlay.empty()
    layer04 = build_layer04_rim_placement_result(
        selected_placements=(),
        rejected_candidates=(),
        provisional_overlay=overlay,
        replay_frames=(),
    )
    summary: dict[str, object] = {
        "completed_layer_slugs": ["layer_01_reconstruction", "layer_02_exterior_transport"],
    }
    merge_rim_stack_into_solver_summary(summary, layer03=layer03, layer04=layer04)
    assert summary["route_probe_succeeded_count"] == 45
    assert summary["normal_candidate_count"] == 0
    assert summary["layer04_selected_count"] == 0
    assert LAYER_03_RIM_MINING_BUNDLES in summary["completed_layer_slugs"]
    assert LAYER_04_RIM_BUNDLE_PLACEMENT in summary["completed_layer_slugs"]


def test_merge_rim_stack_hold_skips_completed_slugs() -> None:
    from django_apps.asteroid_lab.layers.contracts.candidates import (
        build_rim_bundle_candidate_set,
    )

    layer03 = build_rim_bundle_candidate_set(
        normal_candidates=(),
        diagnostic_rejected_candidates=(),
        metrics=Layer03ExpansionMetrics(
            rim_anchor_count=81,
            seed_projection_attempt_count=0,
            local_geometry_rejected_count=0,
            route_probe_attempt_count=0,
            route_probe_succeeded_count=0,
            route_probe_failed_count=0,
            dedupe_duplicate_count=0,
            normal_candidate_count=0,
            diagnostic_rejected_count=0,
            budget_skipped_count=0,
            layer_skip_reason=Layer03SkipReason.EMPTY_MINER_SEED_CATALOG,
        ),
    )
    overlay = ProvisionalLayoutOverlay.empty()
    layer04 = build_layer04_rim_placement_result(
        selected_placements=(),
        rejected_candidates=(),
        provisional_overlay=overlay,
        replay_frames=(),
    )
    summary: dict[str, object] = {
        "completed_layer_slugs": [
            "layer_01_reconstruction",
            "layer_02_exterior_transport",
            LAYER_03_RIM_MINING_BUNDLES,
            LAYER_04_RIM_BUNDLE_PLACEMENT,
        ],
    }
    merge_rim_stack_into_solver_summary(summary, layer03=layer03, layer04=layer04)
    assert summary["layer03_skip_reason"] == "empty_miner_seed_catalog"
    assert LAYER_03_RIM_MINING_BUNDLES not in summary["completed_layer_slugs"]
    assert LAYER_04_RIM_BUNDLE_PLACEMENT not in summary["completed_layer_slugs"]
