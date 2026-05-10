"""P4 protected corridor parsing, Pass3 touched fallback, canonical pool selection."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    P4_RECLAIM_CORRIDOR_SOURCE_EMPTY,
    P4_RECLAIM_CORRIDOR_SOURCE_P3E3_TOUCHED_FALLBACK,
    P4_RECLAIM_CORRIDOR_SOURCE_PASS3_TRACE,
    P4_RECLAIM_CORRIDOR_SOURCE_SOLVER_POOL,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.reclaim.reclaim_corridor_contracts import (  # noqa: E501
    ProtectedCorridorSets,
)


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


def solver_routing_state_for_p4_reclaim(step4_result: object) -> Mapping[str, object] | None:
    """Merge Step4 ``routing_state`` corridor fields, then ``trunk_load`` legacy keys.

    Prefer semantic ``routing_state`` (protected pool / policy). When ``routing_state``
    declares any corridor key (``hard_protected_corridors``, ``soft_protected_corridors``,
    or ``protected_corridors``), those values win **unless every list is empty** — then
    ``trunk_load`` legacy corridor keys still bridge into P4 (stub-in-trunk gaps, §12).

    If ``routing_state`` omits corridor keys entirely, ``trunk_load`` supplies legacy
    ``hard_protected_corridors`` / ``soft_protected_corridors`` / nested
    ``protected_corridors`` as a temporary bridge.
    """

    merged: dict[str, object] = {}
    rs = getattr(step4_result, "routing_state", None)
    rs_has_corridor_keys = False
    if isinstance(rs, dict):
        rs_has_corridor_keys = any(
            k in rs
            for k in ("hard_protected_corridors", "soft_protected_corridors", "protected_corridors")
        )
        inner_pc = rs.get("protected_corridors")
        if isinstance(inner_pc, Mapping):
            merged["protected_corridors"] = dict(inner_pc)
        for k in ("hard_protected_corridors", "soft_protected_corridors"):
            if k in rs:
                merged[k] = rs[k]
    tl_raw = getattr(step4_result, "trunk_load", None)
    if isinstance(tl_raw, dict):
        use_trunk_bridge = not rs_has_corridor_keys or not _corridor_payload_non_empty(merged)
        if use_trunk_bridge:
            m_pc = merged.get("protected_corridors")
            if "protected_corridors" not in merged:
                tl_pc = tl_raw.get("protected_corridors")
                if isinstance(tl_pc, Mapping):
                    merged["protected_corridors"] = dict(tl_pc)
            elif isinstance(m_pc, Mapping) and not _corridor_payload_non_empty(
                {"protected_corridors": m_pc}
            ):
                tl_pc = tl_raw.get("protected_corridors")
                if isinstance(tl_pc, Mapping) and _corridor_payload_non_empty(
                    {"protected_corridors": tl_pc}
                ):
                    merged["protected_corridors"] = dict(tl_pc)
            for k in ("hard_protected_corridors", "soft_protected_corridors"):
                cur = merged.get(k)
                missing_or_empty = k not in merged or (isinstance(cur, list) and len(cur) == 0)
                if missing_or_empty and k in tl_raw:
                    merged[k] = tl_raw[k]
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


def _solver_pool_corridors_available(solver_routing_state: Mapping[str, object]) -> bool:
    """solver routing_state에 Reclaim loop corridor pool이 있는지 확인한다 (§12.2)."""
    if (
        "hard_protected_corridors" in solver_routing_state
        or "soft_protected_corridors" in solver_routing_state
    ):
        return True
    nested = solver_routing_state.get("protected_corridors")
    return isinstance(nested, Mapping) and ("hard" in nested or "soft" in nested)


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


def _corridors_from_pass3_trace_protected_block(
    pass3_trace: Mapping[str, object],
) -> ProtectedCorridorSets | None:
    """Pass3 trace protected block에서 Reclaim corridor sets를 복원한다 (§12.2)."""
    raw = pass3_trace.get("protected_corridors")
    if not isinstance(raw, Mapping):
        return None
    if "hard" not in raw and "soft" not in raw:
        return None
    return ProtectedCorridorSets(
        hard=_parse_coord_pair_frozenset(raw.get("hard")),
        soft=_parse_coord_pair_frozenset(raw.get("soft")),
        source=P4_RECLAIM_CORRIDOR_SOURCE_PASS3_TRACE,
        existing_layout_hints_cells=frozenset(),
    )


def hard_soft_corridors_from_pass3_trace(
    pass3_trace: dict[str, Any],
) -> tuple[frozenset[Coord], frozenset[Coord]]:
    """Parse P3-E3 guarded candidate ``touched_*`` lists only (read-only).

    This extracts **candidate-touched** hard/soft cells from ``p3e3_guarded_commit_candidate``;
    it is **not** the full protected corridor pool used for STEP 6 reclaim exclusions.
    For reclaim, use :func:`protected_corridors_for_reclaim` instead.
    """

    raw = pass3_trace.get("p3e3_guarded_commit_candidate")
    if not isinstance(raw, dict):
        return frozenset(), frozenset()

    def _pairs(key: str) -> frozenset[Coord]:
        """Pass3 trace 좌표 배열을 corridor pair iterator로 변환한다 (§12.2)."""
        lst = raw.get(key)
        if not isinstance(lst, list):
            return frozenset()
        out: set[Coord] = set()
        for it in lst:
            if isinstance(it, (list, tuple)) and len(it) == 2:
                x, y = it[0], it[1]
                if isinstance(x, int) and isinstance(y, int) and x != 0:
                    out.add((x, y))
        return frozenset(out)

    return _pairs("touched_hard_protected_cells"), _pairs("touched_soft_protected_cells")


def _merge_existing_layout_solver_hints_into_soft(
    base: ProtectedCorridorSets,
    existing_layout_solver_hints: Mapping[str, object] | None,
) -> ProtectedCorridorSets:
    """Union STEP 0.5 hint cells into *soft* only; *hard* from Step4/Pass3 always wins (§14.2.3).

    ``trunk_seed_cell_union`` (``main_trunk_candidate``) and ``cleanup_candidate_cell_union``
    (orphan / artifact / ``cleanup_candidate``) are both treated as **soft** exclusions for P4
    reclaim mineable/probe overlap: conservative merge so existing transport footprint is not
    stomped before the semantic corridor pool classifies them.
    """

    if not isinstance(existing_layout_solver_hints, Mapping):
        return base
    trunk = _parse_coord_pair_frozenset(existing_layout_solver_hints.get("trunk_seed_cell_union"))
    cleanup = _parse_coord_pair_frozenset(
        existing_layout_solver_hints.get("cleanup_candidate_cell_union")
    )
    hint_cells = trunk | cleanup
    if not hint_cells:
        return base
    new_soft = (base.soft | hint_cells) - base.hard
    return ProtectedCorridorSets(
        hard=base.hard,
        soft=new_soft,
        source=base.source,
        existing_layout_hints_cells=hint_cells,
    )


def protected_corridors_for_reclaim(
    *,
    pass3_trace: Mapping[str, object],
    solver_routing_state: Mapping[str, object] | None = None,
    existing_layout_solver_hints: Mapping[str, object] | None = None,
) -> ProtectedCorridorSets:
    """Select hard/soft protected corridors for Reclaim (canonical source priority).

    Order: (1) solver-level pool on ``solver_routing_state`` (including nested
    ``routing_state`` corridor keys), (2) ``pass3_trace`` key ``protected_corridors``
    with ``hard`` / ``soft`` lists, (3) P3-E3 guarded candidate ``touched_*`` cells via
    :func:`hard_soft_corridors_from_pass3_trace`, (4) empty sets.

    Prefer passing the dict from :func:`solver_routing_state_for_p4_reclaim` so Step4
    semantic ``routing_state`` wins over ``trunk_load`` corridor fallbacks.

    Trace consumers should record ``source`` for diagnostics (unchanged when hints merge;
    see ``existing_layout_hints_cells`` on the DTO).

    After the base pool is chosen, ``existing_layout_solver_hints`` (typically
    ``existing_layout_analysis["solver_hints"]``) is merged into **soft** only; see
    :func:`_merge_existing_layout_solver_hints_into_soft`.
    """

    eff: Mapping[str, object] | None = None
    if isinstance(solver_routing_state, Mapping):
        eff = _effective_solver_routing_mapping(solver_routing_state)
    base: ProtectedCorridorSets
    if eff is not None and _solver_pool_corridors_available(eff):
        base = _corridors_from_solver_routing_state(eff)
    else:
        from_pass3 = _corridors_from_pass3_trace_protected_block(pass3_trace)
        if from_pass3 is not None:
            base = from_pass3
        else:
            p3_dict = pass3_trace if isinstance(pass3_trace, dict) else dict(pass3_trace)
            th, ts = hard_soft_corridors_from_pass3_trace(p3_dict)
            if th or ts:
                base = ProtectedCorridorSets(
                    hard=th,
                    soft=ts,
                    source=P4_RECLAIM_CORRIDOR_SOURCE_P3E3_TOUCHED_FALLBACK,
                    existing_layout_hints_cells=frozenset(),
                )
            else:
                base = ProtectedCorridorSets(
                    hard=frozenset(),
                    soft=frozenset(),
                    source=P4_RECLAIM_CORRIDOR_SOURCE_EMPTY,
                    existing_layout_hints_cells=frozenset(),
                )
    return _merge_existing_layout_solver_hints_into_soft(base, existing_layout_solver_hints)


protected_corridors_for_reclaim_from_solver_state = protected_corridors_for_reclaim
