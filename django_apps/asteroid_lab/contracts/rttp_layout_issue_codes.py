"""Stable layout connectivity issue codes (RTTP A6 — read-only validation)."""

from __future__ import annotations

ISSUE_CODE_MISSING_OUTPUT_TRANSPORT = "missing_output_transport"
ISSUE_CODE_MISSING_EXTERIOR_ROUTE = "missing_exterior_route"
ISSUE_CODE_INSUFFICIENT_EXTERIOR_CONNECTORS = "insufficient_exterior_connectors"
ISSUE_CODE_ROUTE_WITHOUT_LANE_ASSIGNMENT = "route_without_lane_assignment"
ISSUE_CODE_EXTERIOR_LANE_OVER_CAPACITY = "exterior_lane_over_capacity"
ISSUE_CODE_EXTERIOR_LANE_KIND_MISMATCH = "exterior_lane_kind_mismatch"
ISSUE_CODE_EXTERIOR_LANE_PREMATURE_ACTIVATION = "exterior_lane_premature_activation"
ISSUE_CODE_EXTERIOR_LANE_TRUNK_NOT_SHARED = "exterior_lane_trunk_not_shared"
ISSUE_CODE_EXTERIOR_LANE_BRANCH_NOT_CONNECTED_TO_TRUNK = (
    "exterior_lane_branch_not_connected_to_trunk"
)
# EVTC-6b DEFERRED: reserved for post-commit shortest-path audit; not emitted by validation yet.
ISSUE_CODE_ROUTE_NOT_SHORTEST_FEASIBLE = "route_not_shortest_feasible"

__all__ = [
    "ISSUE_CODE_EXTERIOR_LANE_BRANCH_NOT_CONNECTED_TO_TRUNK",
    "ISSUE_CODE_EXTERIOR_LANE_KIND_MISMATCH",
    "ISSUE_CODE_EXTERIOR_LANE_OVER_CAPACITY",
    "ISSUE_CODE_EXTERIOR_LANE_PREMATURE_ACTIVATION",
    "ISSUE_CODE_EXTERIOR_LANE_TRUNK_NOT_SHARED",
    "ISSUE_CODE_INSUFFICIENT_EXTERIOR_CONNECTORS",
    "ISSUE_CODE_MISSING_EXTERIOR_ROUTE",
    "ISSUE_CODE_MISSING_OUTPUT_TRANSPORT",
    "ISSUE_CODE_ROUTE_NOT_SHORTEST_FEASIBLE",
    "ISSUE_CODE_ROUTE_WITHOUT_LANE_ASSIGNMENT",
]
