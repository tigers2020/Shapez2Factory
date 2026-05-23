"""RTTP v0.2 test contract constants (H2) — not production imports."""

from __future__ import annotations

from django_apps.asteroid_lab.replay import event_types as et

RTTP_PIPELINE_MILESTONE_EVENT_TYPES = frozenset(
    {
        et.EVENT_TYPE_ROUTING_PROBE_STARTED,
        et.EVENT_TYPE_CANDIDATE_GENERATED,
        et.EVENT_TYPE_GA_BEST_UPDATED,
        et.EVENT_TYPE_ROUTING_COMMITTED,
    }
)

__all__ = ["RTTP_PIPELINE_MILESTONE_EVENT_TYPES"]
