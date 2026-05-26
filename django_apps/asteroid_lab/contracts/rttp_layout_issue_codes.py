"""Stable layout connectivity issue codes (RTTP A6 — read-only validation)."""

from __future__ import annotations

ISSUE_CODE_MISSING_OUTPUT_TRANSPORT = "missing_output_transport"
ISSUE_CODE_MISSING_EXTERIOR_ROUTE = "missing_exterior_route"
ISSUE_CODE_INSUFFICIENT_EXTERIOR_CONNECTORS = "insufficient_exterior_connectors"
# EVTC-6b DEFERRED: reserved for post-commit shortest-path audit; not emitted by validation yet.
ISSUE_CODE_ROUTE_NOT_SHORTEST_FEASIBLE = "route_not_shortest_feasible"

__all__ = [
    "ISSUE_CODE_INSUFFICIENT_EXTERIOR_CONNECTORS",
    "ISSUE_CODE_MISSING_EXTERIOR_ROUTE",
    "ISSUE_CODE_MISSING_OUTPUT_TRANSPORT",
    "ISSUE_CODE_ROUTE_NOT_SHORTEST_FEASIBLE",
]
