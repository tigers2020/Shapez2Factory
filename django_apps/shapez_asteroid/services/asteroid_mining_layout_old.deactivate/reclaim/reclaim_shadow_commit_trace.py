"""P4 reclaim commit neutral traces and placeholder summary."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_soft_replace import (  # noqa: E501
    _p4_soft_replace_neutral_trace,
)


def p4_b2_incremental_route_neutral_trace(
    *,
    attempted: bool = False,
    committed: bool = False,
    rollback_performed: bool = False,
    rollback_reason: str | None = None,
    skip_reason: str | None = None,
) -> dict[str, Any]:
    """P4-B2 trace keys when incremental route commit does not run."""

    return {
        "p4_reclaim_incremental_route_attempted": attempted,
        "p4_reclaim_incremental_route_committed": committed,
        "p4_reclaim_incremental_route_rollback_performed": rollback_performed,
        "p4_reclaim_incremental_route_rollback_reason": rollback_reason,
        "p4_reclaim_incremental_route_skip_reason": skip_reason,
        "p4_reclaim_incremental_route_path_cells": None,
        "p4_reclaim_incremental_route_cells_added": [],
        "p4_reclaim_incremental_route_b2_internal_transport_added": None,
    }


def p4_reclaim_provisional_commit_neutral_trace(
    *,
    attempted: bool,
    committed: bool = False,
    rollback_performed: bool = False,
    rollback_reason: str | None = None,
    skip_reason: str | None = None,
) -> dict[str, Any]:
    """P4-B1 trace keys when provisional commit does not run or makes no change."""

    return {
        "p4_reclaim_provisional_commit_attempted": attempted,
        "p4_reclaim_provisional_commit_committed": committed,
        "p4_reclaim_provisional_commit_rollback_performed": rollback_performed,
        "p4_reclaim_provisional_commit_rollback_reason": rollback_reason,
        "p4_reclaim_selected_candidate": None,
        "p4_reclaim_selected_candidate_rank": None,
        "p4_reclaim_added_extractor_cells": [],
        "p4_reclaim_added_extension_cells": [],
        "p4_reclaim_added_stub_cells": [],
        "p4_reclaim_provisional_commit_skip_reason": skip_reason,
        **p4_b2_incremental_route_neutral_trace(),
    }


def p4_reclaim_shadow_placeholder(*, skip_reason: str) -> dict[str, Any]:
    """Stable ``p4_reclaim_*`` keys when the reclaim shadow path does not run."""

    b1 = p4_reclaim_provisional_commit_neutral_trace(attempted=False, skip_reason=skip_reason)
    return {
        "p4_reclaim_shadow_enabled": False,
        "p4_reclaim_shadow_skip_reason": skip_reason,
        "p4_reclaim_shadow_scan_limit": None,
        "p4_reclaim_final_route_cells_added": [],
        "p4_reclaim_soft_protected_candidate_cells_added": [],
        "p4_reclaim_route_zone_rebuilt": False,
        "p4_reclaim_mineable_excluded_by_route_cells": None,
        "p4_reclaim_route_zone_excluded_cumulative_count": 0,
        "p4_reclaim_last_commit_route_cells": [],
        "p4_reclaim_last_soft_protected_candidate_cells": [],
        "p4_reclaim_candidate_count": None,
        "p4_reclaim_accepted_shadow_count": None,
        "p4_reclaim_rejected_shadow_count": None,
        "p4_reclaim_internal_transport_budget": None,
        "p4_reclaim_internal_transport_projected_added": None,
        "p4_reclaim_best_candidate": None,
        "p4_reclaim_protected_corridor_source": None,
        "p4_reclaim_hard_protected_count": None,
        "p4_reclaim_soft_protected_count": None,
        "p4_reclaim_existing_layout_hint_cell_count": None,
        "p4_soft_replace_contract": None,
        "p4_soft_replace_attempt_count": 0,
        "p4_soft_replace_commit_count": 0,
        **b1,
        **_p4_soft_replace_neutral_trace(),
    }
