"""STEP4 ``trunk_load`` payload contract (accumulate-only metrics, no capacity gates).

Contract version ``trunk_load_contract_version`` (int) identifies the nested schema for
replay/UI consumers.

Nested blocks (v1):

- ``route_metrics``: ``route_cell_visits`` (sum of committed path lengths; double-counts
  shared cells) vs ``unique_route_cell_count`` (``|union of committed path cells|``).
- ``trunk_load_by_kind``: per ``transport_kind`` committed trunk size, visits, and kind-local
  unique path cells (diagnostic; global unique may differ if kinds ever overlap — not expected
  for shape vs fluid in the MVP split).
- ``transport_usage_load``:
  - ``existing_transport_cell_crossings``: counts **entries onto pre-existing transport cells**
    of the routed role during path paint (same map as legacy ``edges``). This is **not** full
  route-cell load and **not** graph edge load.
  - ``trunk_edge_load``: per ``transport_kind`` undirected corridor edge keys
    ``"x1,y1--x2,y2"`` (sorted endpoints) counting route path step traversals. Separate from
    ``existing_transport_cell_crossings`` / legacy ``edges`` (pre-existing transport cell entries).

Merge safety:

- ``p2c_metrics`` keys in ``_TRUNK_LOAD_V1_P2C_SAFEGUARD_KEYS`` are ignored so corrective
  metrics cannot overwrite the v1 contract block or legacy route counters.

Legacy:

- ``edges`` is a **deprecated** alias of
  ``transport_usage_load["existing_transport_cell_crossings"]`` (sorted string keys
  ``"x,y"``). Do not interpret as graph edge capacity.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    placement_commit_counts_by_state,
    unfinalized_placement_count_from_counts,
)

TRUNK_LOAD_CONTRACT_VERSION = 1

# v1 keys that must not be overwritten by ``p2c_metrics`` (defensive merge).
# P2-C metrics must use ``p2c_*`` or other non-contract diagnostic keys — not these names.
_TRUNK_LOAD_V1_P2C_SAFEGUARD_KEYS: frozenset[str] = frozenset(
    {
        "trunk_load_contract_version",
        "mode",
        "route_metrics",
        "trunk_load_by_kind",
        "transport_usage_load",
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
    for u, v in zip(path, path[1:], strict=True):
        ek = canonical_trunk_edge_key(u, v)
        bucket[ek] = bucket.get(ek, 0) + 1


def _normalized_trunk_edge_load_block(
    trunk_edge_load_by_kind: Mapping[str, Mapping[str, int]] | None,
    kind_keys: tuple[str, ...],
) -> dict[str, dict[str, int]]:
    src = trunk_edge_load_by_kind or {}
    return {k: dict(sorted((src.get(k) or {}).items())) for k in kind_keys}


def _ordered_kind_keys(
    committed_trunk_by_kind: dict[str, set[Coord]],
    route_visits_by_kind: dict[str, int],
    unique_cells_by_kind: dict[str, set[Coord]],
) -> tuple[str, ...]:
    extra = (
        set(committed_trunk_by_kind) | set(route_visits_by_kind) | set(unique_cells_by_kind)
    ) - set(_DEFAULT_TRUNK_KINDS)
    return tuple(dict.fromkeys((*_DEFAULT_TRUNK_KINDS, *sorted(extra))))


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
    for k in kind_keys:
        cells_k = unique_cells_by_kind.get(k) or set()
        by_kind_out[k] = {
            "committed_trunk_cell_count": len(committed_trunk_by_kind.get(k, ())),
            "route_cell_visits": int(route_visits_by_kind.get(k, 0)),
            "unique_route_cell_count": len(cells_k),
        }

    out: dict[str, Any] = {
        "trunk_load_contract_version": TRUNK_LOAD_CONTRACT_VERSION,
        "mode": trace.get("mode", "accumulate_only"),
        "route_metrics": {
            "route_cell_visits": int(route_cell_visits),
            "unique_route_cell_count": int(unique_global),
        },
        "trunk_load_by_kind": by_kind_out,
        "transport_usage_load": {
            "existing_transport_cell_crossings": crossings_sorted,
            "trunk_edge_load": trunk_edge_block,
        },
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
        if key in _TRUNK_LOAD_V1_P2C_SAFEGUARD_KEYS:
            continue
        out[key] = val
    return out


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
    }
    if pass12_skipped:
        trace["skipped"] = True
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
