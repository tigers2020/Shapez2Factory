"""P3-F: topology branch candidate semantics + replacement probe / commit trace.

A semantics layer on top of the P3-E3 guarded atomic candidate (DTO + validation + swap).
This module **never** mutates layout state and **never** introduces a new routing engine.
It classifies the existing replacement candidate into one of four branch kinds, computes
deterministic metrics, and emits a ``p3f_*`` trace dict consumed by ``pass3_transport``.

See ``documents/plans/plan_pass3_f_topology_branch_mvp_2026-05-11.md``.
"""

from __future__ import annotations

import math
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    MAX_ROUTE_LENGTH_RATIO,
    P3E3_REJECT_CONNECTIVITY,
    P3E3_REJECT_DISCONNECTED_STUB,
    P3E3_REJECT_EXTERNAL_UNREACHABLE_TRANSPORT,
    P3E3_REJECT_FIXED_STUB_REMOVAL,
    P3E3_REJECT_GEOMETRY,
    P3E3_REJECT_HARD_PROTECTED_CORRIDOR,
    P3E3_REJECT_NO_INTERNAL_TRANSPORT_GAIN,
    P3E3_REJECT_NO_REPLACEMENT_ROUTE,
    P3E3_REJECT_ORPHAN_TRANSPORT,
    P3E3_REJECT_PRECHECK_NO_CANDIDATE,
    P3E3_REJECT_PRECHECK_NO_REPLACEMENT_ROUTE,
    P3E3_REJECT_ROUTE_LENGTH_RATIO,
    P3E3_REJECT_VALIDATION,
    P3F_COMMIT_REASON_NORMAL_GAIN,
    P3F_KIND_LONG_PERIMETER_DETOUR,
    P3F_KIND_LOW_REUSE,
    P3F_KIND_MINEABLE_HEAVY,
    P3F_KIND_NONE,
    P3F_KIND_PARALLEL_DUPLICATE,
    P3F_KIND_PRIORITY_ORDER,
    P3F_LONG_DETOUR_RATIO_MIN,
    P3F_LOW_REUSE_RATIO_MAX,
    P3F_MINEABLE_HEAVY_RATIO_MIN,
    P3F_PARALLEL_ENDPOINT_MANHATTAN_MAX,
    P3F_PARALLEL_OVERLAP_RATIO_MAX,
    P3F_REJECTED_NO_REPLACEMENT_ROUTE,
    P3F_REJECTED_REASON_UNMAPPED,
    P3F_REPLACEMENT_SEARCH_MODE_LEX_PER_STUB,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.pass3.pass3_e3_guarded_dto import (
    P3E3GuardedCommitCandidate,
)

# Reason string for ``p3f_parallel_duplicate_inactive_reason`` when per-stub greedy paths
# are not threaded through the call site (MVP: paths are not collected for trace).
P3F_PARALLEL_INACTIVE_GREEDY_PATHS_UNAVAILABLE = "greedy_paths_unavailable"


__all__ = [
    "P3F_PARALLEL_INACTIVE_GREEDY_PATHS_UNAVAILABLE",
    "P3F_REJECT_REASON_TABLE",
    "p3f_build_trace",
    "p3f_disabled_trace",
    "p3f_map_rejected_reason",
    "p3f_pass3_summary_placeholder",
]


# P3-E3 reject constants → P3-F namespace. Anything not listed falls back to
# ``P3F_REJECTED_REASON_UNMAPPED`` with the raw string preserved in ``p3f_rejected_reason_raw``.
P3F_REJECT_REASON_TABLE: dict[str, str] = {
    P3E3_REJECT_PRECHECK_NO_REPLACEMENT_ROUTE: P3F_REJECTED_NO_REPLACEMENT_ROUTE,
    P3E3_REJECT_NO_REPLACEMENT_ROUTE: P3F_REJECTED_NO_REPLACEMENT_ROUTE,
    P3E3_REJECT_PRECHECK_NO_CANDIDATE: P3E3_REJECT_PRECHECK_NO_CANDIDATE,
    P3E3_REJECT_CONNECTIVITY: P3E3_REJECT_CONNECTIVITY,
    P3E3_REJECT_DISCONNECTED_STUB: P3E3_REJECT_DISCONNECTED_STUB,
    P3E3_REJECT_ORPHAN_TRANSPORT: P3E3_REJECT_ORPHAN_TRANSPORT,
    P3E3_REJECT_EXTERNAL_UNREACHABLE_TRANSPORT: P3E3_REJECT_EXTERNAL_UNREACHABLE_TRANSPORT,
    P3E3_REJECT_NO_INTERNAL_TRANSPORT_GAIN: P3E3_REJECT_NO_INTERNAL_TRANSPORT_GAIN,
    P3E3_REJECT_GEOMETRY: P3E3_REJECT_GEOMETRY,
    P3E3_REJECT_VALIDATION: P3E3_REJECT_VALIDATION,
    P3E3_REJECT_FIXED_STUB_REMOVAL: P3E3_REJECT_FIXED_STUB_REMOVAL,
    P3E3_REJECT_HARD_PROTECTED_CORRIDOR: P3E3_REJECT_HARD_PROTECTED_CORRIDOR,
    P3E3_REJECT_ROUTE_LENGTH_RATIO: P3E3_REJECT_ROUTE_LENGTH_RATIO,
}


def p3f_map_rejected_reason(raw: str | None) -> tuple[str | None, str | None]:
    """Map a P3-E3 reject constant to its P3-F namespace value.

    Returns ``(mapped, raw_if_unmapped)``. ``mapped`` is None when ``raw`` is None.
    When ``raw`` is provided but not in the table, ``mapped`` is the fallback string
    and ``raw_if_unmapped`` preserves the original.
    """

    if raw is None:
        return None, None
    if raw in P3F_REJECT_REASON_TABLE:
        return P3F_REJECT_REASON_TABLE[raw], None
    return P3F_REJECTED_REASON_UNMAPPED, raw


def _round6(x: float) -> float:
    return round(float(x), 6)


def _manhattan(a: Coord, b: Coord) -> int:
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def _sort_kinds_by_priority(kinds: list[str]) -> list[str]:
    """Sort detected kinds by ``P3F_KIND_PRIORITY_ORDER`` for stable UI/Replay ordering.

    Priority order is documented in
    ``documents/plans/plan_pass3_f_topology_branch_mvp_2026-05-11.md``.
    """

    found = set(kinds)
    return [k for k in P3F_KIND_PRIORITY_ORDER if k in found]


def _detect_parallel_duplicate(
    *,
    greedy_paths: list[list[Coord]] | None,
    trunk_cells: frozenset[Coord],
) -> bool:
    """Two stubs reach the same trunk with close endpoints and low overlap.

    Conservative: needs explicit per-stub paths. ``None`` disables this label and the
    caller emits ``p3f_parallel_duplicate_inactive_reason`` so consumers know the label
    is currently inactive (not “absent”).
    """

    if not greedy_paths or len(greedy_paths) < 2:
        return False
    sets: list[frozenset[Coord]] = [frozenset(p) for p in greedy_paths if p]
    if len(sets) < 2:
        return False
    for i in range(len(greedy_paths)):
        for j in range(i + 1, len(greedy_paths)):
            pi = greedy_paths[i]
            pj = greedy_paths[j]
            if not pi or not pj:
                continue
            end_i = pi[-1]
            end_j = pj[-1]
            if end_i not in trunk_cells or end_j not in trunk_cells:
                continue
            if _manhattan(end_i, end_j) > P3F_PARALLEL_ENDPOINT_MANHATTAN_MAX:
                continue
            shared = len(sets[i] & sets[j])
            max_len = max(len(pi), len(pj))
            if max_len <= 0:
                continue
            if shared / max_len <= P3F_PARALLEL_OVERLAP_RATIO_MAX:
                return True
    return False


def _detect_kinds(
    *,
    removed: frozenset[Coord],
    trunk_cells: frozenset[Coord],
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    sum_lex_len: int | None,
    sum_gr_len: int | None,
    greedy_paths: list[list[Coord]] | None,
) -> tuple[list[str], int, float, int, int]:
    """Return ``(kinds, mineable_freed, reuse_ratio, internal_removed, removed_count)``."""

    removed_count = len(removed)
    mineable_freed = len(removed & mineable)
    reuse_hits = len(removed & trunk_cells)
    reuse_ratio = _round6(reuse_hits / max(1, removed_count))
    internal_removed = len(removed & asteroid)

    kinds: list[str] = []

    if removed_count > 0:
        if mineable_freed / removed_count >= P3F_MINEABLE_HEAVY_RATIO_MIN:
            kinds.append(P3F_KIND_MINEABLE_HEAVY)
        if reuse_hits / removed_count <= P3F_LOW_REUSE_RATIO_MAX:
            kinds.append(P3F_KIND_LOW_REUSE)

    if (
        isinstance(sum_lex_len, int)
        and isinstance(sum_gr_len, int)
        and sum_lex_len > 0
        and sum_gr_len >= sum_lex_len * P3F_LONG_DETOUR_RATIO_MIN
    ):
        kinds.append(P3F_KIND_LONG_PERIMETER_DETOUR)

    if _detect_parallel_duplicate(greedy_paths=greedy_paths, trunk_cells=trunk_cells):
        kinds.append(P3F_KIND_PARALLEL_DUPLICATE)

    return kinds, mineable_freed, reuse_ratio, internal_removed, removed_count


def _best_kind(kinds: list[str]) -> str:
    found = set(kinds)
    for k in P3F_KIND_PRIORITY_ORDER:
        if k in found:
            return k
    return P3F_KIND_NONE


def _route_cell_delta_within_budget(
    *,
    baseline_route_length: int | None,
    candidate_route_length: int | None,
    max_route_length_ratio: float = MAX_ROUTE_LENGTH_RATIO,
) -> bool | None:
    """Mirror of ``_p3e3_route_length_ratio_allowed`` (ceil baseline * max_ratio)."""

    if baseline_route_length is None or candidate_route_length is None:
        return None
    if baseline_route_length <= 0:
        return candidate_route_length <= 0
    allowed = int(math.ceil(float(baseline_route_length) * float(max_route_length_ratio)))
    return candidate_route_length <= allowed


def p3f_pass3_summary_placeholder(*, rejected_reason: str | None) -> dict[str, Any]:
    """Stable ``p3f_*`` keys when the Pass3 P3-F path does not run (parity with P3-E3)."""

    return {
        "p3f_candidate_kind_count": None,
        "p3f_best_candidate_kind": None,
        "p3f_candidate_kinds": None,
        "p3f_candidate_internal_cells": None,
        "p3f_candidate_mineable_freed": None,
        "p3f_candidate_reuse_ratio": None,
        "p3f_candidate_score_tuple": None,
        "p3f_replacement_connected": None,
        "p3f_fixed_output_stub_preserved": None,
        "p3f_hard_protected_preserved": None,
        "p3f_internal_transport_delta": None,
        "p3f_route_cell_delta": None,
        "p3f_route_cell_delta_within_budget": None,
        "p3f_replacement_search_mode": None,
        "p3f_replacement_expanded_nodes": None,
        "p3f_replacement_search_ms": None,
        "p3f_parallel_duplicate_inactive_reason": None,
        "p3f_committed": None,
        "p3f_transport_cells_added": None,
        "p3f_transport_cells_removed": None,
        "p3f_internal_transport_saved": None,
        "p3f_commit_reason": None,
        "p3f_rejected_reason": rejected_reason,
        "p3f_rejected_reason_raw": None,
    }


def p3f_disabled_trace() -> dict[str, Any]:
    """Default ``p3f_*`` fields when guarded atomic phase did not run (parity with P3-E3)."""

    return {
        "p3f_candidate_kind_count": 0,
        "p3f_best_candidate_kind": P3F_KIND_NONE,
        "p3f_candidate_kinds": [],
        "p3f_candidate_internal_cells": 0,
        "p3f_candidate_mineable_freed": 0,
        "p3f_candidate_reuse_ratio": 0.0,
        "p3f_candidate_score_tuple": [0, 0.0, 0, 0],
        "p3f_replacement_connected": None,
        "p3f_fixed_output_stub_preserved": None,
        "p3f_hard_protected_preserved": None,
        "p3f_internal_transport_delta": None,
        "p3f_route_cell_delta": None,
        "p3f_route_cell_delta_within_budget": None,
        "p3f_replacement_search_mode": None,
        "p3f_replacement_expanded_nodes": None,
        "p3f_replacement_search_ms": None,
        "p3f_parallel_duplicate_inactive_reason": P3F_PARALLEL_INACTIVE_GREEDY_PATHS_UNAVAILABLE,
        "p3f_committed": False,
        "p3f_transport_cells_added": 0,
        "p3f_transport_cells_removed": 0,
        "p3f_internal_transport_saved": 0,
        "p3f_commit_reason": None,
        "p3f_rejected_reason": None,
        "p3f_rejected_reason_raw": None,
    }


def p3f_build_trace(
    *,
    dto: P3E3GuardedCommitCandidate,
    baseline_internal_transport_count: int,
    candidate_internal_transport_count: int,
    fixed_output_stubs: frozenset[Coord],
    hard_protected_corridors: frozenset[Coord],
    trunk_cells: frozenset[Coord],
    mineable: frozenset[Coord],
    asteroid: frozenset[Coord],
    sum_lex_len: int | None,
    sum_gr_len: int | None,
    greedy_paths: list[list[Coord]] | None,
    committed: bool,
    rejected_reason_raw: str | None,
    internal_transport_saved: int,
    search_ms: int,
    expanded_nodes: int | None,
    route_length_ratio_max: float = MAX_ROUTE_LENGTH_RATIO,
) -> dict[str, Any]:
    """Compose the ``p3f_*`` trace from the existing P3-E3 DTO and Pass3 context."""

    removed = dto.removed_transport_cells
    added = dto.added_transport_cells
    candidate_tc = dto.candidate_transport_cells

    kinds, mineable_freed, reuse_ratio, internal_removed, _removed_count = _detect_kinds(
        removed=removed,
        trunk_cells=trunk_cells,
        mineable=mineable,
        asteroid=asteroid,
        sum_lex_len=sum_lex_len,
        sum_gr_len=sum_gr_len,
        greedy_paths=greedy_paths,
    )

    internal_delta = candidate_internal_transport_count - baseline_internal_transport_count
    if dto.baseline_route_length is None or dto.candidate_route_length is None:
        route_cell_delta: int | None = None
    else:
        route_cell_delta = int(dto.candidate_route_length) - int(dto.baseline_route_length)
    route_cell_delta_within_budget = _route_cell_delta_within_budget(
        baseline_route_length=dto.baseline_route_length,
        candidate_route_length=dto.candidate_route_length,
        max_route_length_ratio=route_length_ratio_max,
    )

    fixed_stub_preserved = fixed_output_stubs.issubset(candidate_tc) if candidate_tc else False
    hard_preserved = (
        True if not hard_protected_corridors else hard_protected_corridors.issubset(candidate_tc)
    )

    # ``p3f_replacement_connected`` reports the P3-E3 precheck outcome (lex + greedy probes
    # succeeded for every stub and the DTO carries no ``rejected_reason``). It is *not* a
    # standalone connectivity probe; downstream connectivity is asserted by
    # ``_p3e3_validate_candidate_transport_map`` and reflected via the rejected-reason path.
    if dto.attempted and dto.precheck_passed and dto.rejected_reason is None:
        replacement_connected: bool | None = True
    elif dto.attempted:
        replacement_connected = False
    else:
        replacement_connected = None

    score_tuple: list[Any] = [
        int(internal_delta),
        float(reuse_ratio),
        int(mineable_freed),
        int(route_cell_delta) if route_cell_delta is not None else 0,
    ]

    commit_reason: str | None = P3F_COMMIT_REASON_NORMAL_GAIN if committed else None

    if committed:
        rejected_mapped: str | None = None
        rejected_raw_kept: str | None = None
    else:
        rejected_mapped, rejected_raw_kept = p3f_map_rejected_reason(rejected_reason_raw)

    parallel_inactive_reason: str | None = (
        P3F_PARALLEL_INACTIVE_GREEDY_PATHS_UNAVAILABLE if not greedy_paths else None
    )

    return {
        "p3f_candidate_kind_count": len(kinds),
        "p3f_best_candidate_kind": _best_kind(kinds),
        "p3f_candidate_kinds": _sort_kinds_by_priority(kinds),
        "p3f_candidate_internal_cells": internal_removed,
        "p3f_candidate_mineable_freed": mineable_freed,
        "p3f_candidate_reuse_ratio": reuse_ratio,
        "p3f_candidate_score_tuple": score_tuple,
        "p3f_replacement_connected": replacement_connected,
        "p3f_fixed_output_stub_preserved": fixed_stub_preserved,
        "p3f_hard_protected_preserved": hard_preserved,
        "p3f_internal_transport_delta": int(internal_delta),
        "p3f_route_cell_delta": route_cell_delta,
        "p3f_route_cell_delta_within_budget": route_cell_delta_within_budget,
        "p3f_replacement_search_mode": P3F_REPLACEMENT_SEARCH_MODE_LEX_PER_STUB,
        "p3f_replacement_expanded_nodes": expanded_nodes,
        "p3f_replacement_search_ms": int(search_ms),
        "p3f_parallel_duplicate_inactive_reason": parallel_inactive_reason,
        "p3f_committed": bool(committed),
        "p3f_transport_cells_added": len(added),
        "p3f_transport_cells_removed": len(removed),
        "p3f_internal_transport_saved": int(internal_transport_saved),
        "p3f_commit_reason": commit_reason,
        "p3f_rejected_reason": rejected_mapped,
        "p3f_rejected_reason_raw": rejected_raw_kept,
    }
