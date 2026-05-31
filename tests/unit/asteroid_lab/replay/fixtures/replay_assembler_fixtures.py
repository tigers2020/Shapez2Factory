"""Fixtures for central solver runtime replay assembler tests."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.candidates import (
    Layer03ExpansionMetrics,
    Layer03SkipReason,
    RimBundleCandidateSet,
    RouteProbedBundleCandidate,
)
from django_apps.asteroid_lab.layers.contracts.rim_placement import Layer04RimPlacementResult
from django_apps.asteroid_lab.layers.layer_02_exterior_transport.wire import (
    exterior_connector_plan_to_metrics_dict,
)
from django_apps.asteroid_lab.reconstruction.complete_map import ReconstructionCompleteMap
from django_apps.asteroid_lab.replay.replay_enums import ReplayEventType
from django_apps.asteroid_lab.replay.timeline_dtos import ReplayMapView
from django_apps.asteroid_lab.replay.timeline_serialization import replay_map_view_from_json_dict
from tests.unit.asteroid_lab.layers.fixtures.layer_03_candidate_set_factory import (
    rim_bundle_candidate_set_for_test,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_03_golden_map import (
    expected_golden_rim_anchor_count,
    golden_5x5_complete_map,
    minimal_l2_plan_for_golden,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    layer04_rim_placement_result_for_probes,
    succeeded_probe_at,
)


def reconstruction_complete_lab_frame_dict_for_golden() -> dict[str, object]:
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


def _compact_probe(
    anchor: tuple[int, int],
    *,
    equivalence_key: str,
    rank: int,
) -> RouteProbedBundleCandidate:
    stub = (anchor[0] + 1, anchor[1])
    goal = (stub[0] + 1, stub[1])
    return succeeded_probe_at(
        anchor,
        equivalence_key=equivalence_key,
        rank=rank,
        mining=frozenset({anchor}),
        transport=frozenset({stub}),
        goal=goal,
    )


def rim_bundle_candidate_set_with_observability_for_golden() -> RimBundleCandidateSet:
    probes = (
        _compact_probe((6, 4), equivalence_key="equiv_a", rank=1),
        _compact_probe((4, 6), equivalence_key="equiv_b", rank=2),
        _compact_probe((6, 2), equivalence_key="equiv_c", rank=3),
        _compact_probe((2, 6), equivalence_key="equiv_d", rank=4),
    )
    metrics = Layer03ExpansionMetrics(
        rim_anchor_count=expected_golden_rim_anchor_count(),
        seed_projection_attempt_count=2,
        local_geometry_rejected_count=0,
        route_probe_attempt_count=len(probes),
        route_probe_succeeded_count=len(probes),
        route_probe_failed_count=0,
        dedupe_duplicate_count=0,
        normal_candidate_count=len(probes),
        diagnostic_rejected_count=0,
        budget_skipped_count=0,
        layer_skip_reason=Layer03SkipReason.NONE,
    )
    return rim_bundle_candidate_set_for_test(
        normal_candidates=probes,
        diagnostic_rejected_candidates=(),
        metrics=metrics,
    )


def layer04_result_with_selection_for_golden() -> Layer04RimPlacementResult:
    return layer04_rim_placement_result_for_probes((succeeded_probe_at((6, 4)),))
