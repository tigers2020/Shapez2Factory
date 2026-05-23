from __future__ import annotations

from django_apps.asteroid_lab.replay import event_types as et
from django_apps.asteroid_lab.services.lab_optimization_milestone_payload import (
    RTTP_MILESTONE_EVENT_TYPES,
)


def test_rttp_milestone_event_types_match_v03_contract() -> None:
    expected = frozenset(
        {
            et.EVENT_TYPE_RTTP_ROUTE_DOMAIN_SNAPSHOT,
            et.EVENT_TYPE_RTTP_CANDIDATE_POOL_SNAPSHOT,
            et.EVENT_TYPE_RTTP_GENOME_SELECTION_SNAPSHOT,
            et.EVENT_TYPE_RTTP_COMMIT_DOMAIN_SNAPSHOT,
        }
    )
    assert RTTP_MILESTONE_EVENT_TYPES == expected
