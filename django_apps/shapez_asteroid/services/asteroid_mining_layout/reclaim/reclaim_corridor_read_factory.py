"""``routing_state`` / trunk corridor read merge → :class:`ProtectedCorridors` + replay overlay.

Merge rules mirror the former inline implementation in
``solver.solver_replay_corridors.protected_corridors_overlay_from_routing_state`` (flat keys vs
nested ``protected_corridors`` / ``soft_protected_candidate_corridors``). Lives under ``reclaim``
next to contracts so consumers import one direction without ``solver ↔ reclaim`` cycles.

This module is **replay / STEP10 UI** semantics only. Reclaim uses
``reclaim_corridors._corridors_from_solver_routing_state`` (different nested precedence for P4);
see the NOTE in that module—do not unify parsers without P3-C write-authority review.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridor_contracts import (  # noqa: E501
    ProtectedCorridors,
)

CoordPair = list[int]

SOURCE_ROUTING_STATE_OVERLAY = "routing_state_overlay"


def _normalize_coord_pairs(raw: object) -> list[CoordPair]:
    """Normalize ``[[x,y], ...]`` to ``[x,y]`` lists; skip ``x == 0`` (replay contract)."""

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


def _merged_corridor_pair_lists_from_routing_state(
    routing_state: Mapping[str, Any] | None,
) -> tuple[list[CoordPair], list[CoordPair], list[CoordPair]]:
    """Return ``(hard, soft, candidate)`` pair lists using replay overlay merge precedence."""

    empty: tuple[list[CoordPair], list[CoordPair], list[CoordPair]] = ([], [], [])
    if not isinstance(routing_state, Mapping):
        return empty

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

    return hard, soft, candidate


def protected_corridors_overlay_from_routing_state(
    routing_state: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Serialize corridor pools for replay UI (lists of ``[x, y]``, ``x != 0``)."""

    hard, soft, candidate = _merged_corridor_pair_lists_from_routing_state(routing_state)
    counts = {"hard": len(hard), "soft": len(soft), "candidate": len(candidate)}
    return {"hard": hard, "soft": soft, "candidate": candidate, "counts": counts}


def protected_corridors_read_from_routing_state(
    routing_state: Mapping[str, Any] | None,
) -> ProtectedCorridors:
    """Parse the same merge as the replay overlay into a read-only DTO."""

    hard_l, soft_l, cand_l = _merged_corridor_pair_lists_from_routing_state(routing_state)

    def to_fs(pairs: list[CoordPair]) -> frozenset[Coord]:
        return frozenset((p[0], p[1]) for p in pairs if len(p) >= 2)

    return ProtectedCorridors(
        hard=to_fs(hard_l),
        soft=to_fs(soft_l),
        candidate=to_fs(cand_l),
        source=SOURCE_ROUTING_STATE_OVERLAY,
    )


__all__ = [
    "SOURCE_ROUTING_STATE_OVERLAY",
    "protected_corridors_overlay_from_routing_state",
    "protected_corridors_read_from_routing_state",
]
