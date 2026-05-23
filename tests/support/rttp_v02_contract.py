"""RTTP v0.2 test contract constants (H2) — not production imports."""

from __future__ import annotations

from django_apps.asteroid_lab.replay import event_types as et

RTTP_PIPELINE_MILESTONE_EVENT_TYPES = frozenset(
    {
        et.EVENT_TYPE_RTTP_ROUTE_DOMAIN_SNAPSHOT,
        et.EVENT_TYPE_RTTP_CANDIDATE_POOL_SNAPSHOT,
        et.EVENT_TYPE_RTTP_GENOME_SELECTION_SNAPSHOT,
        et.EVENT_TYPE_RTTP_COMMIT_DOMAIN_SNAPSHOT,
    }
)

__all__ = ["RTTP_PIPELINE_MILESTONE_EVENT_TYPES"]
