"""Layer 04 runtime replay segment tests (transient specs; assembler composes overlays)."""

from __future__ import annotations

from django_apps.asteroid_lab.genetic_sample.enums import Direction
from django_apps.asteroid_lab.layers.contracts.rim_placement import (
    Layer04PackingObservability,
    RimPlacementRejection,
    RimPlacementRejectReason,
)
from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_LAYER04_RIM_CANDIDATE_SELECTED,
    EVENT_TYPE_LAYER04_RIM_PLACEMENT_BEGIN,
    EVENT_TYPE_LAYER04_RIM_PLACEMENT_COMPLETE,
    is_registered_event_type,
)
from django_apps.asteroid_lab.replay.layer04_segment import (
    OVERLAY_KIND_ROUTE_PROBE_PATH,
    build_layer04_runtime_segment_specs,
)
from django_apps.asteroid_lab.replay.replay_limits import (
    MAX_LAYER04_REPLAY_REJECTED_OVERLAP,
    MAX_LAYER04_REPLAY_SELECTED,
)
from django_apps.asteroid_lab.replay.runtime_frame_finalize import (
    finalize_specs_to_timeline_frames,
    transient_overlay_cells_to_wire,
)
from django_apps.asteroid_lab.replay.timeline_dtos import replay_map_view_is_renderable
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    rim_bundle_placement_from_probe,
    succeeded_probe_at,
)
from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
    renderable_base_map_view_for_golden,
)


def _frames_from_specs(*, selected, rejected, packing_observability=None):
    base_map_view = renderable_base_map_view_for_golden()
    specs = build_layer04_runtime_segment_specs(
        selected=selected,
        rejected=rejected,
        packing_observability=packing_observability,
    )
    return finalize_specs_to_timeline_frames(
        specs,
        structural_map_view=base_map_view,
    )


def test_layer04_selected_overlay_includes_route_probe_path_not_space_belt() -> None:
    placement = rim_bundle_placement_from_probe(
        succeeded_probe_at(
            (3, -10),
            output_dir=Direction.N,
            transport=frozenset({(3, -9)}),
            goal=(3, -8),
        ),
    )
    specs = build_layer04_runtime_segment_specs(selected=(placement,), rejected=())
    selected_spec = next(
        spec for spec in specs if spec.event_type.value == EVENT_TYPE_LAYER04_RIM_CANDIDATE_SELECTED
    )
    wire = transient_overlay_cells_to_wire(selected_spec.transient_overlay_cells)
    path_rows = [row for row in wire if row["kind"] == OVERLAY_KIND_ROUTE_PROBE_PATH]
    assert path_rows
    assert all(row["kind"] != "space_belt" for row in path_rows)
    assert any(row["x"] == 3 and row["y"] == -9 for row in path_rows)


def test_layer04_selected_overlay_preserves_candidate_cell_rotation() -> None:
    placement = rim_bundle_placement_from_probe(
        succeeded_probe_at((3, -10), output_dir=Direction.N),
    )
    specs = build_layer04_runtime_segment_specs(selected=(placement,), rejected=())
    selected_spec = next(
        spec for spec in specs if spec.event_type.value == EVENT_TYPE_LAYER04_RIM_CANDIDATE_SELECTED
    )
    wire = transient_overlay_cells_to_wire(selected_spec.transient_overlay_cells)
    miner = next(row for row in wire if row["kind"] == "shape_miner")
    assert miner["x"] == 3
    assert miner["y"] == -10
    assert miner["rotation"] == 3
    assert miner["tile_type"] == "Layout_ShapeMiner"


def test_layer04_segment_emits_begin_selected_complete() -> None:
    placement = rim_bundle_placement_from_probe(succeeded_probe_at((3, 4)))
    frames = _frames_from_specs(selected=(placement,), rejected=())
    types = [fr.event_type.value for fr in frames]
    assert types[0] == EVENT_TYPE_LAYER04_RIM_PLACEMENT_BEGIN
    assert EVENT_TYPE_LAYER04_RIM_CANDIDATE_SELECTED in types
    assert types[-1] == EVENT_TYPE_LAYER04_RIM_PLACEMENT_COMPLETE
    assert all(is_registered_event_type(t) for t in types)
    assert all(replay_map_view_is_renderable(fr.map_view) for fr in frames)
    selected_frames = [
        fr for fr in frames if fr.event_type.value == EVENT_TYPE_LAYER04_RIM_CANDIDATE_SELECTED
    ]
    assert len(selected_frames) == 1
    assert selected_frames[0].metrics["placement_state"] == "PROVISIONAL_PLACED"


def test_layer04_segment_truncates_selected_at_replay_cap() -> None:
    placements = tuple(
        rim_bundle_placement_from_probe(
            succeeded_probe_at(
                (3 + i, 4),
                gene_key=f"miner_seed_m{i:02d}",
                equivalence_key=f"eq_{i}",
            )
        )
        for i in range(MAX_LAYER04_REPLAY_SELECTED + 5)
    )
    frames = _frames_from_specs(selected=placements, rejected=())
    selected_count = sum(
        1 for fr in frames if fr.event_type.value == EVENT_TYPE_LAYER04_RIM_CANDIDATE_SELECTED
    )
    assert selected_count == MAX_LAYER04_REPLAY_SELECTED
    complete = frames[-1]
    assert complete.metrics.get("truncated_selected_replay") is True
    assert complete.metrics.get("selected_count") == len(placements)


def test_layer04_segment_truncates_rejected_overlap_at_replay_cap() -> None:
    rejections = tuple(
        RimPlacementRejection(
            candidate_id=f"cand_{i}",
            equivalence_key=f"eq_{i}",
            reason=RimPlacementRejectReason.PHYSICAL_OVERLAP,
            conflicting_candidate_id="winner",
            conflicting_cells=frozenset({(i % 5, i % 5)}),
        )
        for i in range(MAX_LAYER04_REPLAY_REJECTED_OVERLAP + 10)
    )
    frames = _frames_from_specs(selected=(), rejected=rejections)
    overlap_frames = [
        fr for fr in frames if fr.event_type.value == "layer04_rim_candidate_rejected_overlap"
    ]
    assert len(overlap_frames) == MAX_LAYER04_REPLAY_REJECTED_OVERLAP
    complete = frames[-1]
    assert complete.metrics.get("truncated_rejected_overlap_replay") is True
    assert complete.metrics.get("rejected_overlap_count") == len(rejections)


def test_layer04_complete_frame_projects_packing_observability() -> None:
    placement = rim_bundle_placement_from_probe(succeeded_probe_at((3, 4)))
    observability = Layer04PackingObservability(
        greedy_baseline_total_gain=4,
        selected_total_gain=5,
        budget_limited=False,
        component_records=(),
    )
    frames = _frames_from_specs(
        selected=(placement,),
        rejected=(),
        packing_observability=observability,
    )
    complete = frames[-1]
    assert complete.metrics["selected_total_gain"] == 5
    assert complete.metrics["greedy_baseline_total_gain"] == 4
    assert complete.metrics["budget_limited"] is False
