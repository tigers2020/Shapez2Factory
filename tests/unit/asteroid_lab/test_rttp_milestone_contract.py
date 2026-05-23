from __future__ import annotations

from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    RTTP_MILESTONE_EVENT_TYPES,
)


def test_rttp_milestone_event_types_match_v02_contract() -> None:
    expected = frozenset(
        {
            et.EVENT_TYPE_ROUTING_PROBE_STARTED,
            et.EVENT_TYPE_CANDIDATE_GENERATED,
            et.EVENT_TYPE_GA_BEST_UPDATED,
            et.EVENT_TYPE_ROUTING_COMMITTED,
        }
    )
    assert RTTP_MILESTONE_EVENT_TYPES == expected
