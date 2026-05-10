"""Replay contract: timeline frame order, summary keys, future mutation event kinds (STEP10).

Hash-stable summaries are not enough for UI/CI diff; this module defines a small JSON-friendly
snapshot alongside ``solver_state_hash`` / step hashes.
"""

from __future__ import annotations

import uuid
from enum import StrEnum
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    SOLVER_REPLAY_CONTRACT_VERSION,
)

# v1: frame_order + per-frame summary_keys only.
# v2: adds ``events`` (append-only mutation log); kinds may grow; ignore unknown kinds.
# v2 transaction grouping: ``transaction_begin`` / ``rollback`` / ``map_diff_committed`` for the
# same logical txn share ``payload.transaction_id``. Optional ``payload.parent_txn_id`` links a
# child txn to an ancestor (lineage for replay UI; parent may already be committed). Omit if
# absent.
# v3: top-level ``computation_cycle`` (max index) + each event ``computation_cycle`` (1..n in
# append order). Adds ``pass3_layout_snapshot`` (payload.marker before|after,
# payload.layout_state_sha256).


class SolverMutationEventKind(StrEnum):
    """Mutation / transaction labels for replay and STEP10 UI (subset emitted per run)."""

    FRAME_CHECKPOINT = "frame_checkpoint"
    PASS12_BUNDLE_COMMIT = "pass12_bundle_commit"
    STEP4_ROUTE_COMMIT = "step4_route_commit"
    PASS3_TRANSPORT_COMMIT = "pass3_transport_commit"
    PASS3_LAYOUT_SNAPSHOT = "pass3_layout_snapshot"
    P4_RECLAIM_ITERATION = "p4_reclaim_iteration"
    P4_SOFT_REPLACE = "p4_soft_replace"
    RECOVERY_BRANCH = "recovery_branch"
    TRANSACTION_BEGIN = "transaction_begin"
    MAP_DIFF_COMMITTED = "map_diff_committed"
    ROLLBACK = "rollback"
    ROUTE_REPLACED = "route_replaced"
    PLACEMENT_STATE_CHANGED = "placement_state_changed"


def new_replay_transaction_id() -> str:
    """Opaque hex id: group replay events for one ``SolverMutationTransaction`` (STEP4, P4, …)."""

    return uuid.uuid4().hex


def replay_transaction_payload(
    *,
    transaction_id: str,
    parent_txn_id: str | None = None,
) -> dict[str, Any]:
    """Payload keys shared by txn-scoped replay events (group by ``transaction_id``)."""

    p: dict[str, Any] = {"transaction_id": transaction_id}
    if parent_txn_id is not None:
        p["parent_txn_id"] = parent_txn_id
    return p


def layout_snapshot_payload(
    *,
    marker: str,
    layout_state_sha256: str,
    transaction_id: str,
    parent_txn_id: str | None = None,
) -> dict[str, Any]:
    """Pass3 before/after layout fingerprint (same ``transaction_id`` as enclosing Pass3 txn)."""

    p = replay_transaction_payload(transaction_id=transaction_id, parent_txn_id=parent_txn_id)
    p["marker"] = marker
    p["layout_state_sha256"] = layout_state_sha256
    return p


def normalize_replay_events_computation_cycles(events: list[dict[str, Any]]) -> int:
    """Assign monotonic ``computation_cycle`` (1..n) in list order.

    Returns max cycle (0 if no dict events).
    """

    n = 0
    for ev in events:
        if not isinstance(ev, dict):
            continue
        n += 1
        ev["computation_cycle"] = n
    return n


def build_solver_replay_snapshot(
    *,
    frames: list[dict[str, Any]],
    run_id: str,
    events: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Deterministic replay snapshot: frame order, summary keys, optional mutation ``events``."""

    frame_order = [str(f.get("id", "")) for f in frames]
    per_frame: list[dict[str, Any]] = []
    for f in frames:
        summary = f.get("summary")
        keys: list[str] = []
        if isinstance(summary, dict):
            keys = sorted(summary.keys())
        per_frame.append({"id": f.get("id"), "summary_keys": keys})
    ev = list(events) if events is not None else []
    max_cycle = normalize_replay_events_computation_cycles(ev)
    return {
        "contract_version": SOLVER_REPLAY_CONTRACT_VERSION,
        "run_id": run_id,
        "frame_order": frame_order,
        "frames": per_frame,
        "computation_cycle": max_cycle,
        "events": ev,
    }
