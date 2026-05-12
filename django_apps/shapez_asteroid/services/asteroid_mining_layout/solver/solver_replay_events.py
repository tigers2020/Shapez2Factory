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
# v4: ``ui_frames`` — one UI row per ``solver_timeline`` index (event_indices, computation_cycle
# bounds, pass3_layout_snapshots); built from the same normalized ``events`` list.
# v4: ``ui_frames`` STEP10 primary hints — ``primary_for_step10_ui``, ``computation_cycle_ui_*``,
# ``overlay_event_indices`` (see ``solver_replay_frames.build_replay_ui_frames``). Events with
# ``phase=validation_recovery`` (e.g. ``recovery_branch``) map to the ``solver_validate`` timeline
# row. P5 recovery summary keys are emitted on ``solver_summary`` (not replay root).
# v5: ``route_replaced`` payload adds optional cell diff for STEP10 map overlay:
# ``cells_removed`` / ``cells_added`` (list of ``[x, y]``), ``cells_kept`` (null or list),
# ``transport_kind`` (``shape_belt`` | ``fluid_pipe``), ``replacement_reason``; per-row detail
# remains in ``replacements[]``. Aggregates on the event mirror the union of replacement rows.
# v7: protected corridor delta kinds — ``corridor_added``, ``corridor_removed``,
# ``corridor_promoted``, ``corridor_replaced`` (see ``corridor_*_replay_payload`` helpers;
# MVP may emit only a subset).
# v8: ``ui_frames[].trunk_load_overlay`` — compact STEP4 trunk observation slice for STEP10 UI
# (includes ``trunk_observation_layer`` = committed route traversals; corridor tiers are separate).


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
    CORRIDOR_ADDED = "corridor_added"
    CORRIDOR_REMOVED = "corridor_removed"
    CORRIDOR_PROMOTED = "corridor_promoted"
    CORRIDOR_REPLACED = "corridor_replaced"


CORRIDOR_REPLAY_TIERS: frozenset[str] = frozenset({"hard", "soft", "candidate"})


def sorted_corridor_replay_cells(raw: object) -> list[list[int]]:
    """Normalize ``[x, y]`` pairs: drop ``x==0``, dedupe, sort by (y, x) like STEP4 pools."""

    pairs: set[tuple[int, int]] = set()
    if isinstance(raw, list):
        for it in raw:
            if isinstance(it, (list, tuple)) and len(it) >= 2:
                try:
                    x, y = int(it[0]), int(it[1])
                except (TypeError, ValueError):
                    continue
                if x == 0:
                    continue
                pairs.add((x, y))
    return [[a, b] for a, b in sorted(pairs, key=lambda p: (p[1], p[0]))]


def corridor_added_replay_payload(
    *,
    transaction_id: str,
    parent_txn_id: str | None,
    tier: str,
    cells_raw: object,
) -> dict[str, Any] | None:
    """Payload for ``corridor_added``; ``None`` if tier invalid or no cells after normalize."""

    if tier not in CORRIDOR_REPLAY_TIERS:
        return None
    cells = sorted_corridor_replay_cells(cells_raw)
    if not cells:
        return None
    out = replay_transaction_payload(transaction_id=transaction_id, parent_txn_id=parent_txn_id)
    out["tier"] = tier
    out["cells"] = cells
    return out


def corridor_removed_replay_payload(
    *,
    transaction_id: str,
    parent_txn_id: str | None,
    tier: str,
    cells_raw: object,
) -> dict[str, Any] | None:
    """Payload for ``corridor_removed``; same shape as ``corridor_added``."""

    return corridor_added_replay_payload(
        transaction_id=transaction_id,
        parent_txn_id=parent_txn_id,
        tier=tier,
        cells_raw=cells_raw,
    )


def corridor_promoted_replay_payload(
    *,
    transaction_id: str,
    parent_txn_id: str | None,
    from_tier: str,
    to_tier: str,
    cells_raw: object,
) -> dict[str, Any] | None:
    """Payload for ``corridor_promoted``; ``None`` if tiers invalid, equal, or no cells."""

    if from_tier not in CORRIDOR_REPLAY_TIERS or to_tier not in CORRIDOR_REPLAY_TIERS:
        return None
    if from_tier == to_tier:
        return None
    cells = sorted_corridor_replay_cells(cells_raw)
    if not cells:
        return None
    out = replay_transaction_payload(transaction_id=transaction_id, parent_txn_id=parent_txn_id)
    out["from_tier"] = from_tier
    out["to_tier"] = to_tier
    out["cells"] = cells
    return out


def corridor_replaced_replay_payload(
    *,
    transaction_id: str,
    parent_txn_id: str | None,
    tier: str,
    cells_removed_raw: object,
    cells_added_raw: object,
) -> dict[str, Any] | None:
    """Payload for ``corridor_replaced`` (v7); ``None`` if tier invalid or both sides empty."""

    if tier not in CORRIDOR_REPLAY_TIERS:
        return None
    rem = sorted_corridor_replay_cells(cells_removed_raw)
    add = sorted_corridor_replay_cells(cells_added_raw)
    if not rem and not add:
        return None
    out = replay_transaction_payload(transaction_id=transaction_id, parent_txn_id=parent_txn_id)
    out["tier"] = tier
    out["cells_removed"] = rem
    out["cells_added"] = add
    return out


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


def normalize_replay_transport_kind(kind: str | None) -> str | None:
    """Canonical replay v5 ``route_replaced`` ``transport_kind`` for UI and JSON.

    Maps legacy aliases ``belt`` / ``pipe`` to ``shape_belt`` / ``fluid_pipe``. Other non-empty
    strings are returned trimmed unchanged; ``None`` or blank → ``None`` (omit in payloads).
    """

    if kind is None:
        return None
    s = kind.strip()
    if not s:
        return None
    tl = s.lower()
    if tl == "belt":
        return "shape_belt"
    if tl == "pipe":
        return "fluid_pipe"
    if tl == "shape_belt":
        return "shape_belt"
    if tl == "fluid_pipe":
        return "fluid_pipe"
    return s


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
    optimization_metrics: dict[str, Any] | None = None,
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
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_frames import (  # noqa: E501
        build_replay_ui_frames,
    )

    ui_frames = build_replay_ui_frames(solver_timeline=frames, events=ev)
    snap: dict[str, Any] = {
        "contract_version": SOLVER_REPLAY_CONTRACT_VERSION,
        "run_id": run_id,
        "frame_order": frame_order,
        "frames": per_frame,
        "computation_cycle": max_cycle,
        "events": ev,
        "ui_frames": ui_frames,
    }
    if optimization_metrics is not None:
        snap["optimization_metrics"] = optimization_metrics
    return snap
