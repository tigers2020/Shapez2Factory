"""Seed Pass12LayoutScratch from merged with_transport+final map (preserve-first).

Mineable cells that already hold extractors/extensions must block Pass1/Pass2 from
treating them as empty slots (see ``scratch_from_working_map`` mineable-only blocked rule).
"""

from __future__ import annotations

import copy
import heapq
from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Any, Literal

from django.conf import settings

from django_apps.shapez_asteroid.extraction.shape_miner_rotation import (
    output_offset_r,
    rotation_r_for_output_direction,
    shape_miner_output_cell,
)
from django_apps.shapez_asteroid.extraction.shapez_grid import (
    neighbors4,
    require_cardinal_unit_toward,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    MAX_PASS12_NEAREST_TRANSPORT_TRACE_HOPS,
    MAX_PASS12_RECOVERY_BFS_HOPS,
    MAX_PASS12_RECOVERY_PROBES_PER_MINER,
    MAX_PASS12_STUB_ROUTE_RECOVERY_NEAREST_HOPS,
    PASS12_MAX_EXTENSION_TILES,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.extension_topology import (  # noqa: E501
    rotation_r_for_extension_facing_parent,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_contracts import (
    Pass12LayoutScratch,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.pass12_preserve_stub_route_recovery import (  # noqa: E501
    StubRouteRecoveryResult,
    _empty_psr,
    _no_same_kind_route_subtype,
    try_preserve_stub_route_recovery,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement.placement_commit import (
    PlacementCommitRecord,
    PlacementCommitState,
    make_placement_id,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.routing.routing_cells import (
    EXTENSIONS,
    EXTRACTORS_FLUID,
    EXTRACTORS_SHAPE,
    layout_kind,
    transport_kind_for_extractor,
    want_role,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.validation import (
    final_validation as _final_validation,
)


class PreserveDropReason(StrEnum):
    """Fixed taxonomy for preserve-first merged-seed extractor drops (histogram / CI)."""

    NO_ADJACENT_TRANSPORT = "NO_ADJACENT_TRANSPORT"
    NO_MATCHING_STUB = "NO_MATCHING_STUB"
    NO_VALID_ROTATION = "NO_VALID_ROTATION"
    ORPHAN_COMPONENT = "ORPHAN_COMPONENT"
    NON_CARDINAL_OUTPUT = "NON_CARDINAL_OUTPUT"
    MIXED_KIND_CONFLICT = "MIXED_KIND_CONFLICT"
    INVALID_EXISTING_ROW = "INVALID_EXISTING_ROW"


class RecoverabilityClass(StrEnum):
    """Salvageability tier above ``PreserveDropReason`` (trace / dashboards; static rules)."""

    TRIVIAL = "TRIVIAL"
    LOCAL_ROTATION = "LOCAL_ROTATION"
    NEAR_TRANSPORT = "NEAR_TRANSPORT"
    NEEDS_REROUTE = "NEEDS_REROUTE"
    UNRECOVERABLE = "UNRECOVERABLE"


@dataclass(frozen=True)
class _DeferredNearTransportStubRecovery:
    """Queued NO_MATCHING_STUB miner (NEAR_TRANSPORT band) for post-scan stub-route retries."""

    miner: Coord
    extensions: frozenset[Coord]
    transport_kind: str
    row_m: dict[str, Any]
    nhops_seed: int
    ncell_seed: Coord | None
    neighbor_stub_coords: tuple[Coord, ...]
    eff_r_after_inline: int | None
    stub_route_trace_last: dict[str, Any] | None


def _append_bounded_stub_sample(
    samples: list[dict[str, Any]],
    *,
    miner: Coord,
    rr_res: StubRouteRecoveryResult,
    cap: int = 5,
) -> None:
    if len(samples) >= cap:
        return
    psr = rr_res.trace.get("preserve_stub_recovery")
    samples.append(
        {
            "miner_cell": [int(miner[0]), int(miner[1])],
            "stub_cell": psr.get("selected_stub_cell") if isinstance(psr, dict) else None,
            "chosen_r": psr.get("selected_r") if isinstance(psr, dict) else None,
            "route_len_edges": psr.get("route_len_edges") if isinstance(psr, dict) else None,
            "new_transport_cell_count": (
                psr.get("new_transport_cell_count") if isinstance(psr, dict) else None
            ),
        }
    )


def _append_bounded_unrecovered_stub_sample(
    samples: list[dict[str, Any]],
    detail_row: Mapping[str, Any],
    *,
    cap: int = 5,
) -> None:
    if len(samples) >= cap:
        return
    samples.append(
        {
            "miner_cell": detail_row.get("miner_cell"),
            "preserve_drop_reason": detail_row.get("preserve_drop_reason"),
            "recoverability_class": detail_row.get("recoverability_class"),
            "nearest_same_kind_transport_hops": detail_row.get("nearest_same_kind_transport_hops"),
        }
    )


def _bounded_recovery_summary_from_details(details: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate tier telemetry from ``preserve_stub_recovery`` rows (NDJSON only)."""

    def _bump(m: dict[str, int], key: str) -> None:
        if not key:
            return
        m[key] = m.get(key, 0) + 1

    out: dict[str, Any] = {
        "tier_a_attempted_count": 0,
        "tier_a_success_count": 0,
        "tier_b_attempted_count": 0,
        "tier_b_success_count": 0,
        "tier_c_attempted_count": 0,
        "tier_c_success_count": 0,
        "tier_d_attempted_count": 0,
        "tier_d_success_count": 0,
        "tier_b_skip_reason_counts": {},
        "tier_c_skip_reason_counts": {},
        "tier_d_skip_reason_counts": {},
        "tier_b_failure_reason_counts": {},
        "tier_c_failure_reason_counts": {},
        "tier_d_failure_reason_counts": {},
        "final_rejected_reason_counts": {},
        "final_rejected_reason_subtype_counts": {},
    }
    for d in details:
        psr = d.get("preserve_stub_recovery")
        if not isinstance(psr, dict):
            continue
        if psr.get("tier_a_attempted") is True:
            out["tier_a_attempted_count"] += 1
        if psr.get("tier_a_success") is True:
            out["tier_a_success_count"] += 1
        if psr.get("tier_b_attempted") is True:
            out["tier_b_attempted_count"] += 1
        if psr.get("tier_b_success") is True:
            out["tier_b_success_count"] += 1
        if psr.get("tier_c_attempted") is True:
            out["tier_c_attempted_count"] += 1
        if psr.get("tier_c_success") is True:
            out["tier_c_success_count"] += 1
        if psr.get("tier_d_attempted") is True:
            out["tier_d_attempted_count"] += 1
        if psr.get("tier_d_success") is True:
            out["tier_d_success_count"] += 1
        sb = psr.get("tier_b_skip_reason")
        if isinstance(sb, str) and sb:
            _bump(out["tier_b_skip_reason_counts"], sb)
        sc = psr.get("tier_c_skip_reason")
        if isinstance(sc, str) and sc:
            _bump(out["tier_c_skip_reason_counts"], sc)
        fb = psr.get("tier_b_failure_reason")
        if isinstance(fb, str) and fb:
            _bump(out["tier_b_failure_reason_counts"], fb)
        fc = psr.get("tier_c_failure_reason")
        if isinstance(fc, str) and fc:
            _bump(out["tier_c_failure_reason_counts"], fc)
        sd = psr.get("tier_d_skip_reason")
        if isinstance(sd, str) and sd:
            _bump(out["tier_d_skip_reason_counts"], sd)
        fd = psr.get("tier_d_failure_reason")
        if isinstance(fd, str) and fd:
            _bump(out["tier_d_failure_reason_counts"], fd)
        rr = psr.get("rejected_reason")
        if isinstance(rr, str) and rr:
            _bump(out["final_rejected_reason_counts"], rr)
        rs = psr.get("rejected_reason_subtype")
        if isinstance(rs, str) and rs:
            _bump(out["final_rejected_reason_subtype_counts"], rs)
    for key in (
        "tier_b_skip_reason_counts",
        "tier_c_skip_reason_counts",
        "tier_d_skip_reason_counts",
        "tier_b_failure_reason_counts",
        "tier_c_failure_reason_counts",
        "tier_d_failure_reason_counts",
        "final_rejected_reason_counts",
        "final_rejected_reason_subtype_counts",
    ):
        out[key] = dict(sorted(out[key].items(), key=lambda kv: kv[0]))
    return out


def _unrecoverable_contract_reason_code(detail: Mapping[str, Any]) -> str | None:
    """Stable bucket for expected-loss summary (``None`` = not design-unrecoverable)."""

    pdr = str(detail.get("preserve_drop_reason") or detail.get("reason") or "")
    if pdr in (
        PreserveDropReason.ORPHAN_COMPONENT.value,
        PreserveDropReason.INVALID_EXISTING_ROW.value,
    ):
        return "orphan_or_invalid_no_preserve_trunk"
    psr = detail.get("preserve_stub_recovery")
    if not isinstance(psr, dict):
        return None
    rr = psr.get("rejected_reason")
    if rr == "nearest_hops_none":
        return "orphan_or_invalid_no_preserve_trunk"
    if rr == "nearest_hops_over_cap":
        return "no_legal_same_kind_route_under_bounds"
    if rr in ("route_len_over_cap", "new_transport_cells_over_cap", "visit_cap"):
        return "no_legal_same_kind_route_under_bounds"
    td_skip = psr.get("tier_d_skip_reason")
    if td_skip == "tier_d_skipped_diagonal_only_extension_topology":
        return "diagonal_only_extension_topology"
    if td_skip == "tier_d_skipped_empty_bundle":
        return "would_require_unrelated_bundle_demolition"
    if td_skip == "tier_d_skipped_no_repack_candidates":
        return "sealed_by_unrelated_body"
    tdf = psr.get("tier_d_failure_reason")
    if isinstance(tdf, str) and tdf:
        if "no_same_kind_route" in tdf:
            return "no_legal_same_kind_route_under_bounds"
        if (
            "route_len_over_cap" in tdf
            or "new_transport_cells_over_cap" in tdf
            or "visit_cap" in tdf
        ):
            return "no_legal_same_kind_route_under_bounds"
        if "unrelated_extractor" in tdf or "foreign_extension" in tdf:
            return "would_require_unrelated_bundle_demolition"
        if "protected_corridor" in tdf:
            return "would_require_transport_or_protected_corridor_removal"
    if psr.get("tier_d_attempted") is True and psr.get("tier_d_success") is not True:
        if isinstance(tdf, str) and tdf.startswith("tier_d_failed_"):
            return "no_legal_same_kind_route_under_bounds"
    return None


def classify_pass12_remaining_preserve_drop_row(detail: Mapping[str, Any]) -> str:
    """Post-hoc triage label for NDJSON rows (debug reports; not solver input)."""

    psr = detail.get("preserve_stub_recovery")
    if not isinstance(psr, dict):
        return "needs_more_telemetry"
    if psr.get("tier_d_success") is True:
        return "recoverable_with_small_fix"
    code = _unrecoverable_contract_reason_code(detail)
    if code is not None:
        return "unrecoverable_by_design"
    if psr.get("attempted") is False and psr.get("rejected_reason") not in (
        None,
        "nearest_hops_none",
        "nearest_hops_over_cap",
    ):
        return "needs_more_telemetry"
    if psr.get("tier_d_attempted") is True and psr.get("tier_d_success") is not True:
        if psr.get("tier_d_skip_reason") is None and psr.get("tier_d_failure_reason") is None:
            return "needs_more_telemetry"
        return "unrecoverable_by_design"
    return "needs_more_telemetry"


def report_pass12_preserved_missing_stub_drop_details(
    details: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Extract NDJSON-oriented fields for each remaining preserve drop (output / tooling only)."""

    rows: list[dict[str, Any]] = []
    for d in details:
        psr = d.get("preserve_stub_recovery")
        if not isinstance(psr, dict):
            psr = {}
        probe = psr.get("stub_route_probe_last")
        blocked_fc: Any = None
        if isinstance(probe, dict):
            blocked_fc = probe.get("blocked_frontier_reason_counts")
        rows.append(
            {
                "miner_cell": d.get("miner_cell"),
                "transport_kind": d.get("transport_kind"),
                "nearest_same_kind_transport_hops": d.get("nearest_same_kind_transport_hops"),
                "nearest_same_kind_transport_cell": d.get("nearest_same_kind_transport_cell"),
                "recoverability_class": d.get("recoverability_class"),
                "preserve_drop_reason": d.get("preserve_drop_reason") or d.get("reason"),
                "rejected_reason_subtype": psr.get("rejected_reason_subtype"),
                "adjacent_cardinal_cells": d.get("adjacent_cardinal_cells"),
                "rotation_probe_summary": d.get("rotation_probe_summary"),
                "preserve_stub_recovery.rejected_reason": psr.get("rejected_reason"),
                "preserve_stub_recovery.rejected_reason_subtype": psr.get(
                    "rejected_reason_subtype"
                ),
                "tier_d_attempted": psr.get("tier_d_attempted"),
                "tier_d_success": psr.get("tier_d_success"),
                "tier_d_skip_reason": psr.get("tier_d_skip_reason"),
                "tier_d_failure_reason": psr.get("tier_d_failure_reason"),
                "output_repack_candidate_count": psr.get("output_repack_candidate_count"),
                "output_repack_candidate_sample": psr.get("output_repack_candidate_sample"),
                "output_repack_selected_rotation": psr.get("output_repack_selected_rotation"),
                "blocked_frontier_reason_counts": blocked_fc,
                "pass12_remaining_drop_classification": classify_pass12_remaining_preserve_drop_row(
                    d
                ),
                "pass12_unrecoverable_contract_reason_code": _unrecoverable_contract_reason_code(d),
            }
        )
    return rows


def _preserve_missing_stub_summary_from_details(
    details: list[dict[str, Any]],
) -> dict[str, Any]:
    """Roll up ``pass12_preserved_missing_stub_drop_details`` for NDJSON / finalize trace."""

    by_reason: dict[str, int] = {}
    by_rec: dict[str, int] = {}
    by_sub: dict[str, int] = {}
    repack_eligible = 0
    unrecoverable_drop_count = 0
    unrecoverable_reason_counts: dict[str, int] = {}
    for d in details:
        pr = str(d.get("preserve_drop_reason") or d.get("reason") or "unknown")
        by_reason[pr] = by_reason.get(pr, 0) + 1
        rc = str(d.get("recoverability_class") or "unknown")
        by_rec[rc] = by_rec.get(rc, 0) + 1
        sub = ""
        psr = d.get("preserve_stub_recovery")
        if isinstance(psr, dict):
            sub = str(psr.get("rejected_reason_subtype") or "")
            if sub == "occupied_neighbor_ring":
                repack_eligible += 1
        if not sub:
            sub = "(none)"
        by_sub[sub] = by_sub.get(sub, 0) + 1
        ucode = _unrecoverable_contract_reason_code(d)
        if ucode is not None:
            unrecoverable_drop_count += 1
            unrecoverable_reason_counts[ucode] = unrecoverable_reason_counts.get(ucode, 0) + 1
    bounded = _bounded_recovery_summary_from_details(details)
    drop_count = len(details)
    expected_unrecoverable_drop_count = unrecoverable_drop_count
    recoverable_unresolved_drop_count = max(0, drop_count - unrecoverable_drop_count)
    return {
        "drop_count": drop_count,
        "by_reason": dict(sorted(by_reason.items(), key=lambda kv: kv[0])),
        "by_recoverability": dict(sorted(by_rec.items(), key=lambda kv: kv[0])),
        "by_rejected_reason_subtype": dict(sorted(by_sub.items(), key=lambda kv: kv[0])),
        "local_repack_candidate_count": repack_eligible,
        "bounded_recovery": bounded,
        "unrecoverable_drop_count": unrecoverable_drop_count,
        "expected_unrecoverable_drop_count": expected_unrecoverable_drop_count,
        "recoverable_unresolved_drop_count": recoverable_unresolved_drop_count,
        "unrecoverable_reason_counts": dict(
            sorted(unrecoverable_reason_counts.items(), key=lambda kv: kv[0])
        ),
    }


def _normalize_preserve_stub_recovery_drop_contract(detail_row: dict[str, Any]) -> None:
    """NDJSON/solver_summary: ensure probe + subtype stay self-consistent on merge.

    Some pipelines retain shallow references; backfill nested ``stub_route_probe_last`` from
    ``preserve_stub_recovery`` mirrors and re-derive ``rejected_reason_subtype`` when missing.
    """

    psr = detail_row.get("preserve_stub_recovery")
    if not isinstance(psr, dict):
        return
    probe = psr.get("stub_route_probe_last")
    if not isinstance(probe, dict):
        return
    _mirror_keys = (
        "start_cell",
        "stub_start_cell",
        "goal_count",
        "goal_sample",
        "edge_cap",
        "max_new_transport_cells",
    )
    for key in _mirror_keys:
        if probe.get(key) is None and psr.get(key) is not None:
            probe[key] = psr[key]
    if probe.get("goal_count") is None:
        gtc = psr.get("goal_transport_cell_count")
        if isinstance(gtc, int):
            probe["goal_count"] = gtc
    start_cell = probe.get("start_cell")
    if start_cell is not None:
        probe["start"] = start_cell
    else:
        ss = probe.get("stub_start_cell")
        if ss is not None:
            probe["start"] = ss
    if str(psr.get("rejected_reason") or "") == "no_same_kind_route":
        sub = psr.get("rejected_reason_subtype")
        if sub is None or sub == "":
            psr["rejected_reason_subtype"] = _no_same_kind_route_subtype(
                blocked=probe.get("blocked_frontier_reason_counts"),
                reachable_relaxed=int(
                    probe.get("reachable_same_kind_goals_under_edge_cap_512") or 0
                ),
            )
        for key in _mirror_keys:
            if psr.get(key) is None and probe.get(key) is not None:
                psr[key] = probe[key]


def _missing_stub_drop_detail_row(
    *,
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
    tk: str,
    row_m: dict[str, Any],
    merged_seed_miner_count: int,
    nhops: int | None,
    ncell: Coord | None,
    neighbor_stub_coords: tuple[Coord, ...],
    eff_r: int | None,
    stub_route_trace_for_drop: dict[str, Any] | None,
) -> dict[str, Any]:
    wr_exp = want_role(tk)
    cardinals = _cardinal_neighbor_cell_summaries(miner, cells)
    transport_adj = [e for e in cardinals if e.get("role") in ("belt", "pipe")]
    pdr = _classify_preserve_drop_reason(
        want_wr=wr_exp,
        cardinals=cardinals,
        nearest_hops=nhops,
    )
    raw_rr = row_m.get("r")
    existing_row_r = int(raw_rr) % 4 if isinstance(raw_rr, int) else None
    rot_summary = (
        _rotation_probe_summary(miner, cells, tk, row_m.get("r")) if tk is not None else []
    )
    detail_row: dict[str, Any] = {
        "miner_cell": [int(miner[0]), int(miner[1])],
        "reason": pdr.value,
        "preserve_drop_reason": pdr.value,
        "transport_kind": tk,
        "expected_stub_role": wr_exp,
        "pass12_merged_seed_miner_count": merged_seed_miner_count,
        "nearest_same_kind_transport_hops": nhops,
        "nearest_same_kind_transport_cell": (
            None if ncell is None else [int(ncell[0]), int(ncell[1])]
        ),
        "rotation_probe_summary": rot_summary,
        "matching_adjacent_stub_coords": [[int(c[0]), int(c[1])] for c in neighbor_stub_coords],
        "adjacent_transport_cells": transport_adj,
        "adjacent_cardinal_cells": cardinals,
        "existing_row_r": existing_row_r,
        "recovered_r": eff_r,
    }
    _rc = recoverability_class_for_preserve_drop_detail(detail_row)
    detail_row["recoverability_class"] = _rc.value
    if stub_route_trace_for_drop is not None:
        detail_row.update(copy.deepcopy(stub_route_trace_for_drop))
    else:
        detail_row["preserve_stub_recovery"] = copy.deepcopy(_empty_psr(nhops))
    _normalize_preserve_stub_recovery_drop_contract(detail_row)
    _ensure_extension_carve_schema_on_preserve_stub_recovery(detail_row)
    return detail_row


def _ensure_extension_carve_schema_on_preserve_stub_recovery(detail_row: dict[str, Any]) -> None:
    """NDJSON: ``preserve_stub_recovery`` always exposes extension carve keys (telemetry only)."""

    psr = detail_row.get("preserve_stub_recovery")
    if not isinstance(psr, dict):
        detail_row["preserve_stub_recovery"] = {}
        psr = detail_row["preserve_stub_recovery"]
    psr.setdefault("extension_carve_considered", False)
    psr.setdefault("extension_carve_candidate_cells", [])
    psr.setdefault("extension_carve_skip_reason", None)
    psr.setdefault("extension_carve_attempted", False)
    psr.setdefault("extension_carve_applied", None)
    psr.setdefault("post_carve_rejected_reason", None)
    psr.setdefault("carved_extension_cell", None)
    psr.setdefault("recovery_tier_attempted", [])
    psr.setdefault("output_reorientation_attempted", False)
    psr.setdefault("output_reorientation_success", False)
    psr.setdefault("bounded_bundle_rollback_attempted", False)
    psr.setdefault("bounded_bundle_rollback_cells", [])
    psr.setdefault("bounded_bundle_rollback_success", False)
    psr.setdefault("tier_a_attempted", False)
    psr.setdefault("tier_a_success", False)
    psr.setdefault("tier_a_failure_reason", None)
    psr.setdefault("tier_b_attempted", False)
    psr.setdefault("tier_b_success", False)
    psr.setdefault("tier_b_skip_reason", None)
    psr.setdefault("tier_b_failure_reason", None)
    psr.setdefault("tier_c_attempted", False)
    psr.setdefault("tier_c_success", False)
    psr.setdefault("tier_c_skip_reason", None)
    psr.setdefault("tier_c_failure_reason", None)
    psr.setdefault("tier_c_direct_stub_blocker_cells", [])
    psr.setdefault("tier_c_same_bundle_cardinal_neighbor_cells", [])
    psr.setdefault("tier_c_candidate_pair_count", 0)
    psr.setdefault("tier_c_candidate_pair_sample", [])
    psr.setdefault("tier_c_pair_generation_mode", None)
    psr.setdefault("tier_c_no_pair_diagnostic", None)
    psr.setdefault("tier_d_attempted", False)
    psr.setdefault("tier_d_success", False)
    psr.setdefault("tier_d_skip_reason", None)
    psr.setdefault("tier_d_failure_reason", None)
    psr.setdefault("output_repack_candidate_count", 0)
    psr.setdefault("output_repack_candidate_sample", [])
    psr.setdefault("output_repack_selected_rotation", None)
    psr.setdefault("output_repack_removed_extension_cells", [])
    psr.setdefault("output_repack_replaced_extension_cells", [])
    psr.setdefault("output_repack_preserved_extension_count", None)
    psr.setdefault("output_repack_route_len_edges", None)


def _preserve_stub_route_drop_observability(
    *,
    stub_route_recovery_enabled: bool,
    nhops_seed: int | None,
    pdr_pre: PreserveDropReason,
    stub_route_trace_for_drop: dict[str, Any] | None,
    drop_phase: Literal["immediate_inline", "deferred_queue_exhausted"],
) -> dict[str, Any]:
    """NDJSON/solver_summary: stub-route vs deferred-queue decision (no routing policy reads)."""

    maxh = MAX_PASS12_STUB_ROUTE_RECOVERY_NEAREST_HOPS
    deferred_eligible = bool(
        stub_route_recovery_enabled
        and pdr_pre == PreserveDropReason.NO_MATCHING_STUB
        and nhops_seed is not None
        and 1 <= nhops_seed <= maxh
    )
    out: dict[str, Any] = {
        "preserve_stub_route_recovery_enabled": stub_route_recovery_enabled,
        "preserve_stub_route_deferred_queue_min_hops_inclusive": 1,
        "preserve_stub_route_deferred_queue_max_hops_inclusive": maxh,
        "preserve_stub_route_deferred_queue_eligible": deferred_eligible,
        "preserve_stub_route_drop_phase": drop_phase,
        "preserve_stub_route_drop_after_deferred_queue": drop_phase == "deferred_queue_exhausted",
        "preserve_stub_route_hops_equal_one": nhops_seed == 1,
    }
    if not stub_route_recovery_enabled:
        out["preserve_stub_route_inline_attempted"] = False
        out["preserve_stub_route_inline_skip_reason"] = "recovery_disabled"
    elif nhops_seed is None:
        out["preserve_stub_route_inline_attempted"] = False
        out["preserve_stub_route_inline_skip_reason"] = "nearest_hops_none"
    elif nhops_seed > maxh:
        out["preserve_stub_route_inline_attempted"] = False
        out["preserve_stub_route_inline_skip_reason"] = "nearest_hops_over_cap"
    else:
        out["preserve_stub_route_inline_attempted"] = True
        psr = (stub_route_trace_for_drop or {}).get("preserve_stub_recovery")
        if isinstance(psr, dict):
            out["preserve_stub_route_inline_accepted"] = psr.get("accepted")
            out["preserve_stub_route_inline_rejected_reason"] = psr.get("rejected_reason")
        else:
            out["preserve_stub_route_inline_accepted"] = None
            out["preserve_stub_route_inline_rejected_reason"] = None
    return out


def _detail_adjacent_same_kind_transport(detail: Mapping[str, Any], want_wr: str) -> bool:
    """True when a cardinal neighbour row already matches ``want_wr`` (belt/pipe role)."""

    for key in ("adjacent_transport_cells", "adjacent_cardinal_cells"):
        cells = detail.get(key)
        if not isinstance(cells, list):
            continue
        for e in cells:
            if isinstance(e, dict) and e.get("role") == want_wr:
                return True
    rot = detail.get("rotation_probe_summary")
    if isinstance(rot, list):
        for e in rot:
            if isinstance(e, dict) and e.get("matches") is True:
                return True
    return False


def _recoverability_band_from_nearest_hops(
    hops: int, *, max_recovery_bfs_hops: int
) -> RecoverabilityClass:
    """TRIVIAL / NEAR_TRANSPORT / NEEDS_REROUTE from integer BFS hop distance."""

    if hops <= 1:
        return RecoverabilityClass.TRIVIAL
    if hops <= max_recovery_bfs_hops:
        return RecoverabilityClass.NEAR_TRANSPORT
    return RecoverabilityClass.NEEDS_REROUTE


def recoverability_class_for_preserve_drop_detail(
    detail: Mapping[str, Any],
    *,
    max_recovery_bfs_hops: int = MAX_PASS12_RECOVERY_BFS_HOPS,
) -> RecoverabilityClass:
    """Map a single drop detail dict to ``RecoverabilityClass`` (reviewer static table v1)."""

    raw = detail.get("preserve_drop_reason") or detail.get("reason")
    try:
        pdr = PreserveDropReason(str(raw)) if raw is not None else None
    except ValueError:
        pdr = None
    if pdr is None:
        return RecoverabilityClass.NEEDS_REROUTE
    hops_raw = detail.get("nearest_same_kind_transport_hops")
    hops = int(hops_raw) if isinstance(hops_raw, int) else None
    want_wr = str(detail.get("expected_stub_role") or "")

    if pdr in (PreserveDropReason.ORPHAN_COMPONENT, PreserveDropReason.INVALID_EXISTING_ROW):
        return RecoverabilityClass.UNRECOVERABLE
    if pdr == PreserveDropReason.MIXED_KIND_CONFLICT:
        return RecoverabilityClass.NEEDS_REROUTE
    if pdr == PreserveDropReason.NON_CARDINAL_OUTPUT:
        return RecoverabilityClass.LOCAL_ROTATION
    if pdr == PreserveDropReason.NO_VALID_ROTATION:
        if want_wr and _detail_adjacent_same_kind_transport(detail, want_wr):
            return RecoverabilityClass.TRIVIAL
        return RecoverabilityClass.LOCAL_ROTATION
    if pdr == PreserveDropReason.NO_MATCHING_STUB:
        if hops is None:
            return RecoverabilityClass.NEEDS_REROUTE
        return _recoverability_band_from_nearest_hops(
            hops,
            max_recovery_bfs_hops=max_recovery_bfs_hops,
        )
    if pdr == PreserveDropReason.NO_ADJACENT_TRANSPORT:
        if hops is None:
            return RecoverabilityClass.UNRECOVERABLE
        return _recoverability_band_from_nearest_hops(
            hops,
            max_recovery_bfs_hops=max_recovery_bfs_hops,
        )
    return RecoverabilityClass.NEEDS_REROUTE


def _preserve_first_hard_gate(existing_layout_source_kind: str | None) -> bool:
    """True when Pass1 must not clear unrouted merged bundles (fluid existing maps only)."""

    return existing_layout_source_kind == "existing_fluid_layout"


def _strip_provisional_placement_row_keys(row: dict[str, Any]) -> dict[str, Any]:
    """Remove row FSM markers that would fail final geometry validation on preserved copies."""

    out = dict(row)
    for key in ("placement_state", "placement_commit_state"):
        v = out.get(key)
        if isinstance(v, str) and v.lower() in ("quarantined_unrouted", "provisional_placed"):
            out.pop(key, None)
    return out


def _first_rotation_with_matching_stub(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
    transport_kind: str,
    raw_r: Any,
) -> int | None:
    """Prefer declared ``r`` when its stub matches; else first ``r`` in 0..3 with matching stub."""

    wr = want_role(transport_kind)
    order: list[int] = []
    if isinstance(raw_r, int):
        order.append(raw_r % 4)
    for r in range(4):
        if r not in order:
            order.append(r)
    for cand_r in order:
        sc = shape_miner_output_cell(miner, cand_r)
        if sc is None:
            continue
        st = cells.get(sc)
        if st is not None and st.get("role") == wr:
            return cand_r
    return None


def _cardinal_neighbor_cell_summaries(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
) -> list[dict[str, Any]]:
    """All existing cardinal neighbors with role/layout_kind (debug / drop trace)."""

    x, y = miner
    out: list[dict[str, Any]] = []
    for nxt in neighbors4(x, y):
        row = cells.get(nxt)
        if row is None:
            continue
        rv = row.get("role")
        role_s = str(rv) if isinstance(rv, str) else None
        out.append(
            {
                "cell": [int(nxt[0]), int(nxt[1])],
                "role": role_s,
                "layout_kind": layout_kind(row),
            }
        )
    out.sort(key=lambda e: (e["cell"][1], e["cell"][0]))
    return out


def _neighbor_stub_coords_for_kind(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
    transport_kind: str,
) -> tuple[Coord, ...]:
    """Cardinal neighbours whose mining-map role matches this extractor transport kind."""

    wr = want_role(transport_kind)
    x, y = miner
    found: list[Coord] = []
    for nxt in neighbors4(x, y):
        row = cells.get(nxt)
        if row is not None and row.get("role") == wr:
            found.append(nxt)
    return tuple(sorted(found, key=lambda p: (p[1], p[0])))


def _rotation_from_sorted_neighbor_stub(
    miner: Coord,
    neighbor_stubs: tuple[Coord, ...],
) -> int | None:
    """Pick deterministic stub among cardinally adjacent belt/pipe cells and yield ``r``."""

    for stub in neighbor_stubs:
        dx, dy = stub[0] - miner[0], stub[1] - miner[1]
        if dx != 0 and dy != 0:
            continue
        try:
            return rotation_r_for_output_direction(dx, dy)
        except ValueError:
            continue
    return None


def _nearest_same_role_transport_bfs(
    start: Coord,
    *,
    want_wr: str,
    cells: Mapping[Coord, dict[str, Any]],
    max_hops: int,
) -> tuple[int | None, Coord | None]:
    """Cardinal BFS on ``cells`` keys until a row with ``role == want_wr`` (transport trace)."""

    if start not in cells:
        return None, None
    q: deque[Coord] = deque([start])
    dist: dict[Coord, int] = {start: 0}
    visits = 0
    while q:
        c = q.popleft()
        visits += 1
        if visits > 50_000:
            return None, None
        d0 = dist[c]
        row = cells.get(c)
        if row is not None and row.get("role") == want_wr:
            return d0, c
        if d0 >= max_hops:
            continue
        x, y = c
        for v in neighbors4(x, y):
            if v not in cells or v in dist:
                continue
            dist[v] = d0 + 1
            q.append(v)
    return None, None


def _rotation_probe_summary(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
    transport_kind: str,
    raw_r: Any,
) -> list[dict[str, Any]]:
    """Per-rotation stub trace; probe order matches ``_first_rotation_with_matching_stub``."""

    wr = want_role(transport_kind)
    order: list[int] = []
    if isinstance(raw_r, int):
        order.append(raw_r % 4)
    for r in range(4):
        if r not in order:
            order.append(r)
    out: list[dict[str, Any]] = []
    for cand_r in order:
        sc = shape_miner_output_cell(miner, cand_r)
        if sc is None:
            out.append({"r": cand_r, "stub_cell": None, "stub_role": None, "matches": False})
            continue
        st = cells.get(sc)
        role = st.get("role") if st is not None else None
        role_s = str(role) if isinstance(role, str) else None
        out.append(
            {
                "r": cand_r,
                "stub_cell": [int(sc[0]), int(sc[1])],
                "stub_role": role_s,
                "matches": st is not None and role == wr,
            }
        )
    return out


def _relaxed_stub_matches_row(row: dict[str, Any], want_wr: str) -> bool:
    """Recovery-only: infer belt/pipe stub from ``layout_kind`` when ``role`` is wrong."""

    role = row.get("role")
    if role == want_wr:
        return True
    lk = (layout_kind(row) or "").lower()
    building_like = (
        "fluid_miner",
        "fluid_extension",
        "shape_miner",
        "shape_extension",
    )
    if want_wr == "pipe":
        return "pipe" in lk and lk not in building_like
    if want_wr == "belt":
        return "belt" in lk and lk not in building_like
    return False


def _first_rotation_with_relaxed_stub_match(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
    transport_kind: str,
    raw_r: Any,
) -> int | None:
    """Like ``_first_rotation_with_matching_stub`` but uses ``_relaxed_stub_matches_row``."""

    wr = want_role(transport_kind)
    order: list[int] = []
    if isinstance(raw_r, int):
        order.append(raw_r % 4)
    for r in range(4):
        if r not in order:
            order.append(r)
    n = 0
    for cand_r in order:
        n += 1
        if n > MAX_PASS12_RECOVERY_PROBES_PER_MINER:
            break
        sc = shape_miner_output_cell(miner, cand_r)
        if sc is None:
            continue
        st = cells.get(sc)
        if st is not None and _relaxed_stub_matches_row(st, wr):
            return cand_r
    return None


def _neighbor_stub_coords_relaxed(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
    transport_kind: str,
    *,
    use_relaxed: bool,
) -> tuple[Coord, ...]:
    wr = want_role(transport_kind)
    found: list[Coord] = []
    x, y = miner
    for nxt in neighbors4(x, y):
        row = cells.get(nxt)
        if row is None:
            continue
        if row.get("role") == wr:
            found.append(nxt)
        elif use_relaxed and _relaxed_stub_matches_row(row, wr):
            found.append(nxt)
    return tuple(sorted(found, key=lambda p: (p[1], p[0])))


def _routed_ok_at_rotation(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
    transport_kind: str,
    eff_r: int,
) -> bool:
    wr = want_role(transport_kind)
    stub_cell = shape_miner_output_cell(miner, eff_r)
    if stub_cell is None:
        return False
    st = cells.get(stub_cell)
    if st is None:
        return False
    if st.get("role") == wr:
        return True
    return _relaxed_stub_matches_row(st, wr)


def _attempt_preserve_stub_recovery(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
    transport_kind: str,
    row_m: dict[str, Any],
    neighbor_stub_coords: tuple[Coord, ...],
    eff_r: int | None,
    routed_ok: bool,
) -> tuple[tuple[Coord, ...], int | None, bool, dict[str, Any]] | None:
    """Optional relaxed stub inference; returns new state + provenance, or ``None``."""

    if not getattr(settings, "SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY", False):
        return None
    if routed_ok or neighbor_stub_coords:
        return None
    relaxed_coords = _neighbor_stub_coords_relaxed(miner, cells, transport_kind, use_relaxed=True)
    if relaxed_coords == ():
        return None
    new_eff = _rotation_from_sorted_neighbor_stub(miner, relaxed_coords)
    if new_eff is None:
        new_eff = _first_rotation_with_relaxed_stub_match(
            miner, cells, transport_kind, row_m.get("r")
        )
    if new_eff is None:
        return None
    new_routed = _routed_ok_at_rotation(miner, cells, transport_kind, new_eff)
    if not new_routed:
        return None
    provenance: dict[str, Any] = {
        "applied": True,
        "recovery_mode": ["relaxed_layout_kind_stub_match", "rotation_recovered"],
        "miner_cell": [int(miner[0]), int(miner[1])],
        "original_rotation": (int(row_m["r"]) % 4) if isinstance(row_m.get("r"), int) else None,
        "recovered_rotation": int(new_eff),
        "relaxed_stub_coords": [[int(c[0]), int(c[1])] for c in relaxed_coords],
        "recovery_bfs_hops_budget": MAX_PASS12_RECOVERY_BFS_HOPS,
        "recovery_probe_budget": MAX_PASS12_RECOVERY_PROBES_PER_MINER,
    }
    return relaxed_coords, new_eff, new_routed, provenance


def _classify_preserve_drop_reason(
    *,
    want_wr: str,
    cardinals: list[dict[str, Any]],
    nearest_hops: int | None,
) -> PreserveDropReason:
    roles = [c.get("role") for c in cardinals if isinstance(c.get("role"), str)]
    belt_pipe = [r for r in roles if r in ("belt", "pipe")]
    if belt_pipe and not any(r == want_wr for r in belt_pipe):
        return PreserveDropReason.MIXED_KIND_CONFLICT
    if belt_pipe and any(r == want_wr for r in belt_pipe):
        return PreserveDropReason.NO_VALID_ROTATION
    if nearest_hops is not None and nearest_hops >= 1:
        return PreserveDropReason.NO_MATCHING_STUB
    if nearest_hops is None:
        return PreserveDropReason.ORPHAN_COMPONENT
    return PreserveDropReason.NO_ADJACENT_TRANSPORT


def _miner_missing_stub_drop_probe(
    miner: Coord,
    cells: Mapping[Coord, dict[str, Any]],
    *,
    merged_seed_miner_count: int,
    existing_layout_source_kind: str | None,
) -> tuple[bool, int | None, Coord | None]:
    """Missing-stub drop path + one nearest-transport BFS; else ``(False, None, None)``."""

    if not (_preserve_first_hard_gate(existing_layout_source_kind) and merged_seed_miner_count > 1):
        return False, None, None
    row_m = cells.get(miner)
    if row_m is None or row_m.get("role") != "occupied":
        return False, None, None
    if layout_kind(row_m) not in EXTRACTORS_SHAPE | EXTRACTORS_FLUID:
        return False, None, None
    tk = transport_kind_for_extractor(row_m)
    if tk is None:
        return False, None, None
    eff_r = _first_rotation_with_matching_stub(miner, cells, tk, row_m.get("r"))
    neighbor_stub_coords = _neighbor_stub_coords_for_kind(miner, cells, tk)
    if eff_r is None:
        eff_r = _rotation_from_sorted_neighbor_stub(miner, neighbor_stub_coords)
    stub_cell = shape_miner_output_cell(miner, eff_r) if eff_r is not None else None
    wr = want_role(tk)
    st = cells.get(stub_cell) if stub_cell is not None else None
    routed_ok = st is not None and st.get("role") == wr
    would_drop = not routed_ok and len(neighbor_stub_coords) == 0
    if not would_drop:
        return False, None, None
    nhops, ncell = _nearest_same_role_transport_bfs(
        miner,
        want_wr=wr,
        cells=cells,
        max_hops=MAX_PASS12_NEAREST_TRANSPORT_TRACE_HOPS,
    )
    return True, nhops, ncell


def _mining_building_neighbors(
    c: Coord, cells: Mapping[Coord, dict[str, Any]], mineable: frozenset[Coord]
) -> tuple[Coord, ...]:
    x, y = c
    out: list[Coord] = []
    for n in neighbors4(x, y):
        if n not in mineable or n not in cells:
            continue
        row = cells[n]
        if row.get("role") != "occupied":
            continue
        lk = layout_kind(row)
        if lk in EXTRACTORS_SHAPE | EXTRACTORS_FLUID | EXTENSIONS:
            out.append(n)
    return tuple(sorted(out, key=lambda p: (p[1], p[0])))


_ClaimKey = tuple[int, int, int, int]  # (dist, miner_scan_index, root_miner_y, root_miner_x)


def _merged_seed_extension_claims(
    miners: Sequence[Coord],
    cells: Mapping[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
) -> dict[Coord, _ClaimKey]:
    """Multi-source shortest-path claims on extension cells (no crossing other extractors).

    Each extension cell gets the lexicographically minimum tuple
    ``(dist, miner_scan_index, root_y, root_x)`` among paths from any root miner.
    """

    best: dict[Coord, _ClaimKey] = {}
    heap: list[tuple[int, int, int, int, Coord]] = []
    for miner_idx, root in enumerate(miners):
        my, mx = root[1], root[0]
        for n in _mining_building_neighbors(root, cells, mineable):
            if layout_kind(cells[n]) not in EXTENSIONS:
                continue
            heapq.heappush(heap, (1, miner_idx, my, mx, n))
    while heap:
        dist, miner_idx, my, mx, cur = heapq.heappop(heap)
        tkey = (dist, miner_idx, my, mx)
        prev = best.get(cur)
        if prev is not None and prev <= tkey:
            continue
        best[cur] = tkey
        root = miners[miner_idx]
        for nb in _mining_building_neighbors(cur, cells, mineable):
            lk = layout_kind(cells[nb])
            if lk in EXTRACTORS_SHAPE | EXTRACTORS_FLUID:
                if nb != root:
                    continue
                continue
            if lk not in EXTENSIONS:
                continue
            nd = dist + 1
            nkey: _ClaimKey = (nd, miner_idx, my, mx)
            if nb not in best or nkey < best[nb]:
                heapq.heappush(heap, (nd, miner_idx, my, mx, nb))
    return best


def _merged_seed_extension_sets_by_miner(
    miners: Sequence[Coord],
    cells: Mapping[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
) -> dict[Coord, frozenset[Coord]]:
    """Per-root extension sets: multi-owner BFS, then cap at ``PASS12_MAX_EXTENSION_TILES``."""

    if not miners:
        return {}
    claims = _merged_seed_extension_claims(miners, cells, mineable)
    raw_by_miner: dict[Coord, list[Coord]] = {m: [] for m in miners}
    for ext_cell, tkey in claims.items():
        _, miner_idx, _, _ = tkey
        raw_by_miner[miners[miner_idx]].append(ext_cell)
    out: dict[Coord, frozenset[Coord]] = {}
    cap = PASS12_MAX_EXTENSION_TILES
    for m in miners:
        owned = raw_by_miner.get(m, [])
        if len(owned) <= cap:
            out[m] = frozenset(owned)
            continue
        owned.sort(key=lambda p: (claims[p][0], p[1], p[0]))
        out[m] = frozenset(owned[:cap])
    return out


def _extension_facing_parent(ext: Coord, parent_by_cell: dict[Coord, Coord]) -> tuple[int, int]:
    p = parent_by_cell[ext]
    if p == ext:
        return (1, 0)
    return require_cardinal_unit_toward(ext, p)


def _parent_tree_for_miner_and_extensions(
    miner: Coord,
    exts: frozenset[Coord],
    cells: Mapping[Coord, dict[str, Any]],
    mineable: frozenset[Coord],
) -> dict[Coord, Coord]:
    """BFS parent links from ``miner`` through ``exts`` only."""

    parent_by_cell: dict[Coord, Coord] = {miner: miner}
    q: deque[Coord] = deque([miner])
    seen = {miner}
    while q:
        cur = q.popleft()
        for n in _mining_building_neighbors(cur, cells, mineable):
            if n not in exts:
                continue
            if n in seen:
                continue
            parent_by_cell[n] = cur
            seen.add(n)
            q.append(n)
    return parent_by_cell


def seed_pass12_scratch_from_merged_existing(
    merged_mining_map: list[dict[str, Any]],
    *,
    mineable: frozenset[Coord],
    scratch: Pass12LayoutScratch,
    existing_layout_source_kind: str | None = None,
) -> dict[str, Any]:
    """Populate scratch with extractors/extensions already on mineable in ``merged_mining_map``.

    Creates ``PlacementCommitRecord`` rows in ``PROVISIONAL_PLACED`` until STEP4 promotes to
    ``ROUTED_CONFIRMED`` (Algorithm §9.6); merged/preserve paths do not pre-confirm routes.

    Returns count stats for solver summary (caller merges into pass12_stats).
    """

    cells = _final_validation.cells_dict_from_mining_map(merged_mining_map)
    miners: list[Coord] = []
    for c, row in cells.items():
        if c not in mineable or row.get("role") != "occupied":
            continue
        lk = layout_kind(row)
        if lk in EXTRACTORS_SHAPE | EXTRACTORS_FLUID:
            miners.append(c)
    miners.sort(key=lambda p: (p[1], p[0]))
    merged_seed_miner_count = len(miners)
    stub_route_recovery_enabled = bool(
        getattr(settings, "SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY", True)
    )
    nearest_same_kind_transport_bfs_cache: dict[Coord, tuple[int | None, Coord | None]] = {}
    if getattr(settings, "SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY", False) or (
        stub_route_recovery_enabled
    ):
        decorated: list[tuple[tuple[int, int, int, int], Coord]] = []
        for m in miners:
            wd, nh, nc = _miner_missing_stub_drop_probe(
                m,
                cells,
                merged_seed_miner_count=merged_seed_miner_count,
                existing_layout_source_kind=existing_layout_source_kind,
            )
            if wd:
                nearest_same_kind_transport_bfs_cache[m] = (nh, nc)
            if not wd:
                sort_k = (0, 0, m[1], m[0])
            elif nh is None:
                sort_k = (1, 10**9, m[1], m[0])
            else:
                sort_k = (1, nh, m[1], m[0])
            decorated.append((sort_k, m))
        decorated.sort(key=lambda t: t[0])
        miners = [pair[1] for pair in decorated]

    extension_sets_by_miner = _merged_seed_extension_sets_by_miner(miners, cells, mineable)
    seeded_groups = 0
    seeded_routed_records = 0
    preserved_bundle_extractor_cells = 0
    preserved_bundle_extension_cells = 0
    preserved_unrouted_extractor_count = 0
    preserved_missing_stub_drop_extractor_count = 0
    preserved_stripped_rotation_fallback_count = 0
    missing_stub_drop_details: list[dict[str, Any]] = []
    preserve_drop_reason_counts: dict[str, int] = {}
    recoverability_class_counts: dict[str, int] = {}
    preserved_recovery_traces: list[dict[str, Any]] = []
    preserved_bundle_extension_count_histogram: dict[int, int] = {}
    preserved_orphan_extension_count = 0
    rr_attempted = 0
    rr_success = 0
    rr_rej_nearest_hops = 0
    rr_rej_no_stub_space = 0
    rr_rej_no_same_kind_route = 0
    rr_rej_visit_cap = 0
    rr_rej_route_len = 0
    rr_rej_new_transport_cells = 0
    rr_rej_extension_carve = 0
    recovery_queue: list[_DeferredNearTransportStubRecovery] = []
    stub_route_recovery_eligible_count = 0
    rotation_recovery_count = 0
    recovered_stub_samples: list[dict[str, Any]] = []
    unrecovered_stub_samples: list[dict[str, Any]] = []
    recovery_transport_coords_added: set[Coord] = set()
    for miner in miners:
        seed_route_id = "preserve_merged_seed"
        exts = extension_sets_by_miner.get(miner, frozenset())
        parent_by_cell = _parent_tree_for_miner_and_extensions(miner, exts, cells, mineable)

        row_m = cells[miner]
        tk = transport_kind_for_extractor(row_m)
        neighbor_stub_coords: tuple[Coord, ...] = ()
        eff_r: int | None = None
        stub_cell: Coord | None = None
        routed_ok = False
        if tk is not None:
            eff_r = _first_rotation_with_matching_stub(miner, cells, tk, row_m.get("r"))
            neighbor_stub_coords = _neighbor_stub_coords_for_kind(miner, cells, tk)
            if eff_r is None:
                eff_r = _rotation_from_sorted_neighbor_stub(miner, neighbor_stub_coords)
            if eff_r is not None:
                stub_cell = shape_miner_output_cell(miner, eff_r)
                wr = want_role(tk)
                st = cells.get(stub_cell) if stub_cell is not None else None
                routed_ok = st is not None and st.get("role") == wr
        else:
            raw_only = row_m.get("r")
            if isinstance(raw_only, int):
                eff_r = raw_only % 4
                stub_cell = shape_miner_output_cell(miner, eff_r)

        ext_tuple = tuple(sorted(exts, key=lambda p: (p[1], p[0])))

        would_drop_unrecoverable = (
            _preserve_first_hard_gate(existing_layout_source_kind)
            and merged_seed_miner_count > 1
            and tk is not None
            and not routed_ok
            and len(neighbor_stub_coords) == 0
        )
        nhops_seed: int | None = None
        ncell_seed: Coord | None = None
        stub_route_trace_for_drop: dict[str, Any] | None = None
        if would_drop_unrecoverable:
            assert tk is not None
            wr_seed = want_role(tk)
            bfs_cached = nearest_same_kind_transport_bfs_cache.get(miner)
            if bfs_cached is not None:
                nhops_seed, ncell_seed = bfs_cached
            else:
                nhops_seed, ncell_seed = _nearest_same_role_transport_bfs(
                    miner,
                    want_wr=wr_seed,
                    cells=cells,
                    max_hops=MAX_PASS12_NEAREST_TRANSPORT_TRACE_HOPS,
                )
            rec = _attempt_preserve_stub_recovery(
                miner, cells, tk, row_m, neighbor_stub_coords, eff_r, routed_ok
            )
            if rec is not None:
                neighbor_stub_coords, eff_r, routed_ok, _prov = rec
                preserved_recovery_traces.append(dict(_prov))
                rotation_recovery_count += 1
                if routed_ok and eff_r is not None and tk is not None:
                    stub_cell = shape_miner_output_cell(miner, eff_r)
            if stub_route_recovery_enabled and not routed_ok:
                if nhops_seed is None or nhops_seed > MAX_PASS12_STUB_ROUTE_RECOVERY_NEAREST_HOPS:
                    rr_rej_nearest_hops += 1
                    stub_route_trace_for_drop = {
                        "preserve_stub_recovery": {
                            "attempted": False,
                            "accepted": False,
                            "rejected_reason": (
                                "nearest_hops_none"
                                if nhops_seed is None
                                else "nearest_hops_over_cap"
                            ),
                            "nearest_same_kind_transport_hops": nhops_seed,
                        }
                    }
                else:
                    rr_attempted += 1
                    rr_res = try_preserve_stub_route_recovery(
                        miner=miner,
                        extensions=frozenset(exts),
                        transport_kind=tk,
                        cells=cells,
                        mineable=mineable,
                        scratch_transport_cells=frozenset(scratch.transport_cells),
                        scratch_blocked_cells=frozenset(scratch.blocked_cells),
                        nearest_same_kind_transport_hops=nhops_seed,
                        row_r_raw=row_m.get("r"),
                        nearest_same_kind_transport_cell=ncell_seed,
                    )
                    stub_route_trace_for_drop = rr_res.trace
                    psr = rr_res.trace.get("preserve_stub_recovery")
                    if rr_res.accepted:
                        rr_success += 1
                        if rr_res.carved_extension_cells:
                            for _cc in rr_res.carved_extension_cells:
                                cells.pop(_cc, None)
                            exts = frozenset(
                                e for e in exts if e not in rr_res.carved_extension_cells
                            )
                        if rr_res.tier_d_extensions_removed:
                            for _cc in rr_res.tier_d_extensions_removed:
                                cells.pop(_cc, None)
                            for coord, row in rr_res.tier_d_extension_placements:
                                cells[coord] = dict(row)
                            exts = rr_res.tier_d_final_extension_cells
                        if rr_res.chosen_r is not None:
                            mr = dict(cells[miner])
                            mr["r"] = rr_res.chosen_r
                            cells[miner] = mr
                        ext_tuple = tuple(sorted(exts, key=lambda p: (p[1], p[0])))
                        parent_by_cell = _parent_tree_for_miner_and_extensions(
                            miner, exts, cells, mineable
                        )
                        scratch.transport_cells |= set(rr_res.new_transport_coords)
                        recovery_transport_coords_added.update(rr_res.new_transport_coords)
                        eff_r = rr_res.chosen_r
                        stub_cell = rr_res.stub_cell
                        routed_ok = True
                        seed_route_id = "preserve_stub_route_recovery"
                        prov_rt = dict(rr_res.trace)
                        prov_rt["recovery_mode"] = ["stub_route_to_trunk"]
                        prov_rt["miner_cell"] = [int(miner[0]), int(miner[1])]
                        preserved_recovery_traces.append(prov_rt)
                        _append_bounded_stub_sample(
                            recovered_stub_samples, miner=miner, rr_res=rr_res
                        )
                    elif isinstance(psr, dict):
                        rj = psr.get("rejected_reason")
                        if rj == "extension_carve_disabled":
                            rr_rej_extension_carve += 1
                        elif rj == "route_len_over_cap":
                            rr_rej_route_len += 1
                        elif rj == "new_transport_cells_over_cap":
                            rr_rej_new_transport_cells += 1
                        elif rj == "visit_cap":
                            rr_rej_visit_cap += 1
                        elif rj == "no_same_kind_route":
                            rr_rej_no_same_kind_route += 1
                        elif rj == "no_stub_space":
                            rr_rej_no_stub_space += 1
                        else:
                            rr_rej_no_stub_space += 1

        if routed_ok and tk is not None and stub_cell is not None and eff_r is not None:
            scratch.blocked_cells |= {miner} | set(exts)
            scratch.extractor_cells.add(miner)
            scratch.extractor_output_dirs[miner] = output_offset_r(eff_r)
            for ext in sorted(exts, key=lambda p: (p[1], p[0])):
                if ext in parent_by_cell and parent_by_cell[ext] != ext:
                    scratch.extension_facings[ext] = _extension_facing_parent(ext, parent_by_cell)
            scratch.next_placement_seq += 1
            pid = make_placement_id("pass1", scratch.next_placement_seq)
            commit_state = PlacementCommitState.PROVISIONAL_PLACED
            scratch.placement_records[pid] = PlacementCommitRecord(
                placement_id=pid,
                placement_pass="pass1",
                extractor_cell=miner,
                extension_cells=ext_tuple,
                stub_cell=stub_cell,
                transport_kind=tk,
                state=commit_state,
                route_id=seed_route_id,
            )
            seeded_routed_records += 1
            preserved_bundle_extractor_cells += 1
            preserved_bundle_extension_cells += len(exts)
            preserved_bundle_extension_count_histogram[len(exts)] = (
                preserved_bundle_extension_count_histogram.get(len(exts), 0) + 1
            )
        elif _preserve_first_hard_gate(existing_layout_source_kind) or len(miners) == 1:
            # Fluid existing maps: block every unrouted bundle (multi-miner half-preserve guard).
            # Any map with a single merged miner: block the bundle when still provisional (STEP4
            # not yet confirmed) so Pass1 cannot erase the lone body
            # (``raw_asteroid_field`` / legacy).
            drop_unrecoverable = (
                _preserve_first_hard_gate(existing_layout_source_kind)
                and merged_seed_miner_count > 1
                and tk is not None
                and not routed_ok
                and len(neighbor_stub_coords) == 0
            )
            if drop_unrecoverable:
                assert tk is not None
                wr_exp = want_role(tk)
                cardinals = _cardinal_neighbor_cell_summaries(miner, cells)
                pdr_pre = _classify_preserve_drop_reason(
                    want_wr=wr_exp,
                    cardinals=cardinals,
                    nearest_hops=nhops_seed,
                )
                if (
                    pdr_pre == PreserveDropReason.NO_MATCHING_STUB
                    and nhops_seed is not None
                    and recoverability_class_for_preserve_drop_detail(
                        {
                            "preserve_drop_reason": pdr_pre.value,
                            "nearest_same_kind_transport_hops": nhops_seed,
                            "expected_stub_role": wr_exp,
                        }
                    )
                    == RecoverabilityClass.NEAR_TRANSPORT
                ):
                    stub_route_recovery_eligible_count += 1
                defer_this = (
                    stub_route_recovery_enabled
                    and pdr_pre == PreserveDropReason.NO_MATCHING_STUB
                    and nhops_seed is not None
                    and 1 <= nhops_seed <= MAX_PASS12_STUB_ROUTE_RECOVERY_NEAREST_HOPS
                )
                if defer_this:
                    assert nhops_seed is not None
                    trace_copy = (
                        copy.deepcopy(stub_route_trace_for_drop)
                        if stub_route_trace_for_drop is not None
                        else None
                    )
                    recovery_queue.append(
                        _DeferredNearTransportStubRecovery(
                            miner=miner,
                            extensions=frozenset(exts),
                            transport_kind=tk,
                            row_m=row_m,
                            nhops_seed=nhops_seed,
                            ncell_seed=ncell_seed,
                            neighbor_stub_coords=neighbor_stub_coords,
                            eff_r_after_inline=eff_r,
                            stub_route_trace_last=trace_copy,
                        )
                    )
                    continue
                preserved_missing_stub_drop_extractor_count += 1
                detail_row = _missing_stub_drop_detail_row(
                    miner=miner,
                    cells=cells,
                    tk=tk,
                    row_m=row_m,
                    merged_seed_miner_count=merged_seed_miner_count,
                    nhops=nhops_seed,
                    ncell=ncell_seed,
                    neighbor_stub_coords=neighbor_stub_coords,
                    eff_r=eff_r,
                    stub_route_trace_for_drop=stub_route_trace_for_drop,
                )
                detail_row.update(
                    _preserve_stub_route_drop_observability(
                        stub_route_recovery_enabled=stub_route_recovery_enabled,
                        nhops_seed=nhops_seed,
                        pdr_pre=pdr_pre,
                        stub_route_trace_for_drop=stub_route_trace_for_drop,
                        drop_phase="immediate_inline",
                    )
                )
                prev_n = preserve_drop_reason_counts.get(detail_row["preserve_drop_reason"], 0)
                preserve_drop_reason_counts[detail_row["preserve_drop_reason"]] = prev_n + 1
                recoverability_class_counts[detail_row["recoverability_class"]] = (
                    recoverability_class_counts.get(detail_row["recoverability_class"], 0) + 1
                )
                missing_stub_drop_details.append(detail_row)
                _append_bounded_unrecovered_stub_sample(unrecovered_stub_samples, detail_row)
                seeded_groups += 1
                continue

            scratch.blocked_cells |= {miner} | set(exts)
            miner_row = _strip_provisional_placement_row_keys(row_m)
            if tk is not None and neighbor_stub_coords and not routed_ok:
                miner_row.pop("r", None)
                preserved_stripped_rotation_fallback_count += 1
            elif eff_r is not None:
                miner_row["r"] = eff_r
            scratch.preserved_mining_row_overrides[miner] = miner_row
            for ext in exts:
                ext_row = _strip_provisional_placement_row_keys(dict(cells[ext]))
                if ext in parent_by_cell and parent_by_cell[ext] != ext:
                    ext_facing = _extension_facing_parent(ext, parent_by_cell)
                    ext_row["r"] = rotation_r_for_extension_facing_parent(ext_facing)
                    scratch.extension_facings[ext] = ext_facing
                scratch.preserved_mining_row_overrides[ext] = ext_row
            preserved_bundle_extractor_cells += 1
            preserved_bundle_extension_cells += len(exts)
            preserved_unrouted_extractor_count += 1
            preserved_bundle_extension_count_histogram[len(exts)] = (
                preserved_bundle_extension_count_histogram.get(len(exts), 0) + 1
            )
        seeded_groups += 1

    rr_stub_queue_rounds = 0
    max_stub_queue_rounds = (
        min(12, max(len(miners), len(recovery_queue) * 3 + 4)) if recovery_queue else 0
    )
    while recovery_queue:
        if rr_stub_queue_rounds >= max_stub_queue_rounds:
            break
        rr_stub_queue_rounds += 1
        recovery_queue.sort(key=lambda d: (d.nhops_seed, d.miner[1], d.miner[0]))
        next_queue: list[_DeferredNearTransportStubRecovery] = []
        progressed_any = False
        for d in recovery_queue:
            rr_attempted += 1
            rr_q = try_preserve_stub_route_recovery(
                miner=d.miner,
                extensions=d.extensions,
                transport_kind=d.transport_kind,
                cells=cells,
                mineable=mineable,
                scratch_transport_cells=frozenset(scratch.transport_cells),
                scratch_blocked_cells=frozenset(scratch.blocked_cells),
                nearest_same_kind_transport_hops=d.nhops_seed,
                row_r_raw=d.row_m.get("r"),
                nearest_same_kind_transport_cell=d.ncell_seed,
            )
            psr = rr_q.trace.get("preserve_stub_recovery")
            if rr_q.accepted:
                rr_success += 1
                progressed_any = True
                if rr_q.carved_extension_cells:
                    for _cc in rr_q.carved_extension_cells:
                        cells.pop(_cc, None)
                    dex_exts = {e for e in d.extensions if e not in rr_q.carved_extension_cells}
                else:
                    dex_exts = set(d.extensions)
                if rr_q.tier_d_extensions_removed:
                    for _cc in rr_q.tier_d_extensions_removed:
                        cells.pop(_cc, None)
                    for coord, row in rr_q.tier_d_extension_placements:
                        cells[coord] = dict(row)
                    dex_exts = set(rr_q.tier_d_final_extension_cells)
                dminer = d.miner
                if rr_q.chosen_r is not None and dminer in cells:
                    mr = dict(cells[dminer])
                    mr["r"] = rr_q.chosen_r
                    cells[dminer] = mr
                scratch.transport_cells |= set(rr_q.new_transport_coords)
                recovery_transport_coords_added.update(rr_q.new_transport_coords)
                ext_tuple_q = tuple(sorted(dex_exts, key=lambda p: (p[1], p[0])))
                eff_rq = rr_q.chosen_r
                stub_cell_q = rr_q.stub_cell
                assert eff_rq is not None and stub_cell_q is not None
                parent_q = _parent_tree_for_miner_and_extensions(
                    dminer, frozenset(dex_exts), cells, mineable
                )
                tk_q = d.transport_kind
                scratch.blocked_cells |= {dminer} | dex_exts
                scratch.extractor_cells.add(dminer)
                scratch.extractor_output_dirs[dminer] = output_offset_r(eff_rq)
                for ext in sorted(dex_exts, key=lambda p: (p[1], p[0])):
                    if ext in parent_q and parent_q[ext] != ext:
                        scratch.extension_facings[ext] = _extension_facing_parent(ext, parent_q)
                scratch.next_placement_seq += 1
                pid_q = make_placement_id("pass1", scratch.next_placement_seq)
                cq_st = PlacementCommitState.PROVISIONAL_PLACED
                scratch.placement_records[pid_q] = PlacementCommitRecord(
                    placement_id=pid_q,
                    placement_pass="pass1",
                    extractor_cell=dminer,
                    extension_cells=ext_tuple_q,
                    stub_cell=stub_cell_q,
                    transport_kind=tk_q,
                    state=cq_st,
                    route_id="preserve_stub_route_recovery",
                )
                seeded_routed_records += 1
                preserved_bundle_extractor_cells += 1
                preserved_bundle_extension_cells += len(dex_exts)
                preserved_bundle_extension_count_histogram[len(dex_exts)] = (
                    preserved_bundle_extension_count_histogram.get(len(dex_exts), 0) + 1
                )
                prov_rt_q = dict(rr_q.trace)
                prov_rt_q["recovery_mode"] = ["stub_route_to_trunk"]
                prov_rt_q["miner_cell"] = [int(dminer[0]), int(dminer[1])]
                preserved_recovery_traces.append(prov_rt_q)
                _append_bounded_stub_sample(recovered_stub_samples, miner=dminer, rr_res=rr_q)
            else:
                if isinstance(psr, dict):
                    rj = psr.get("rejected_reason")
                    if rj == "extension_carve_disabled":
                        rr_rej_extension_carve += 1
                    elif rj == "route_len_over_cap":
                        rr_rej_route_len += 1
                    elif rj == "new_transport_cells_over_cap":
                        rr_rej_new_transport_cells += 1
                    elif rj == "visit_cap":
                        rr_rej_visit_cap += 1
                    elif rj == "no_same_kind_route":
                        rr_rej_no_same_kind_route += 1
                    elif rj == "no_stub_space":
                        rr_rej_no_stub_space += 1
                    else:
                        rr_rej_no_stub_space += 1
                last_trace = copy.deepcopy(rr_q.trace) if rr_q.trace else None
                next_queue.append(replace(d, stub_route_trace_last=last_trace))
        recovery_queue = next_queue
        if not progressed_any:
            break

    for d in recovery_queue:
        preserved_missing_stub_drop_extractor_count += 1
        wr_q = want_role(d.transport_kind)
        cardinals_q = _cardinal_neighbor_cell_summaries(d.miner, cells)
        pdr_q = _classify_preserve_drop_reason(
            want_wr=wr_q,
            cardinals=cardinals_q,
            nearest_hops=d.nhops_seed,
        )
        detail_row = _missing_stub_drop_detail_row(
            miner=d.miner,
            cells=cells,
            tk=d.transport_kind,
            row_m=d.row_m,
            merged_seed_miner_count=merged_seed_miner_count,
            nhops=d.nhops_seed,
            ncell=d.ncell_seed,
            neighbor_stub_coords=d.neighbor_stub_coords,
            eff_r=d.eff_r_after_inline,
            stub_route_trace_for_drop=d.stub_route_trace_last,
        )
        detail_row.update(
            _preserve_stub_route_drop_observability(
                stub_route_recovery_enabled=stub_route_recovery_enabled,
                nhops_seed=d.nhops_seed,
                pdr_pre=pdr_q,
                stub_route_trace_for_drop=d.stub_route_trace_last,
                drop_phase="deferred_queue_exhausted",
            )
        )
        prev_dn = preserve_drop_reason_counts.get(detail_row["preserve_drop_reason"], 0)
        preserve_drop_reason_counts[detail_row["preserve_drop_reason"]] = prev_dn + 1
        recoverability_class_counts[detail_row["recoverability_class"]] = (
            recoverability_class_counts.get(detail_row["recoverability_class"], 0) + 1
        )
        missing_stub_drop_details.append(detail_row)
        _append_bounded_unrecovered_stub_sample(unrecovered_stub_samples, detail_row)
        seeded_groups += 1

    for c, row in cells.items():
        if c not in mineable or row.get("role") != "occupied":
            continue
        if layout_kind(row) not in EXTENSIONS:
            continue
        if c in scratch.blocked_cells:
            continue
        scratch.blocked_cells.add(c)
        nbrs = _mining_building_neighbors(c, cells, mineable)
        parent: Coord | None = None
        for n in nbrs:
            if layout_kind(cells[n]) in EXTRACTORS_SHAPE | EXTRACTORS_FLUID:
                parent = n
                break
        if parent is None:
            for n in nbrs:
                if layout_kind(cells[n]) in EXTENSIONS:
                    parent = n
                    break
        if parent is not None:
            scratch.extension_facings[c] = require_cardinal_unit_toward(c, parent)
        else:
            scratch.extension_facings[c] = (1, 0)
        preserved_orphan_extension_count += 1

    sk = existing_layout_source_kind or "unspecified"
    return {
        "pass12_merged_seed_miner_count": merged_seed_miner_count,
        "pass12_preserved_equipment_groups": seeded_groups,
        "pass12_preserved_routed_placement_records": seeded_routed_records,
        "pass12_preserve_first_source_kind": sk,
        "pass12_preserved_bundle_extractor_cells": preserved_bundle_extractor_cells,
        "pass12_preserved_bundle_extension_cells": preserved_bundle_extension_cells,
        "pass12_preserved_routed_confirmed_count": seeded_routed_records,
        "pass12_preserved_unrouted_extractor_count": preserved_unrouted_extractor_count,
        "pass12_preserved_missing_stub_drop_extractor_count": (
            preserved_missing_stub_drop_extractor_count
        ),
        "pass12_preserved_missing_stub_drop_details": missing_stub_drop_details,
        "preserve_missing_stub_summary": _preserve_missing_stub_summary_from_details(
            missing_stub_drop_details
        ),
        "pass12_preserve_drop_reason_counts": dict(
            sorted(preserve_drop_reason_counts.items(), key=lambda kv: kv[0])
        ),
        "pass12_recoverability_class_counts": dict(
            sorted(recoverability_class_counts.items(), key=lambda kv: kv[0])
        ),
        "pass12_preserved_recovery_traces": preserved_recovery_traces,
        "pass12_preserved_recovery_success_count": len(preserved_recovery_traces),
        "pass12_preserved_stripped_rotation_fallback_count": (
            preserved_stripped_rotation_fallback_count
        ),
        "pass12_preserved_bundle_extension_count_histogram": dict(
            sorted(preserved_bundle_extension_count_histogram.items())
        ),
        "pass12_preserved_extension_per_extractor_avg": (
            round(preserved_bundle_extension_cells / preserved_bundle_extractor_cells, 6)
            if preserved_bundle_extractor_cells > 0
            else 0.0
        ),
        "pass12_preserved_orphan_extension_count": preserved_orphan_extension_count,
        "pass12_preserved_missing_stub_route_recovery_attempted_count": rr_attempted,
        "pass12_preserved_missing_stub_route_recovery_success_count": rr_success,
        "pass12_preserved_missing_stub_route_recovery_rejected_by_nearest_hops_count": (
            rr_rej_nearest_hops
        ),
        "pass12_preserved_missing_stub_route_recovery_rejected_by_no_stub_space_count": (
            rr_rej_no_stub_space
        ),
        "pass12_preserved_missing_stub_route_recovery_rejected_by_no_same_kind_route_count": (
            rr_rej_no_same_kind_route
        ),
        "pass12_preserved_missing_stub_route_recovery_rejected_by_visit_cap_count": (
            rr_rej_visit_cap
        ),
        "pass12_preserved_missing_stub_route_recovery_rejected_by_route_len_count": (
            rr_rej_route_len
        ),
        "pass12_preserved_missing_stub_route_recovery_rejected_by_new_transport_cells_count": (
            rr_rej_new_transport_cells
        ),
        "pass12_preserved_missing_stub_route_recovery_rejected_by_extension_carve_disabled_count": (
            rr_rej_extension_carve
        ),
        "pass12_preserved_rotation_recovery_count": rotation_recovery_count,
        "pass12_preserved_missing_stub_route_recovery_queue_rounds": rr_stub_queue_rounds,
        "pass12_preserved_recovered_stub_samples": recovered_stub_samples,
        "pass12_preserved_unrecovered_stub_drop_samples": unrecovered_stub_samples,
        "pass12_stub_route_recovery_enabled": stub_route_recovery_enabled,
        "pass12_stub_route_recovery_disabled_by_flag": not stub_route_recovery_enabled,
        "pass12_stub_route_recovery_eligible_count": stub_route_recovery_eligible_count,
        "pass12_stub_route_recovery_queue_rounds": rr_stub_queue_rounds,
        "pass12_stub_route_recovery_attempted_count": rr_attempted,
        "pass12_recovery_new_transport_coords": frozenset(recovery_transport_coords_added),
    }
