"""P4 provisional / incremental commit entry gates (readability helpers; contract unchanged)."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord


def p4_provisional_commit_entry_skip_reason(
    *,
    provisional_enabled: bool,
    scan_trace: Mapping[str, Any],
) -> str | None:
    """Return ``p4_reclaim_provisional_commit_skip_reason`` when B1 must no-op, else ``None``."""

    if not provisional_enabled:
        return "p4_reclaim_provisional_commit_disabled"
    if not scan_trace.get("p4_reclaim_shadow_enabled"):
        return str(scan_trace.get("p4_reclaim_shadow_skip_reason") or "p4_shadow_disabled")
    if scan_trace.get("p4_reclaim_shadow_skip_reason"):
        return str(scan_trace.get("p4_reclaim_shadow_skip_reason"))
    return None


def p4_incremental_route_commit_will_run(
    p4_reclaim_incremental_route_commit_enabled: bool,
    is_external: Callable[[Coord], bool] | None,
) -> bool:
    """Whether P4-B2 incremental route commit is eligible (same predicate as legacy B1)."""

    return p4_reclaim_incremental_route_commit_enabled and is_external is not None


def p4_incremental_route_skip_reason_for_trace(
    p4_reclaim_incremental_route_commit_enabled: bool,
) -> str:
    """Trace ``p4_reclaim_incremental_route_skip_reason`` when B2 does not run."""

    return (
        "p4_reclaim_incremental_route_disabled"
        if not p4_reclaim_incremental_route_commit_enabled
        else "is_external_not_provided"
    )
