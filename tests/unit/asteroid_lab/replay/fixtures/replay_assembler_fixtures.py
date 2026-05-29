"""Fixtures for central solver runtime replay assembler tests."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import (
    Layer03ExpansionMetrics,
    Layer03SkipReason,
    RimBundleCandidateSet,
)
from django_apps.asteroid_lab.layers.contracts.layer_budget import LayerBudgetContext
from django_apps.asteroid_lab.layers.contracts.rim_placement import Layer04RimPlacementResult
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.wire import (
    exterior_connector_plan_to_metrics_dict,
)
from django_apps.asteroid_lab.layers.layer_03_rim_mining_bundles.expand import (
    expand_rim_bundle_candidates,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType
from django_apps.asteroid_lab.replay.timeline_dtos import ReplayMapView
from django_apps.asteroid_lab.replay.timeline_serialization import replay_map_view_from_json_dict
from tests.unit.asteroid_lab.layers.fixtures.layer_03_candidate_set_factory import (
    rim_bundle_candidate_set_for_test,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
    two_seed_catalog,
)


def reconstruction_complete_lab_frame_dict_for_golden() -> dict[str, object]:
    """Minimal renderable reconstruction.completed wire for golden 5×5 map."""
    complete = golden_5x5_complete_map()
    rows = [
        {
            "x": x,
            "y": y,
            "kind": "asteroid_shape_field",
            "transport": "",
            "rotation": 0,
        }
        for x, y in sorted(complete.field_cells)
    ]
    xs = [int(r["x"]) for r in rows]
    ys = [int(r["y"]) for r in rows]
    return {
        "frame_index": 0,
        "event_type": ReplayEventType.RECONSTRUCTION_COMPLETED.value,
        "phase": "reconstruction",
        "map_view": {
            "full_cells": rows,
            "overlay_cells": [],
            "cell_delta": [],
            "annotations": [],
            "bbox": {
                "min_x": min(xs),
                "min_y": min(ys),
                "max_x": max(xs),
                "max_y": max(ys),
            },
        },
        "metrics": {},
    }


def exterior_plan_wire_for_golden() -> dict[str, object]:
    metrics = exterior_connector_plan_to_metrics_dict(minimal_l2_plan_for_golden())
    wire = metrics["exterior_connector_plan"]
    if not isinstance(wire, dict):
        msg = "exterior_connector_plan wire must be a dict"
        raise TypeError(msg)
    return wire


def renderable_base_map_view_for_golden() -> ReplayMapView:
    raw_map_view = reconstruction_complete_lab_frame_dict_for_golden()["map_view"]
    if not isinstance(raw_map_view, dict):
        msg = "map_view must be a dict"
        raise TypeError(msg)
    return replay_map_view_from_json_dict(raw_map_view)


def golden_complete_map() -> ReconstructionCompleteMap:
    return golden_5x5_complete_map()


def rim_bundle_candidate_set_missing_exterior_plan() -> RimBundleCandidateSet:
    metrics = Layer03ExpansionMetrics(
        rim_anchor_count=0,
        seed_projection_attempt_count=0,
        local_geometry_rejected_count=0,
        route_probe_attempt_count=0,
        route_probe_succeeded_count=0,
        route_probe_failed_count=0,
        dedupe_duplicate_count=0,
        normal_candidate_count=0,
        diagnostic_rejected_count=0,
        budget_skipped_count=0,
        layer_skip_reason=Layer03SkipReason.MISSING_EXTERIOR_CONNECTION_PLAN,
    )
    return rim_bundle_candidate_set_for_test(
        normal_candidates=(),
        diagnostic_rejected_candidates=(),
        metrics=metrics,
    )


def rim_bundle_candidate_set_with_observability_for_golden() -> RimBundleCandidateSet:
    return expand_rim_bundle_candidates(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
        seed_catalog=two_seed_catalog(),
    )


def layer04_result_with_selection_for_golden() -> Layer04RimPlacementResult:
    from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.run import (
        run_layer_04_rim_bundle_placement,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_03_candidate_set_factory import (
        rim_bundle_candidate_set_for_test,
    )
    from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
        succeeded_probe_at,
    )

    entry = succeeded_probe_at((6, 4))
    candidate_set = rim_bundle_candidate_set_for_test(
        normal_candidates=(entry,),
        diagnostic_rejected_candidates=(),
        metrics=Layer03ExpansionMetrics(
            rim_anchor_count=1,
            seed_projection_attempt_count=0,
            local_geometry_rejected_count=0,
            route_probe_attempt_count=1,
            route_probe_succeeded_count=1,
            route_probe_failed_count=0,
            dedupe_duplicate_count=0,
            normal_candidate_count=1,
            diagnostic_rejected_count=0,
            budget_skipped_count=0,
            layer_skip_reason=Layer03ExpansionMetrics.empty().layer_skip_reason,
        ),
    )
    return run_layer_04_rim_bundle_placement(
        complete_map=golden_5x5_complete_map(),
        exterior_plan=minimal_l2_plan_for_golden(),
        candidate_set=candidate_set,
        budget_ctx=LayerBudgetContext.from_budget_ms(60_000, now_fn=lambda: 0.0),
    )
