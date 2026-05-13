"""P4 protected corridor runtime authority and replay-side probe parsing.

Runtime hard/soft corridor authority comes only from STEP4 ``routing_state``. Trace, replay,
Pass3 trace, and ``trunk_load`` payloads are output-only and must not synthesize reclaim guards.
"""

from __future__ import annotations

from collections.abc import Mapping

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    P4_RECLAIM_CORRIDOR_SOURCE_EMPTY,
    P4_RECLAIM_CORRIDOR_SOURCE_SOLVER_POOL,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridor_contracts import (  # noqa: E501
    ProtectedCorridors,
    ProtectedCorridorSets,
)


def _parse_coord_pairs_from_trace_list(val: object) -> frozenset[Coord]:
    """Normalize ``[[x,y], ...]`` trace lists to coords (``x != 0``)."""

    if not isinstance(val, list):
        return frozenset()
    out: set[Coord] = set()
    for it in val:
        if isinstance(it, (list, tuple)) and len(it) >= 2:
            try:
                x = int(it[0])
                y = int(it[1])
            except (TypeError, ValueError):
                continue
            if x == 0:
                continue
            out.add((x, y))
    return frozenset(out)


def _probe_lifecycle_cells_from_pass3_trace(
    pass3_trace: Mapping[str, object],
) -> tuple[frozenset[Coord], frozenset[Coord]]:
    """Return ``(probe_candidate_cells, probe_discarded_cells)`` from Pass3 trace only."""

    cand = _parse_coord_pairs_from_trace_list(pass3_trace.get("corridor_probe_candidate_cells"))
    disc = _parse_coord_pairs_from_trace_list(pass3_trace.get("corridor_probe_discarded_cells"))
    return cand, disc


def _parse_coord_pair_frozenset(val: object) -> frozenset[Coord]:
    """Parse JSON-like ``[[x,y], ...]``, ``set``/``frozenset`` of ``(x, y)`` pairs."""

    if val is None:
        return frozenset()
    if isinstance(val, (frozenset, set)):
        out: set[Coord] = set()
        for it in val:
            if isinstance(it, tuple) and len(it) == 2:
                x, y = it[0], it[1]
                if isinstance(x, int) and isinstance(y, int) and x != 0:
                    out.add((x, y))
        return frozenset(out)
    if not isinstance(val, list):
        return frozenset()
    out_ls: set[Coord] = set()
    for it in val:
        if isinstance(it, (list, tuple)) and len(it) == 2:
            x, y = it[0], it[1]
            if isinstance(x, int) and isinstance(y, int) and x != 0:
                out_ls.add((x, y))
    return frozenset(out_ls)


def _effective_solver_routing_mapping(m: Mapping[str, object]) -> Mapping[str, object]:
    """Overlay nested ``routing_state`` corridor keys for pool detection (wrapper input)."""

    inner = m.get("routing_state")
    if not isinstance(inner, Mapping):
        return m
    base = {k: v for k, v in m.items() if k != "routing_state"}
    overlay: dict[str, object] = {}
    for k in ("hard_protected_corridors", "soft_protected_corridors", "protected_corridors"):
        if k in inner:
            overlay[k] = inner[k]
    if not overlay and not base:
        return m
    return {**base, **overlay}


def _corridor_payload_non_empty(merged: Mapping[str, object]) -> bool:
    """True when any hard/soft corridor list under ``merged`` has at least one coordinate pair."""

    for k in ("hard_protected_corridors", "soft_protected_corridors"):
        v = merged.get(k)
        if isinstance(v, list) and len(v) > 0:
            return True
    pc = merged.get("protected_corridors")
    if isinstance(pc, Mapping):
        for sub in ("hard", "soft"):
            vv = pc.get(sub)
            if isinstance(vv, list) and len(vv) > 0:
                return True
    return False


def merge_step4_corridor_routing_mapping(
    *,
    routing_state: Mapping[str, object] | None,
    trunk_load: Mapping[str, object] | None,
) -> dict[str, object] | None:
    """Return STEP4 ``routing_state`` corridor keys without telemetry fallback.

    ``trunk_load`` is accepted only to preserve the caller contract; it is an output mirror and
    never supplies runtime corridor authority.
    """

    _ = trunk_load
    merged: dict[str, object] = {}
    rs = routing_state if isinstance(routing_state, Mapping) else None
    if isinstance(rs, dict):
        inner_pc = rs.get("protected_corridors")
        if isinstance(inner_pc, Mapping):
            merged["protected_corridors"] = dict(inner_pc)
        for k in ("hard_protected_corridors", "soft_protected_corridors"):
            if k in rs:
                merged[k] = rs[k]
        if merged and "source" in rs:
            merged["source"] = rs["source"]
    m_pc_out = merged.get("protected_corridors")
    hh = merged.get("hard_protected_corridors")
    ss = merged.get("soft_protected_corridors")
    if isinstance(m_pc_out, Mapping) and not _corridor_payload_non_empty(
        {"protected_corridors": m_pc_out}
    ):
        if (isinstance(hh, list) and len(hh) > 0) or (isinstance(ss, list) and len(ss) > 0):
            merged["protected_corridors"] = {
                "hard": list(hh) if isinstance(hh, list) else [],
                "soft": list(ss) if isinstance(ss, list) else [],
            }
    return merged if merged else None


def solver_routing_state_for_p4_reclaim(step4_result: object) -> Mapping[str, object] | None:
    """Return Step4 ``routing_state`` corridor fields for P4 reclaim.

    ``trunk_load`` is intentionally ignored because it is a replay/summary mirror, not runtime
    authority.
    """

    rs = getattr(step4_result, "routing_state", None)
    return merge_step4_corridor_routing_mapping(
        routing_state=rs if isinstance(rs, dict) else None,
        trunk_load=None,
    )


def _solver_pool_corridors_available(solver_routing_state: Mapping[str, object]) -> bool:
    """Return whether runtime routing_state contains non-empty protected corridor authority."""

    return _corridor_payload_non_empty(solver_routing_state)


# NOTE: Reclaim corridor merging intentionally differs from replay overlay merging
# (:mod:`reclaim_corridor_read_factory`). Replay preserves UI-facing flat-key precedence when
# both flat lists and nested ``protected_corridors`` exist. Reclaim uses nested ``hard``/``soft``
# keys when present (runtime reclaim / §12.2 pool). Do not unify without P3-C write-authority
# review.


def _corridors_from_solver_routing_state(
    solver_routing_state: Mapping[str, object],
) -> ProtectedCorridorSets:
    """routing_state에서 hard/soft protected corridor sets를 복원한다 (§12.2 budget)."""
    hard = _parse_coord_pair_frozenset(solver_routing_state.get("hard_protected_corridors"))
    soft = _parse_coord_pair_frozenset(solver_routing_state.get("soft_protected_corridors"))
    nested = solver_routing_state.get("protected_corridors")
    if isinstance(nested, Mapping):
        if "hard" in nested:
            hard = _parse_coord_pair_frozenset(nested.get("hard"))
        if "soft" in nested:
            soft = _parse_coord_pair_frozenset(nested.get("soft"))
    return ProtectedCorridorSets(
        hard=hard,
        soft=soft,
        source=P4_RECLAIM_CORRIDOR_SOURCE_SOLVER_POOL,
        existing_layout_hints_cells=frozenset(),
    )


def _attach_existing_layout_solver_hints(
    base: ProtectedCorridorSets,
    existing_layout_solver_hints: Mapping[str, object] | None,
) -> ProtectedCorridorSets:
    """Keep STEP 0.5 hints as diagnostics only; never promote them to hard/soft authority."""

    if not isinstance(existing_layout_solver_hints, Mapping):
        return base
    trunk = _parse_coord_pair_frozenset(existing_layout_solver_hints.get("trunk_seed_cell_union"))
    cleanup = _parse_coord_pair_frozenset(
        existing_layout_solver_hints.get("cleanup_candidate_cell_union")
    )
    hint_cells = trunk | cleanup
    if not hint_cells:
        return base
    return ProtectedCorridorSets(
        hard=base.hard,
        soft=base.soft,
        source=base.source,
        existing_layout_hints_cells=hint_cells,
    )


def protected_corridors_for_reclaim(
    *,
    pass3_trace: Mapping[str, object],
    solver_routing_state: Mapping[str, object] | None = None,
    existing_layout_solver_hints: Mapping[str, object] | None = None,
) -> ProtectedCorridorSets:
    """Select hard/soft protected corridors for Reclaim from runtime route state only.

    ``pass3_trace`` remains in the signature for replay/debug callers, but it is output-only and
    never reconstructs runtime hard/soft authority.
    """

    _ = pass3_trace
    eff: Mapping[str, object] | None = None
    if isinstance(solver_routing_state, Mapping):
        eff = _effective_solver_routing_mapping(solver_routing_state)
    base: ProtectedCorridorSets
    if eff is not None and _solver_pool_corridors_available(eff):
        base = _corridors_from_solver_routing_state(eff)
    else:
        base = ProtectedCorridorSets(
            hard=frozenset(),
            soft=frozenset(),
            source=P4_RECLAIM_CORRIDOR_SOURCE_EMPTY,
            existing_layout_hints_cells=frozenset(),
        )
    return _attach_existing_layout_solver_hints(base, existing_layout_solver_hints)


def protected_corridors_read_for_reclaim(
    *,
    pass3_trace: Mapping[str, object],
    solver_routing_state: Mapping[str, object] | None = None,
    existing_layout_solver_hints: Mapping[str, object] | None = None,
) -> ProtectedCorridors:
    """Same pool selection as :func:`protected_corridors_for_reclaim`, unified read DTO (P3-B)."""

    pcs = protected_corridors_for_reclaim(
        pass3_trace=pass3_trace,
        solver_routing_state=solver_routing_state,
        existing_layout_solver_hints=existing_layout_solver_hints,
    )
    probe_cand, probe_disc = _probe_lifecycle_cells_from_pass3_trace(pass3_trace)
    return ProtectedCorridors(
        hard=pcs.hard,
        soft=pcs.soft,
        candidate=pcs.existing_layout_hints_cells,
        source=pcs.source,
        probe_candidate_cells=probe_cand,
        probe_discarded_cells=probe_disc,
    )


protected_corridors_for_reclaim_from_solver_state = protected_corridors_for_reclaim
