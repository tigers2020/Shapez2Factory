"""P4-A reclaim shadow scan gates and neutral trace shells (no eval loop)."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.dto.reclaim_shadow_types import (
    ReclaimShadowScanResult,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    MAX_RECLAIM_SHADOW_SCAN_LIMIT,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_map_ops import (
    _allowed_internal_transport_budget,
)


def _p4_reclaim_shadow_scan_empty_route_trace_fields() -> dict[str, Any]:
    """List-shaped trace keys that are always empty lists for P4-A scan."""

    return {
        "p4_reclaim_final_route_cells_added": [],
        "p4_reclaim_soft_protected_candidate_cells_added": [],
    }


def reclaim_shadow_scan_result_when_feature_disabled() -> ReclaimShadowScanResult:
    """``p4_reclaim_shadow_enabled`` is False: trace only, no corridor or eval work."""

    return ReclaimShadowScanResult(
        trace={
            "p4_reclaim_shadow_enabled": False,
            "p4_reclaim_shadow_skip_reason": "p4_reclaim_shadow_disabled",
            "p4_reclaim_shadow_scan_limit": None,
            **_p4_reclaim_shadow_scan_empty_route_trace_fields(),
            "p4_reclaim_route_zone_rebuilt": False,
            "p4_reclaim_mineable_excluded_by_route_cells": None,
            "p4_reclaim_candidate_count": None,
            "p4_reclaim_accepted_shadow_count": None,
            "p4_reclaim_rejected_shadow_count": None,
            "p4_reclaim_internal_transport_budget": None,
            "p4_reclaim_internal_transport_projected_added": None,
            "p4_reclaim_best_candidate": None,
            "p4_reclaim_protected_corridor_source": None,
            "p4_reclaim_hard_protected_count": None,
            "p4_reclaim_soft_protected_count": None,
        },
        evals=[],
        transport_kind=None,
    )


def reclaim_shadow_scan_result_no_routing_jobs(
    *,
    zone_route_rebuilt: bool,
    mineable_excluded_by_route_cells: int,
    corridor_trace: dict[str, Any],
) -> ReclaimShadowScanResult:
    """Pass3 map has no routing jobs after corridor context is known."""

    return ReclaimShadowScanResult(
        trace={
            "p4_reclaim_shadow_enabled": True,
            "p4_reclaim_shadow_skip_reason": "no_routing_jobs",
            "p4_reclaim_shadow_scan_limit": MAX_RECLAIM_SHADOW_SCAN_LIMIT,
            **_p4_reclaim_shadow_scan_empty_route_trace_fields(),
            "p4_reclaim_route_zone_rebuilt": zone_route_rebuilt,
            "p4_reclaim_mineable_excluded_by_route_cells": mineable_excluded_by_route_cells,
            "p4_reclaim_candidate_count": 0,
            "p4_reclaim_accepted_shadow_count": 0,
            "p4_reclaim_rejected_shadow_count": 0,
            "p4_reclaim_internal_transport_budget": _allowed_internal_transport_budget(0),
            "p4_reclaim_internal_transport_projected_added": 0,
            "p4_reclaim_best_candidate": None,
            **corridor_trace,
        },
        evals=[],
        transport_kind=None,
    )


def p4_reclaim_shadow_scan_success_trace_prefix(
    *,
    zone_route_rebuilt: bool,
    mineable_excluded_by_route_cells: int,
) -> dict[str, Any]:
    """Opening fields shared by the successful scan path before counts and best candidate."""

    return {
        "p4_reclaim_shadow_enabled": True,
        "p4_reclaim_shadow_skip_reason": None,
        "p4_reclaim_shadow_scan_limit": MAX_RECLAIM_SHADOW_SCAN_LIMIT,
        **_p4_reclaim_shadow_scan_empty_route_trace_fields(),
        "p4_reclaim_route_zone_rebuilt": zone_route_rebuilt,
        "p4_reclaim_mineable_excluded_by_route_cells": mineable_excluded_by_route_cells,
    }
