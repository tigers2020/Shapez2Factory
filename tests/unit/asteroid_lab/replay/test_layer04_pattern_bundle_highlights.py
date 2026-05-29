"""L4 selected-placement pattern_bundle_highlights (equipment cells only)."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_LAYER04_RIM_CANDIDATE_SELECTED,
    EVENT_TYPE_LAYER04_RIM_PLACEMENT_COMPLETE,
)
from django_apps.asteroid_lab.replay.layer04_segment import build_layer04_runtime_segment_specs
from django_apps.asteroid_lab.replay.pattern_bundle_highlight import (
    METRICS_KEY,
    build_pattern_bundle_highlights_wire,
    mining_occupied_from_rim_placement,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    rim_bundle_placement_from_probe,
    succeeded_probe_at,
)


def test_selected_frame_highlights_use_extractor_union_extension_only() -> None:
    placement = rim_bundle_placement_from_probe(
        succeeded_probe_at(
            (3, 4),
            mining=frozenset({(3, 4), (3, 5)}),
            transport=frozenset({(4, 4)}),
        ),
    )
    occupied = mining_occupied_from_rim_placement(placement)
    assert occupied == placement.extractor_cells | placement.extension_cells
    assert placement.output_stub_cells.isdisjoint(occupied)

    expected_wire = build_pattern_bundle_highlights_wire(
        ((placement.candidate_id, occupied, placement.gene_key),)
    )

    specs = build_layer04_runtime_segment_specs(selected=(placement,), rejected=())
    selected = next(
        s for s in specs if s.event_type.value == EVENT_TYPE_LAYER04_RIM_CANDIDATE_SELECTED
    )
    assert selected.metrics.get(METRICS_KEY) == expected_wire


def test_placement_complete_frame_includes_all_selected_highlights() -> None:
    placement_a = rim_bundle_placement_from_probe(
        succeeded_probe_at(
            (3, 4),
            mining=frozenset({(3, 4), (3, 5)}),
            transport=frozenset({(4, 4)}),
        ),
    )
    placement_b = rim_bundle_placement_from_probe(
        succeeded_probe_at(
            (5, 4),
            mining=frozenset({(5, 4), (5, 5)}),
            transport=frozenset({(6, 4)}),
        ),
    )
    expected_wire = build_pattern_bundle_highlights_wire(
        (
            (
                placement_a.candidate_id,
                mining_occupied_from_rim_placement(placement_a),
                placement_a.gene_key,
            ),
            (
                placement_b.candidate_id,
                mining_occupied_from_rim_placement(placement_b),
                placement_b.gene_key,
            ),
        )
    )
    specs = build_layer04_runtime_segment_specs(
        selected=(placement_a, placement_b),
        rejected=(),
    )
    complete = next(
        s for s in specs if s.event_type.value == EVENT_TYPE_LAYER04_RIM_PLACEMENT_COMPLETE
    )
    assert complete.metrics.get(METRICS_KEY) == expected_wire
