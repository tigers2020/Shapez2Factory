"""Rim greedy replay segment projector tests."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.rim_greedy import (
    CommittedRimSeedPlacement,
    IntegratedRimGreedyResult,
    RimGreedyMetrics,
    RimGreedyObservationEvent,
    RimGreedyObservationPhase,
    RimGreedyPass2Report,
    build_empty_integrated_rim_greedy_result,
)
from django_apps.asteroid_lab.layers.contracts.transport_kind import TransportKind
from django_apps.asteroid_lab.layers.layer_03_rim_greedy_placement.append import (
    append_committed_rim_placements,
    provisional_overlay_from_append,
)
from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_LAYER03_RIM_GREEDY_BEGIN,
    EVENT_TYPE_LAYER03_RIM_GREEDY_COMPLETE,
    EVENT_TYPE_LAYER03_RIM_GREEDY_SEED_COMMITTED,
    EVENT_TYPE_LAYER03_RIM_GREEDY_SUMMARY,
)
from django_apps.asteroid_lab.replay.layer03_overlay_cells import (
    OVERLAY_KIND_CANDIDATE_MINER,
)
from django_apps.asteroid_lab.replay.layer03_rim_greedy_segment import (
    build_layer03_rim_greedy_runtime_segment_specs,
    build_layer03_rim_greedy_segment_specs,
)
from django_apps.asteroid_lab.replay.pattern_bundle_highlight import METRICS_KEY
from django_apps.asteroid_lab.replay.runtime_frame_finalize import (
    finalize_segment_spec_to_json_dict,
    finalize_specs_to_timeline_frames,
)
from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
    renderable_base_map_view_for_golden,
)


def _greedy_result_with_placements() -> IntegratedRimGreedyResult:
    placements = (
        CommittedRimSeedPlacement(
            placement_id="rim_greedy_CW_TL_0",
            variant_id="CW_TL",
            anchor=(6, 4),
            output_dir="E",
            seed_id="rim_greedy_m1e1",
            miner_cells=frozenset({(6, 4)}),
            extension_cells=frozenset({(5, 4)}),
            m_output_stub=(7, 4),
            route_probe_path=((7, 4), (8, 4)),
        ),
        CommittedRimSeedPlacement(
            placement_id="rim_greedy_CW_TL_1",
            variant_id="CW_TL",
            anchor=(6, 5),
            output_dir="N",
            seed_id="rim_greedy_m1e1",
            miner_cells=frozenset({(6, 5)}),
            extension_cells=frozenset({(6, 4)}),
            m_output_stub=(6, 6),
            route_probe_path=((6, 6), (7, 6), (8, 4)),
        ),
    )
    append_result = append_committed_rim_placements(committed_placements=placements)
    overlay = provisional_overlay_from_append(
        append_result,
        transport_kind=TransportKind.SHAPE_BELT,
    )
    return IntegratedRimGreedyResult(
        committed_placements=placements,
        rejected_attempts=(),
        occupied_equipment_cells=frozenset({(6, 4), (5, 4), (6, 5)}),
        reserved_route_cells=frozenset({(7, 4), (8, 4), (6, 6), (7, 6)}),
        append_result=append_result,
        provisional_overlay=overlay,
        pass2_report=RimGreedyPass2Report(
            variant_id="CW_TL",
            score=10.0,
            hard_fail=False,
            miner_count=2,
            extension_count=2,
            total_route_length=5,
        ),
        winning_variant_id="CW_TL",
        metrics=RimGreedyMetrics(
            rim_anchor_count=81,
            committed_placement_count=2,
            rejected_attempt_count=0,
            reserved_route_cell_count=4,
            winning_variant_id="CW_TL",
            pass2_score=10.0,
        ),
        observability_events=(),
    )


def test_greedy_events_materialize_monotonic_frames() -> None:
    events = (
        RimGreedyObservationEvent(
            phase=RimGreedyObservationPhase.RIM_GREEDY_BEGIN,
            variant_id="CW_TL",
            payload={},
        ),
        RimGreedyObservationEvent(
            phase=RimGreedyObservationPhase.RIM_GREEDY_COMPLETE,
            variant_id="CW_TL",
            payload={"winning_variant_id": "CW_TL"},
        ),
    )
    specs = build_layer03_rim_greedy_segment_specs(events)
    assert specs[0].metrics["phase"] == "rim_greedy_begin"
    frames = finalize_specs_to_timeline_frames(
        specs,
        structural_map_view=renderable_base_map_view_for_golden(),
    )
    assert len(frames) == 2
    assert all(
        frames[i].frame_index <= frames[i + 1].frame_index for i in range(len(frames) - 1)
    )


def test_runtime_segment_includes_summary_and_overlay_windows() -> None:
    specs = build_layer03_rim_greedy_runtime_segment_specs(_greedy_result_with_placements())
    event_types = [spec.event_type.value for spec in specs]
    assert event_types[0] == EVENT_TYPE_LAYER03_RIM_GREEDY_BEGIN
    assert EVENT_TYPE_LAYER03_RIM_GREEDY_SUMMARY in event_types
    assert EVENT_TYPE_LAYER03_RIM_GREEDY_SEED_COMMITTED in event_types

    summary = next(s for s in specs if s.event_type.value == EVENT_TYPE_LAYER03_RIM_GREEDY_SUMMARY)
    assert METRICS_KEY in summary.metrics

    window = next(
        s for s in specs if s.event_type.value == EVENT_TYPE_LAYER03_RIM_GREEDY_SEED_COMMITTED
    )
    kinds = {cell.kind for cell in window.transient_overlay_cells}
    assert OVERLAY_KIND_CANDIDATE_MINER in kinds
    assert len(window.transient_overlay_cells) > 0


def test_runtime_complete_frame_carries_all_placement_overlays() -> None:
    specs = build_layer03_rim_greedy_runtime_segment_specs(_greedy_result_with_placements())
    complete = next(
        s for s in specs if s.event_type.value == EVENT_TYPE_LAYER03_RIM_GREEDY_COMPLETE
    )
    assert METRICS_KEY in complete.metrics
    assert len(complete.transient_overlay_cells) > 0

    base_map = renderable_base_map_view_for_golden()
    wire = finalize_segment_spec_to_json_dict(
        complete,
        structural_map_view=base_map,
        structural_overlay_wire=(),
        persistent_overlay_wire=(),
        exterior_plan_wire=None,
    )
    overlay = wire["map_view"]["overlay_cells"]
    assert len(overlay) > 0
    kinds = {row.get("kind") for row in overlay if isinstance(row, dict)}
    assert "shape_miner" in kinds
    assert "shape_miner_extension" in kinds
