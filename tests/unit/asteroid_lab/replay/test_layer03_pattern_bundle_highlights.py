"""L3 probe-window pattern_bundle_highlights at segment compose time."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.event_types import (
    EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW,
)
from django_apps.asteroid_lab.replay.layer03_segment import build_layer03_runtime_segment_specs
from django_apps.asteroid_lab.replay.pattern_bundle_highlight import METRICS_KEY
from shapez2_factory.application.asteroid_lab.layers.contracts.candidates import Layer03SkipReason
from shapez2_factory.application.asteroid_lab.layers.contracts.layer03_observability import (
    build_layer03_observability_for_test,
)
from tests.unit.asteroid_lab.layers.fixtures.layer_04_placement_helpers import (
    succeeded_probe_at,
)


def test_probe_window_metrics_include_pattern_bundle_highlights() -> None:
    entry = succeeded_probe_at(
        (3, 4),
        mining=frozenset({(3, 4), (3, 5)}),
        transport=frozenset({(4, 4)}),
    )
    obs = build_layer03_observability_for_test(
        skip_reason=Layer03SkipReason.NONE,
        rim_anchor_count=1,
        route_probe_attempt_count=1,
        route_probe_succeeded_count=1,
        normal_candidate_count=1,
        replay_pool_candidates=(entry,),
    )
    specs = build_layer03_runtime_segment_specs(observability=obs)
    probe = [
        s for s in specs if s.event_type.value == EVENT_TYPE_LAYER03_RIM_BUNDLE_POOL_PROBE_WINDOW
    ]
    assert len(probe) == 1
    highlights = probe[0].metrics.get(METRICS_KEY)
    assert highlights is not None
    bundles = highlights["bundles"]
    assert len(bundles) == 1
    assert bundles[0]["bundle_key"] == entry.candidate.candidate_id
    assert bundles[0]["gene_key"] == entry.candidate.gene_key
