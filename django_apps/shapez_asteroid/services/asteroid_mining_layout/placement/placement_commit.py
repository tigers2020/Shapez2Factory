"""Placement bundle commit FSM (P2-B): provisional → routed / quarantine → rollback."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord


class PlacementCommitState(StrEnum):
    """Pass12 bundle commit FSM 상태값.

        provisional, routed, quarantine, rollback 흐름을 row metadata로 남긴다.
        §9 STEP4 routing failure 맥락이다.

    상세: documents/Algorithm/mining_solver_cursor_sessions/08_step4_routing.md"""

    PROVISIONAL_PLACED = "provisional_placed"
    ROUTED_CONFIRMED = "routed_confirmed"
    QUARANTINED_UNROUTED = "quarantined_unrouted"
    ROLLED_BACK = "rolled_back"


@dataclass(frozen=True)
class PlacementCommitRecord:
    """Pass12 placement bundle의 commit/route/rollback DTO.

        placement_id로 STEP4 route 및 failure 항목과 매칭된다 (§9.6 P2-B).

    상세: documents/Algorithm/mining_solver_cursor_sessions/08_step4_routing.md"""

    placement_id: str
    placement_pass: str
    extractor_cell: Coord
    extension_cells: tuple[Coord, ...]
    stub_cell: Coord
    transport_kind: str
    state: PlacementCommitState
    route_id: str | None = None
    rollback_reason: str | None = None


def make_placement_id(placement_pass: str, seq: int) -> str:
    """Stable id: ``p1-000042`` / ``p2-000007`` (``placement_pass`` is ``pass1``|``pass2``)."""

    prefix = "p1" if placement_pass == "pass1" else "p2"
    return f"{prefix}-{seq:06d}"


def placement_commit_counts_by_state(placement_commit_by_id: dict[str, str]) -> dict[str, int]:
    """placement_commit_by_id를 FSM 상태별 개수로 집계한다 (§9 STEP4 routing failure)."""
    out: dict[str, int] = {s.value: 0 for s in PlacementCommitState}
    for st in placement_commit_by_id.values():
        out[st] = out.get(st, 0) + 1
    return out


def unfinalized_placement_count_from_counts(counts: Mapping[str, int] | None) -> int:
    """FSM rows not yet terminal (``ROUTED_CONFIRMED`` / ``ROLLED_BACK``) — P2-B.1 guard."""

    if not counts:
        return 0
    p = PlacementCommitState.PROVISIONAL_PLACED.value
    q = PlacementCommitState.QUARANTINED_UNROUTED.value
    return int(counts.get(p, 0) + counts.get(q, 0))


def placement_record_to_failure_dict(
    rec: PlacementCommitRecord,
    *,
    reason: str,
    recovery_trigger: str | None = None,
) -> dict[str, Any]:
    """STEP4 ``routing_failures`` entry: row-friendly coords + trace contract fields."""

    d = asdict(rec)
    d["extractor_cell"] = list(d["extractor_cell"])
    d["extension_cells"] = [list(c) for c in d["extension_cells"]]
    d["stub_cell"] = list(d["stub_cell"])
    st = d["state"]
    d["state"] = st.value if isinstance(st, PlacementCommitState) else str(st)
    d["reason"] = reason
    d["extractor_id"] = rec.placement_id
    d["attempt_count"] = 1
    d["final_state"] = d["state"]
    d["last_error"] = reason
    d["recovery_trigger"] = recovery_trigger or RECOVERY_TRIGGER_STEP4_ROUTING_FAILURE
    return d
