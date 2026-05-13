"""STEP4 ``trunk_load`` payload contract (accumulate-only metrics, no capacity gates).

Contract version ``trunk_load_contract_version`` (int) identifies the nested schema for
replay/UI consumers. **Observation fields do not reject routes or enforce capacity**; they are
diagnostic / replay-friendly summaries only (no hard constraints).

**v1**: nested ``route_metrics`` / ``trunk_load_by_kind`` / ``transport_usage_load`` (raw counts).

**v2** adds ``trunk_edge_load_observation``: deterministic summary derived from
``transport_usage_load["trunk_edge_load"]`` (same facts as raw edge load; no extra gates).

**v3** adds ``transport_usage_load["trunk_edge_load_from_maximized_placements"]``: same key
schema as ``trunk_edge_load`` but counts only traversals from routes whose extractor is a
**maximized** group (exactly three owned extensions / placement record). Pass3 lex congestion
uses ``v_eff = (v_all - v_max) + v_max**2`` per edge when this block is present; otherwise
``v_eff = v_all`` (replay backward compatibility).

Nested blocks (v2 = v1 blocks plus observation):

- ``route_metrics``: ``route_cell_visits`` (sum of committed path lengths; double-counts
  shared cells) vs ``unique_route_cell_count`` (``|union of committed path cells|``).
  ``shared_trunk_reuse_ratio`` = ``1 - unique_route_cell_count / route_cell_visits`` when
  visits > 0, else ``0.0`` (observation-only; not a routing gate).
- ``trunk_load_by_kind``: per ``transport_kind`` committed trunk size, visits, and kind-local
  unique path cells (diagnostic; global unique may differ if kinds ever overlap; not expected
  for shape vs fluid in the MVP split).
- ``transport_usage_load``:
  - ``existing_transport_cell_crossings``: counts **entries onto pre-existing transport cells**
    of the routed role during path paint (same map as legacy ``edges``). This is **not** full
    route-cell load and **not** graph edge load.
  - ``trunk_edge_load``: per ``transport_kind`` undirected corridor edge keys
    ``"x1,y1--x2,y2"`` (sorted endpoints) counting route path step traversals. Separate from
    ``existing_transport_cell_crossings`` / legacy ``edges`` (pre-existing transport cell entries).
  - ``trunk_edge_load_from_maximized_placements`` (**v3**): same structure as ``trunk_edge_load``;
    observation summaries still use ``trunk_edge_load`` only (linear totals).
- ``trunk_edge_load_observation``: ``observation_version``, ``top_n``, ``shared_threshold``,
  and ``by_kind`` with ``shape_belt`` / ``fluid_pipe`` (and any extra kinds aligned with
  ``trunk_edge_load`` keys). Per kind: ``traversal_count_total`` is the **sum of integer values**
  in that kind's ``trunk_edge_load`` map (i.e. total traversals of **canonical undirected** edges
  along returned routes; reverse steps increment the same key as forward). ``top_edges`` entries
  use the **same string edge key** as ``trunk_edge_load`` (not directed ``->`` keys; not nested
  coord lists).

Merge safety:

- ``p2c_metrics`` keys in ``_TRUNK_LOAD_CONTRACT_P2C_SAFEGUARD_KEYS`` are ignored so corrective
  metrics cannot overwrite contract blocks, legacy route counters, or
  ``trunk_edge_load_observation``.

Legacy:

- ``edges`` is a **deprecated** alias of
  ``transport_usage_load["existing_transport_cell_crossings"]`` (sorted string keys
  ``"x,y"``). Do not interpret as graph edge capacity.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    PASS3_TRUNK_EDGE_CONGESTION_WEIGHT_PER_TRAVERSAL,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    placement_commit_counts_by_state,
    unfinalized_placement_count_from_counts,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.step4.step4_routing_models import (
    Step4MutableState,
)

TRUNK_LOAD_CONTRACT_VERSION = 3
TRUNK_EDGE_LOAD_OBSERVATION_VERSION = 1
TRUNK_EDGE_LOAD_OBSERVATION_TOP_N = 10
TRUNK_EDGE_SHARED_THRESHOLD = 2

# Contract keys that must not be overwritten by ``p2c_metrics`` (defensive merge).
# P2-C metrics must use ``p2c_*`` or other non-contract diagnostic keys; not these names.
_TRUNK_LOAD_CONTRACT_P2C_SAFEGUARD_KEYS: frozenset[str] = frozenset(
    {
        "trunk_load_contract_version",
        "mode",
        "route_metrics",
        "trunk_load_by_kind",
        "transport_usage_load",
        "trunk_edge_load_observation",
        "edges",
        "step4_accumulated_route_cell_visits",
        "step4_final_route_cell_count",
        "step4_committed_trunk_cell_count_by_kind",
    }
)

# Stable keys for per-kind trunk load (extend with any extra ``transport_kind`` seen in-run).
_DEFAULT_TRUNK_KINDS: tuple[str, ...] = ("shape_belt", "fluid_pipe")


def canonical_trunk_edge_key(a: Coord, b: Coord) -> str:
    """Undirected edge key: sorted endpoints ``x,y`` match legacy cell string order."""

    lo, hi = sorted([a, b])
    return f"{lo[0]},{lo[1]}--{hi[0]},{hi[1]}"


def accumulate_trunk_edge_load(
    trunk_edge_load_by_kind: dict[str, dict[str, int]],
    transport_kind: str,
    path: Sequence[Coord],
) -> None:
    """Add one traversal count per consecutive cell pair in ``path`` (``len(path) < 2``: no-op)."""

    if len(path) < 2:
        return
    bucket = trunk_edge_load_by_kind.setdefault(transport_kind, {})
    for u, v in zip(path[:-1], path[1:], strict=True):
        ek = canonical_trunk_edge_key(u, v)
        bucket[ek] = bucket.get(ek, 0) + 1


def _normalized_trunk_edge_load_block(
    trunk_edge_load_by_kind: Mapping[str, Mapping[str, int]] | None,
    kind_keys: tuple[str, ...],
) -> dict[str, dict[str, int]]:
    src = trunk_edge_load_by_kind or {}
    return {k: dict(sorted((src.get(k) or {}).items())) for k in kind_keys}


def build_trunk_edge_load_observation(
    trunk_edge_block: Mapping[str, Mapping[str, int]],
    *,
    kind_keys: tuple[str, ...],
) -> dict[str, Any]:
    """Summarize ``trunk_edge_load`` per kind (observation-only; no routing or capacity effects).

    ``traversal_count_total`` = sum of counts for that kind's ``trunk_edge_load`` map (undirected
    canonical keys ``"x1,y1--x2,y2"``). ``top_edges[].edge`` uses that same key string.
    """

    by_kind: dict[str, Any] = {}
    for kind in kind_keys:
        em = trunk_edge_block.get(kind) or {}
        traversal_total = sum(em.values())
        edge_count = len(em)
        max_sharing = max(em.values()) if em else 0
        shared_edge_count = sum(1 for c in em.values() if c >= TRUNK_EDGE_SHARED_THRESHOLD)
        ordered = sorted(em.items(), key=lambda kv: (-kv[1], kv[0]))[
            :TRUNK_EDGE_LOAD_OBSERVATION_TOP_N
        ]
        top_edges = [{"edge": ek, "count": int(c)} for ek, c in ordered]
        by_kind[kind] = {
            "traversal_count_total": int(traversal_total),
            "max_sharing": int(max_sharing),
            "shared_edge_count": int(shared_edge_count),
            "edge_count": int(edge_count),
            "top_edges": top_edges,
        }
    return {
        "observation_version": TRUNK_EDGE_LOAD_OBSERVATION_VERSION,
        "top_n": TRUNK_EDGE_LOAD_OBSERVATION_TOP_N,
        "shared_threshold": TRUNK_EDGE_SHARED_THRESHOLD,
        "by_kind": by_kind,
    }


def _ordered_kind_keys(
    committed_trunk_by_kind: dict[str, set[Coord]],
    route_visits_by_kind: dict[str, int],
    unique_cells_by_kind: dict[str, set[Coord]],
) -> tuple[str, ...]:
    extra = (
        set(committed_trunk_by_kind) | set(route_visits_by_kind) | set(unique_cells_by_kind)
    ) - set(_DEFAULT_TRUNK_KINDS)
    return tuple(dict.fromkeys((*_DEFAULT_TRUNK_KINDS, *sorted(extra))))


def _pass3_effective_edge_traversal_count(v_all: int, v_max: int | None) -> int:
    """Pass3 congestion edge step count: linear ``v_all``, or split when maximized map is wired."""

    va = int(v_all)
    if va <= 0:
        return 0
    if v_max is None:
        return va
    vm = min(int(v_max), va)
    return (va - vm) + vm * vm


def build_step4_trunk_load(
    *,
    trunk_edge_hits: dict[str, int],
    route_cell_visits: int,
    final_route_cells: set[Coord],
    committed_trunk_by_kind: dict[str, set[Coord]],
    route_visits_by_kind: dict[str, int],
    unique_cells_by_kind: dict[str, set[Coord]],
    p2c_metrics: dict[str, Any],
    trace: dict[str, Any],
    trunk_edge_load_by_kind: Mapping[str, Mapping[str, int]] | None = None,
    trunk_edge_load_maximized_by_kind: Mapping[str, Mapping[str, int]] | None = None,
) -> dict[str, Any]:
    """Assemble the STEP4 ``trunk_load`` dict (nested contract + legacy flat keys + P2-C)."""

    crossings_sorted = dict(sorted(trunk_edge_hits.items()))
    unique_global = len(final_route_cells)
    by_kind_out: dict[str, dict[str, int]] = {}
    kind_keys = _ordered_kind_keys(
        committed_trunk_by_kind, route_visits_by_kind, unique_cells_by_kind
    )
    edge_only_kinds = set((trunk_edge_load_by_kind or {}).keys()) - set(kind_keys)
    if edge_only_kinds:
        kind_keys = tuple(dict.fromkeys((*kind_keys, *sorted(edge_only_kinds))))
    trunk_edge_block = _normalized_trunk_edge_load_block(trunk_edge_load_by_kind, kind_keys)
    trunk_max_block = _normalized_trunk_edge_load_block(
        trunk_edge_load_maximized_by_kind, kind_keys
    )
    trunk_edge_load_observation = build_trunk_edge_load_observation(
        trunk_edge_block, kind_keys=kind_keys
    )
    for k in kind_keys:
        cells_k = unique_cells_by_kind.get(k) or set()
        by_kind_out[k] = {
            "committed_trunk_cell_count": len(committed_trunk_by_kind.get(k, ())),
            "route_cell_visits": int(route_visits_by_kind.get(k, 0)),
            "unique_route_cell_count": len(cells_k),
        }

    reuse_ratio = (
        round(1.0 - float(unique_global) / float(route_cell_visits), 6)
        if route_cell_visits > 0
        else 0.0
    )
    out: dict[str, Any] = {
        "trunk_load_contract_version": TRUNK_LOAD_CONTRACT_VERSION,
        "mode": trace.get("mode", "accumulate_only"),
        "route_metrics": {
            "route_cell_visits": int(route_cell_visits),
            "unique_route_cell_count": int(unique_global),
            "shared_trunk_reuse_ratio": reuse_ratio,
        },
        "trunk_load_by_kind": by_kind_out,
        "transport_usage_load": {
            "existing_transport_cell_crossings": crossings_sorted,
            "trunk_edge_load": trunk_edge_block,
            "trunk_edge_load_from_maximized_placements": trunk_max_block,
        },
        "trunk_edge_load_observation": trunk_edge_load_observation,
        # Deprecated legacy aliases (keep one release; values mirror nested blocks above).
        "edges": crossings_sorted,
        "step4_accumulated_route_cell_visits": int(route_cell_visits),
        "step4_final_route_cell_count": int(unique_global),
        "step4_committed_trunk_cell_count_by_kind": {
            k: len(v) for k, v in sorted(committed_trunk_by_kind.items())
        },
    }
    for key, val in trace.items():
        if key == "mode":
            continue
        out[key] = val
    for key, val in p2c_metrics.items():
        if key in _TRUNK_LOAD_CONTRACT_P2C_SAFEGUARD_KEYS:
            continue
        out[key] = val
    return out


def build_step4_trunk_load_for_merge_state(
    state: Step4MutableState,
    *,
    p2c_metrics: dict[str, Any],
    trace: dict[str, Any],
) -> dict[str, Any]:
    """Assemble ``trunk_load`` from :class:`Step4MutableState` (runtime vs trace split at call)."""

    return build_step4_trunk_load(
        trunk_edge_hits=state.trunk.trunk_edge_hits,
        route_cell_visits=state.accumulated_route_cell_visits,
        final_route_cells=state.final_route_cells,
        committed_trunk_by_kind=state.committed_trunk_by_kind,
        route_visits_by_kind=state.route_visits_by_kind,
        unique_cells_by_kind=state.unique_cells_by_kind,
        p2c_metrics=p2c_metrics,
        trace=trace,
        trunk_edge_load_by_kind=state.trunk.trunk_edge_load_by_kind,
        trunk_edge_load_maximized_by_kind=state.trunk.trunk_edge_load_maximized_by_kind,
    )


def _empty_p2c_metrics() -> dict[str, Any]:
    return {
        "route_revalidation_passed": True,
        "broken_routed_route_count": 0,
        "cascade_corrective_attempts": 0,
        "cascade_reroute_count": 0,
        "cascade_rollback_count": 0,
        "cascade_rolled_back_placement_ids": tuple(),
        "cascade_route_replay_detail": [],
    }


def _zero_trace_common(*, pass12_skipped: bool) -> dict[str, Any]:
    pcounts = placement_commit_counts_by_state({})
    trace: dict[str, Any] = {
        "mode": "accumulate_only",
        "step4_route_count": 0,
        "step4_route_commit_count": 0,
        "step4_routing_failure_count": 0,
        "placement_commit_counts": pcounts,
        "unfinalized_placement_count": unfinalized_placement_count_from_counts(pcounts),
        "step4_routed_count": 0,
        "step4_rolled_back_count": 0,
        "step4_quarantined_count": 0,
        "step4_quarantined_unrouted_count": 0,
        "step4_trunk_seed_candidate_count_by_kind": {},
        "step4_trunk_seed_candidate_count": 0,
        "step4_goal_set_size_peak": 0,
        "step4_routed_stub_count": 0,
        "step4_total_stub_count": 0,
        "initial_trunk_cells": 0,
        "routes_by_placement_id": {},
        "step4_search_goal_ordering_applied": False,
        "step4_search_goal_ordering_mode": "none",
        "step4_search_diagnostics_samples": [],
    }
    if pass12_skipped:
        trace["skipped"] = True
        trace["step4_committed"] = True
        trace["step4_complete_routing_success"] = True
        trace["step4_degraded"] = False
        trace["step4_state_source"] = {
            "committed_from": "step4_skipped_no_work",
            "trunk_load_mirrors_result": True,
        }
    return trace


def build_step4_trunk_load_pipeline_exception_stub() -> dict[str, Any]:
    """Contract-aligned empty ``trunk_load`` before STEP4 (orchestration exception path).

    Distinguishable from Pass12-skipped STEP4: ``skipped`` is false and ``step4_result_state``
    is ``pipeline_exception`` (no STEP4 run; placeholder summary only).
    """

    trace = dict(_zero_trace_common(pass12_skipped=False))
    trace["skipped"] = False
    trace["step4_result_state"] = "pipeline_exception"
    return build_step4_trunk_load(
        trunk_edge_hits={},
        route_cell_visits=0,
        final_route_cells=set(),
        committed_trunk_by_kind={},
        route_visits_by_kind={},
        unique_cells_by_kind={},
        p2c_metrics=_empty_p2c_metrics(),
        trace=trace,
    )


def build_step4_trunk_load_skipped() -> dict[str, Any]:
    """``trunk_load`` when Pass12 skips STEP4 (same nested schema, counters at zero)."""

    return build_step4_trunk_load(
        trunk_edge_hits={},
        route_cell_visits=0,
        final_route_cells=set(),
        committed_trunk_by_kind={},
        route_visits_by_kind={},
        unique_cells_by_kind={},
        p2c_metrics=_empty_p2c_metrics(),
        trace=_zero_trace_common(pass12_skipped=True),
    )


def pass3_edge_congestion_weights_from_trunk_load(
    trunk_load: Mapping[str, Any] | None,
    *,
    transport_kind: str,
    weight_per_traversal: int | None = None,
) -> dict[str, int] | None:
    """Map STEP4 ``trunk_edge_load`` counts to Pass3 lex **congestion** edge weights (int, ≥0).

    Keys match :func:`canonical_trunk_edge_key`. When
    ``transport_usage_load["trunk_edge_load_from_maximized_placements"]`` carries a non-empty
    per-kind map, each edge uses :func:`_pass3_effective_edge_traversal_count` with ``v_max`` from
    that map; otherwise ``v_eff = v_all`` (older replays or no maximized traversals).

    Returns ``None`` when ``trunk_load`` is missing or has no per-kind edge map (Pass3 behaves as
    before).
    """

    if not isinstance(trunk_load, Mapping):
        return None
    raw_tul = trunk_load.get("transport_usage_load")
    if not isinstance(raw_tul, Mapping):
        return None
    raw_edges = raw_tul.get("trunk_edge_load")
    if not isinstance(raw_edges, Mapping):
        return None
    em = raw_edges.get(transport_kind)
    if not isinstance(em, Mapping) or not em:
        return None
    w = (
        int(weight_per_traversal)
        if weight_per_traversal is not None
        else int(PASS3_TRUNK_EDGE_CONGESTION_WEIGHT_PER_TRAVERSAL)
    )
    v_max_map: dict[str, int] | None = None
    raw_mx = raw_tul.get("trunk_edge_load_from_maximized_placements")
    if isinstance(raw_mx, Mapping):
        mx_kind = raw_mx.get(transport_kind)
        if isinstance(mx_kind, Mapping) and mx_kind:
            v_max_map = {str(k): int(v) for k, v in mx_kind.items() if int(v) > 0}

    def eff_weight(edge_key: str, v_all: int) -> int:
        v_max = v_max_map.get(edge_key) if v_max_map is not None else None
        ve = _pass3_effective_edge_traversal_count(v_all, v_max)
        if w <= 0:
            return ve
        return ve * w

    out: dict[str, int] = {}
    for k, v_all in em.items():
        key = str(k)
        va = int(v_all)
        if va <= 0:
            continue
        ew = eff_weight(key, va)
        if ew > 0:
            out[key] = ew
    return out or None


def cells_on_high_sharing_trunk_edges(
    trunk_load: Mapping[str, Any] | None,
    *,
    transport_kind: str,
    shared_threshold: int | None = None,
) -> frozenset[Coord]:
    """Endpoint cells of trunk edges whose STEP4 traversal count ≥ ``shared_threshold``."""

    thr = int(shared_threshold if shared_threshold is not None else TRUNK_EDGE_SHARED_THRESHOLD)
    wmap = pass3_edge_congestion_weights_from_trunk_load(
        trunk_load, transport_kind=transport_kind, weight_per_traversal=1
    )
    if not wmap:
        return frozenset()
    out: set[Coord] = set()
    for ek, c in wmap.items():
        if int(c) < thr:
            continue
        parts = str(ek).split("--", 1)
        if len(parts) != 2:
            continue
        try:
            a0, a1 = parts[0].split(",", 1)
            b0, b1 = parts[1].split(",", 1)
            out.add((int(a0), int(a1)))
            out.add((int(b0), int(b1)))
        except (TypeError, ValueError):
            continue
    return frozenset(out)


def compact_trunk_load_overlay_for_replay(
    trunk_load: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    """Small STEP10 overlay blob: observation ``by_kind`` + shared_threshold (no raw full maps)."""

    if not isinstance(trunk_load, Mapping):
        return None
    obs = trunk_load.get("trunk_edge_load_observation")
    if not isinstance(obs, Mapping):
        return None
    by_kind = obs.get("by_kind")
    if not isinstance(by_kind, Mapping) or not by_kind:
        return None
    slim: dict[str, Any] = {}
    for kind, block in sorted(by_kind.items()):
        if not isinstance(block, Mapping):
            continue
        slim[str(kind)] = {
            "traversal_count_total": int(block.get("traversal_count_total", 0) or 0),
            "max_sharing": int(block.get("max_sharing", 0) or 0),
            "shared_edge_count": int(block.get("shared_edge_count", 0) or 0),
            "top_edges": block.get("top_edges") if isinstance(block.get("top_edges"), list) else [],
        }
    return {
        "overlay_version": 1,
        "observation_version": int(obs.get("observation_version", 0) or 0),
        "top_n": int(obs.get("top_n", 0) or 0),
        "shared_threshold": int(obs.get("shared_threshold", TRUNK_EDGE_SHARED_THRESHOLD) or 0),
        "by_kind": slim,
        # Replay ``protected_corridors`` tiers (hard/soft/candidate) are routing_state pools;
        # this overlay counts only committed STEP4 painted route traversals (trunk_edge_load).
        "trunk_observation_layer": "committed_step4_routes",
        "corridor_state_note": "hard/soft/candidate cells: replay corridor_added + ui_frames",
    }
