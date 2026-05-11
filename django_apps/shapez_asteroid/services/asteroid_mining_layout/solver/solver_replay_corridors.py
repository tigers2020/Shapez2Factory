"""STEP10 replay: protected corridor coords for read-only UI (hard / soft / candidate)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

CoordPair = list[int]


def _normalize_coord_pairs(raw: object) -> list[CoordPair]:
    out: list[CoordPair] = []
    if not isinstance(raw, list):
        return out
    for it in raw:
        if isinstance(it, (list, tuple)) and len(it) >= 2:
            try:
                x = int(it[0])
                y = int(it[1])
            except (TypeError, ValueError):
                continue
            if x == 0:
                continue
            out.append([x, y])
    return out


def protected_corridors_overlay_from_routing_state(
    routing_state: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Serialize ``routing_state`` corridor pools for replay UI (lists of ``[x, y]``, x≠0)."""

    empty: dict[str, Any] = {
        "hard": [],
        "soft": [],
        "candidate": [],
        "counts": {"hard": 0, "soft": 0, "candidate": 0},
    }
    if not isinstance(routing_state, Mapping):
        return dict(empty)

    hard = _normalize_coord_pairs(routing_state.get("hard_protected_corridors"))
    soft = _normalize_coord_pairs(routing_state.get("soft_protected_corridors"))
    candidate = _normalize_coord_pairs(routing_state.get("soft_protected_candidate_corridors"))

    nested = routing_state.get("protected_corridors")
    if isinstance(nested, Mapping):
        if not hard:
            hard = _normalize_coord_pairs(nested.get("hard"))
        if not soft:
            soft = _normalize_coord_pairs(nested.get("soft"))
        if not candidate and nested.get("candidate") is not None:
            candidate = _normalize_coord_pairs(nested.get("candidate"))

    counts = {"hard": len(hard), "soft": len(soft), "candidate": len(candidate)}
    return {"hard": hard, "soft": soft, "candidate": candidate, "counts": counts}


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


__all__ = [
    "effective_routing_state_at_timeline_index",
    "protected_corridors_overlay_from_routing_state",
]
