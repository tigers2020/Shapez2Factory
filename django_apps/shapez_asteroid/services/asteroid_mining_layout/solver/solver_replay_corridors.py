"""STEP10 replay: protected corridor coords for read-only UI (hard / soft / candidate)."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridor_read_factory import (  # noqa: E501
    protected_corridors_overlay_from_routing_state,
    protected_corridors_read_from_routing_state,
)


def effective_routing_state_at_timeline_index(
    solver_timeline: list[dict[str, Any]],
    idx: int,
) -> dict[str, Any] | None:
    """Latest ``summary.routing_state`` at or before ``idx`` (STEP4 snapshot carries forward)."""

    for j in range(idx, -1, -1):
        if j >= len(solver_timeline):
            continue
        frame = solver_timeline[j]
        if not isinstance(frame, dict):
            continue
        summary = frame.get("summary")
        if not isinstance(summary, dict):
            continue
        rs = summary.get("routing_state")
        if isinstance(rs, dict) and rs:
            return dict(rs)
    return None


def effective_trunk_load_overlay_at_timeline_index(
    solver_timeline: list[dict[str, Any]],
    idx: int,
) -> dict[str, Any] | None:
    """Compact trunk observation overlay at or before ``idx``."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_trunk_load import (  # noqa: E501
        compact_trunk_load_overlay_for_replay,
    )

    for j in range(idx, -1, -1):
        if j >= len(solver_timeline):
            continue
        frame = solver_timeline[j]
        if not isinstance(frame, dict):
            continue
        summary = frame.get("summary")
        if not isinstance(summary, dict):
            continue
        tl = summary.get("trunk_load")
        ov = compact_trunk_load_overlay_for_replay(tl if isinstance(tl, dict) else None)
        if ov:
            return ov
    return None


__all__ = [
    "effective_routing_state_at_timeline_index",
    "effective_trunk_load_overlay_at_timeline_index",
    "protected_corridors_overlay_from_routing_state",
    "protected_corridors_read_from_routing_state",
]
