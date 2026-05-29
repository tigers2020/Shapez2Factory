"""Layer 04 runtime replay segment tests (central assembler PR-A)."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.layer_04_rim_bundle_placement.place import (
    build_rim_bundle_placement,
)
from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_LAYER04_RIM_CANDIDATE_SELECTED,
    EVENT_TYPE_LAYER04_RIM_PLACEMENT_BEGIN,
    EVENT_TYPE_LAYER04_RIM_PLACEMENT_COMPLETE,
    is_registered_event_type,
)
from django_apps.asteroid_lab.replay.layer04_segment import build_layer04_runtime_segment_frames
from django_apps.asteroid_lab.replay.replay_limits import MAX_LAYER04_REPLAY_SELECTED
from django_apps.asteroid_lab.replay.timeline_dtos import replay_map_view_is_renderable
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    succeeded_probe_at,
)
from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
    renderable_base_map_view_for_golden,
)


def test_layer04_segment_emits_begin_selected_complete() -> None:
    placement = build_rim_bundle_placement(succeeded_probe_at((3, 4)))
    base_map_view = renderable_base_map_view_for_golden()
    frames = build_layer04_runtime_segment_frames(
        base_map_view=base_map_view,
        selected=(placement,),
        rejected=(),
    )
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
    base_map_view = renderable_base_map_view_for_golden()
    placements = tuple(
        build_rim_bundle_placement(
            succeeded_probe_at(
                (3 + i, 4),
                gene_key=f"miner_seed_m{i:02d}",
                equivalence_key=f"eq_{i}",
            )
        )
        for i in range(MAX_LAYER04_REPLAY_SELECTED + 5)
    )
    frames = build_layer04_runtime_segment_frames(
        base_map_view=base_map_view,
        selected=placements,
        rejected=(),
    )
    selected_count = sum(
        1 for fr in frames if fr.event_type.value == EVENT_TYPE_LAYER04_RIM_CANDIDATE_SELECTED
    )
    assert selected_count == MAX_LAYER04_REPLAY_SELECTED
    complete = frames[-1]
    assert complete.metrics.get("truncated_selected_replay") is True
    assert complete.metrics.get("selected_count") == len(placements)
