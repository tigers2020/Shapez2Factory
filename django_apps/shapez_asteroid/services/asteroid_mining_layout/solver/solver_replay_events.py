"""Replay contract: timeline frame order, summary keys, future mutation event kinds (STEP10).

**Algorithm isolation:** ``replay_events`` (in-memory, same run) and persisted NDJSON trace rows
are **outputs** for UI replay, CI, and ``scripts/debug`` auditors. Pass3, STEP4, Reclaim, and
Recovery code must not treat replay history or trace files as **primary** routing or policy
state — branch on explicit kwargs, ``routing_state_summary``, mining maps, and structured
summaries passed between stages, not on scanning earlier ``replay_events`` or reading
``var/`` NDJSON.

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
# v9: each replay ``events[]`` entry includes ``event_type`` (canonical category) derived from
# ``kind``; ``kind`` remains the wire-stable legacy label (STEP10 / NDJSON backward compatibility).
# v10: ``prepare_replay_events_for_snapshot`` — optional trace root keys per event (STEP10 schema),
# ``visualization_stream_tick`` (``computation_cycle % 10 == 0``), snapshot refs
# ``layout_snapshot_before_pass3`` / ``layout_snapshot_after_pass3`` on replay root,
# ``existing_layout_replay_overlay`` / ``placement_recovery_overlay`` (output-only).


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


# Canonical ``event_type`` per legacy ``kind`` (Epic B Part 2). Unknown ``kind`` → passthrough.
REPLAY_EVENT_TYPE_BY_KIND: dict[str, str] = {
    SolverMutationEventKind.FRAME_CHECKPOINT.value: "frame_checkpoint",
    SolverMutationEventKind.PASS12_BUNDLE_COMMIT.value: "placement_bundle_commit",
    SolverMutationEventKind.STEP4_ROUTE_COMMIT.value: "route_added",
    SolverMutationEventKind.PASS3_TRANSPORT_COMMIT.value: "pass3_transport_commit",
    SolverMutationEventKind.PASS3_LAYOUT_SNAPSHOT.value: "layout_snapshot",
    SolverMutationEventKind.P4_RECLAIM_ITERATION.value: "reclaim_iteration",
    SolverMutationEventKind.P4_SOFT_REPLACE.value: "reclaim_soft_replace",
    SolverMutationEventKind.RECOVERY_BRANCH.value: "recovery_entered",
    SolverMutationEventKind.TRANSACTION_BEGIN.value: "transaction_begin",
    SolverMutationEventKind.MAP_DIFF_COMMITTED.value: "map_diff_committed",
    SolverMutationEventKind.ROLLBACK.value: "transaction_rollback",
    SolverMutationEventKind.ROUTE_REPLACED.value: "route_replaced",
    SolverMutationEventKind.PLACEMENT_STATE_CHANGED.value: "placement_state_changed",
    SolverMutationEventKind.CORRIDOR_ADDED.value: "corridor_added",
    SolverMutationEventKind.CORRIDOR_REMOVED.value: "corridor_removed",
    SolverMutationEventKind.CORRIDOR_PROMOTED.value: "corridor_promoted",
    SolverMutationEventKind.CORRIDOR_REPLACED.value: "corridor_replaced",
}

OVERLAY_REPLAY_EVENT_TYPES: frozenset[str] = frozenset(
    {
        REPLAY_EVENT_TYPE_BY_KIND[SolverMutationEventKind.RECOVERY_BRANCH.value],
        REPLAY_EVENT_TYPE_BY_KIND[SolverMutationEventKind.ROLLBACK.value],
        REPLAY_EVENT_TYPE_BY_KIND[SolverMutationEventKind.ROUTE_REPLACED.value],
    }
)

REPLAY_EVENT_TYPE_PASS3_LAYOUT_SNAPSHOT = REPLAY_EVENT_TYPE_BY_KIND[
    SolverMutationEventKind.PASS3_LAYOUT_SNAPSHOT.value
]


def replay_event_type_for_kind(kind: str | None) -> str | None:
    """Map legacy ``kind`` to canonical ``event_type``.

    Unknown kinds return the trimmed ``kind`` string (forward-compatible passthrough).
    """

    if kind is None:
        return None
    s = str(kind).strip()
    if not s:
        return None
    return REPLAY_EVENT_TYPE_BY_KIND.get(s, s)


def enrich_replay_events_event_types(events: list[dict[str, Any]]) -> None:
    """Set ``event_type`` on each dict event from ``kind`` (idempotent for same ``kind``)."""

    for ev in events:
        if not isinstance(ev, dict):
            continue
        raw = ev.get("kind")
        if not isinstance(raw, str):
            continue
        et = replay_event_type_for_kind(raw)
        if et is not None:
            ev["event_type"] = et


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


# Optional root keys on each replay event dict (STEP10 trace / UI; all output-only).
REPLAY_EVENT_TRACE_OPTIONAL_KEYS: tuple[str, ...] = (
    "step_index",
    "recovery_trigger",
    "placements_added",
    "placements_removed",
    "routes_added",
    "routes_removed",
    "protected_corridors",
    "transport_kind",
    "search",
    "metrics",
    "decision",
    "visualization_stream_tick",
)


def existing_layout_replay_overlay(
    existing_layout_analysis: dict[str, Any] | None,
    *,
    max_issue_coords: int = 200,
) -> dict[str, Any] | None:
    """JSON-friendly overlay from §E.3 analysis for STEP10 replay (output-only; no routing use)."""

    if not isinstance(existing_layout_analysis, dict):
        return None
    by_kind = existing_layout_analysis.get("transport_by_kind")
    blocks: list[dict[str, Any]] = []
    if isinstance(by_kind, dict) and by_kind:
        blocks = [b for b in by_kind.values() if isinstance(b, dict)]
    else:
        t0 = existing_layout_analysis.get("transport")
        if isinstance(t0, dict):
            blocks = [t0]

    def _main_cells(transport_block: dict[str, Any]) -> list[list[int]]:
        for comp in transport_block.get("components") or []:
            if not isinstance(comp, dict):
                continue
            if comp.get("status") == "main_trunk_candidate":
                out_m: list[list[int]] = []
                for p in comp.get("cells") or []:
                    if isinstance(p, (list, tuple)) and len(p) >= 2:
                        try:
                            out_m.append([int(p[0]), int(p[1])])
                        except (TypeError, ValueError):
                            continue
                return out_m
        return []

    main: list[list[int]] = []
    for blk in blocks:
        if not main:
            main = _main_cells(blk)

    orphans: list[list[int]] = []
    singles: list[list[int]] = []

    def _consume(block: dict[str, Any]) -> None:
        for comp in block.get("components") or []:
            if not isinstance(comp, dict):
                continue
            st = comp.get("status")
            cells = comp.get("cells") or []
            if st == "orphan_component":
                for p in cells:
                    if isinstance(p, (list, tuple)) and len(p) >= 2:
                        try:
                            orphans.append([int(p[0]), int(p[1])])
                        except (TypeError, ValueError):
                            continue
            elif st == "single_cell_artifact":
                for p in cells:
                    if isinstance(p, (list, tuple)) and len(p) >= 2:
                        try:
                            singles.append([int(p[0]), int(p[1])])
                        except (TypeError, ValueError):
                            continue

    for blk in blocks:
        _consume(blk)

    eq = existing_layout_analysis.get("equipment")
    eq_d: dict[str, Any] = eq if isinstance(eq, dict) else {}

    issues_out: list[dict[str, Any]] = []
    used = 0
    for iss in existing_layout_analysis.get("issues") or []:
        if not isinstance(iss, dict):
            continue
        raw_coords = iss.get("coords")
        coords_in = raw_coords if isinstance(raw_coords, list) else []
        trim: list[list[int]] = []
        for pair in coords_in:
            if used >= max_issue_coords:
                break
            if isinstance(pair, (list, tuple)) and len(pair) >= 2:
                try:
                    trim.append([int(pair[0]), int(pair[1])])
                except (TypeError, ValueError):
                    continue
                used += 1
        issues_out.append(
            {
                "code": iss.get("code"),
                "severity": iss.get("severity"),
                "coords": trim,
                "truncated": len(coords_in) > len(trim),
            }
        )

    return {
        "original_main_trunk_component": main,
        "original_orphan_transport_components": orphans,
        "original_single_cell_transport_artifacts": singles,
        "original_miners_without_adjacent_transport": list(
            eq_d.get("miners_without_adjacent_transport") or []
        ),
        "original_miners_attached_to_orphan_transport": list(
            eq_d.get("miners_attached_to_orphan_transport") or []
        ),
        "existing_layout_issues_overlay": issues_out,
    }


def extract_pass3_layout_snapshot_refs(
    events: list[dict[str, Any]],
) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """First Pass3 before/after snapshot blocks for replay root (sha + txn id)."""

    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    for ev in events:
        if not isinstance(ev, dict):
            continue
        if ev.get("kind") != SolverMutationEventKind.PASS3_LAYOUT_SNAPSHOT.value and ev.get(
            "event_type"
        ) != REPLAY_EVENT_TYPE_PASS3_LAYOUT_SNAPSHOT:
            continue
        pl = ev.get("payload")
        if not isinstance(pl, dict):
            continue
        marker = pl.get("marker")
        h = pl.get("layout_state_sha256")
        tid = pl.get("transaction_id")
        if not isinstance(marker, str) or not isinstance(h, str):
            continue
        block: dict[str, Any] = {"layout_state_sha256": h}
        if isinstance(tid, str):
            block["transaction_id"] = tid
        if marker == "before" and before is None:
            before = block
        elif marker == "after" and after is None:
            after = block
    return before, after


def _fill_event_trace_schema(ev: dict[str, Any]) -> None:
    """Populate STEP10 optional root keys; must run after ``computation_cycle`` is set."""

    pl = ev.get("payload")
    pl_d = pl if isinstance(pl, dict) else None

    cyc = ev.get("computation_cycle")
    if isinstance(cyc, int):
        ev["step_index"] = cyc
        ev["visualization_stream_tick"] = bool(cyc % 10 == 0)
    else:
        ev["step_index"] = None
        ev["visualization_stream_tick"] = False

    for k in (
        "recovery_trigger",
        "placements_added",
        "placements_removed",
        "routes_added",
        "routes_removed",
        "protected_corridors",
        "transport_kind",
        "search",
        "metrics",
        "decision",
    ):
        ev[k] = None

    if pl_d is not None:
        ev["recovery_trigger"] = pl_d.get("recovery_trigger")

    kind = ev.get("kind")
    if pl_d is not None:
        tk = normalize_replay_transport_kind(pl_d.get("transport_kind"))
        if tk is not None:
            ev["transport_kind"] = tk
        if "metrics" in pl_d:
            ev["metrics"] = pl_d.get("metrics")
        if "search" in pl_d:
            ev["search"] = pl_d.get("search")
        if "decision" in pl_d:
            ev["decision"] = pl_d.get("decision")

    if kind == SolverMutationEventKind.MAP_DIFF_COMMITTED.value and pl_d is not None:
        ca, cr = pl_d.get("coords_added"), pl_d.get("coords_removed")
        if isinstance(ca, int):
            ev["placements_added"] = ca
        if isinstance(cr, int):
            ev["placements_removed"] = cr

    if kind == SolverMutationEventKind.ROUTE_REPLACED.value and pl_d is not None:
        rem = pl_d.get("cells_removed")
        add = pl_d.get("cells_added")
        if isinstance(rem, list):
            ev["routes_removed"] = len(rem)
        if isinstance(add, list):
            ev["routes_added"] = len(add)

    if kind == SolverMutationEventKind.CORRIDOR_PROMOTED.value and pl_d is not None:
        cells_pm = pl_d.get("cells")
        n_pm = len(cells_pm) if isinstance(cells_pm, list) else None
        ev["protected_corridors"] = {
            "from_tier": pl_d.get("from_tier"),
            "to_tier": pl_d.get("to_tier"),
            "cell_count": n_pm,
        }
    elif kind == SolverMutationEventKind.CORRIDOR_REPLACED.value and pl_d is not None:
        rem_c = pl_d.get("cells_removed")
        add_c = pl_d.get("cells_added")
        ev["protected_corridors"] = {
            "tier": pl_d.get("tier"),
            "cells_removed_count": len(rem_c) if isinstance(rem_c, list) else None,
            "cells_added_count": len(add_c) if isinstance(add_c, list) else None,
        }
    elif kind in (
        SolverMutationEventKind.CORRIDOR_ADDED.value,
        SolverMutationEventKind.CORRIDOR_REMOVED.value,
    ):
        if pl_d is not None:
            tier = pl_d.get("tier")
            cells = pl_d.get("cells")
            n = len(cells) if isinstance(cells, list) else None
            if tier is not None or n is not None:
                ev["protected_corridors"] = {"tier": tier, "cell_count": n}


def prepare_replay_events_for_snapshot(events: list[dict[str, Any]]) -> int:
    """Normalize ``computation_cycle``, ``event_type``, and STEP10 per-event trace keys.

    Output-only: must not be read by solver routing / placement decisions.
    ``visualization_stream_tick`` is True when ``computation_cycle % 10 == 0`` (1-based cycles).
    """

    max_cycle = normalize_replay_events_computation_cycles(events)
    enrich_replay_events_event_types(events)
    for ev in events:
        if isinstance(ev, dict):
            _fill_event_trace_schema(ev)
    return max_cycle


def build_solver_replay_snapshot(
    *,
    frames: list[dict[str, Any]],
    run_id: str,
    events: list[dict[str, Any]] | None = None,
    optimization_metrics: dict[str, Any] | None = None,
    existing_layout_analysis: dict[str, Any] | None = None,
    placement_recovery_overlay: dict[str, Any] | None = None,
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
    max_cycle = prepare_replay_events_for_snapshot(ev)
    from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_frames import (  # noqa: E501
        build_replay_ui_frames,
    )

    ui_frames = build_replay_ui_frames(solver_timeline=frames, events=ev)
    before_p3, after_p3 = extract_pass3_layout_snapshot_refs(ev)
    ela_overlay = existing_layout_replay_overlay(existing_layout_analysis)
    snap: dict[str, Any] = {
        "contract_version": SOLVER_REPLAY_CONTRACT_VERSION,
        "run_id": run_id,
        "frame_order": frame_order,
        "frames": per_frame,
        "computation_cycle": max_cycle,
        "events": ev,
        "ui_frames": ui_frames,
        "layout_snapshot_before_pass3": before_p3,
        "layout_snapshot_after_pass3": after_p3,
    }
    if ela_overlay is not None:
        snap["existing_layout_replay_overlay"] = ela_overlay
    if placement_recovery_overlay is not None:
        snap["placement_recovery_overlay"] = placement_recovery_overlay
    if optimization_metrics is not None:
        snap["optimization_metrics"] = optimization_metrics
    return snap
