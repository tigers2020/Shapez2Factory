"""Pass1/Pass2 pipeline stage extraction for ``solver_service``."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.geometry import Coord
from django_apps.shapez_asteroid.services.asteroid_mining_layout.placement import (
    pass1_timeline_integration as p1_timeline_integration,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_timeline import (
    _pre_pass12_reference_counts,
    count_layout_cells,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    debug_log_event,
)


@dataclass(frozen=True)
class Pass12StageResult:
    """Pass1/Pass2 실행 결과와 기존 summary 계약 필드 묶음."""

    map_after_pass1: list[dict[str, Any]]
    map_after_pass2: list[dict[str, Any]]
    pass12_stats: dict[str, Any]
    pass12_skipped: bool
    pass12_mixed_surface_skipped: bool
    pass12_phase: str
    pass12_status_fields: dict[str, Any]
    pre_counts: dict[str, int]
    post_pass2_counts: dict[str, int]
    placement_records: dict[str, Any] | None
    pass12_replay_txn_id: str | None


def run_pass12_stage(
    *,
    working_map: list[dict[str, Any]],
    final_map: list[dict[str, Any]],
    is_external: Callable[[Coord], bool],
    existing_layout_analysis: dict[str, Any] | None,
    replay_events: list[dict[str, Any]],
    map_timeline: list[dict[str, Any]],
    debug_location: str,
) -> Pass12StageResult:
    """Pass1/Pass2 배치 단계를 실행하고 기존 상태 필드를 조립한다."""

    from django_apps.shapez_asteroid.services.asteroid_mining_layout.existing_layout.existing_layout_analysis import (  # noqa: E501
        effective_suppress_pass1_loop,
        effective_suppress_pass2_loop,
    )

    sp1 = effective_suppress_pass1_loop(existing_layout_analysis)
    sp2 = effective_suppress_pass2_loop(existing_layout_analysis)
    is_ext_basis: list[dict[str, Any]] | None = None
    if len(map_timeline) > 1:
        m1 = map_timeline[1]
        if isinstance(m1, dict):
            raw_basis = m1.get("mining_map")
            if isinstance(raw_basis, list):
                is_ext_basis = raw_basis
    map_after_pass1, map_after_pass2, pass12_stats = (
        p1_timeline_integration.integrate_pass12_placement_into_working_map(
            working_map=working_map,
            final_mining_map=final_map,
            is_external=is_external,
            existing_layout_analysis=existing_layout_analysis,
            replay_events=replay_events,
            suppress_pass1_loop=sp1,
            suppress_pass2_loop=sp2,
            is_external_basis_mining_map=is_ext_basis,
        )
    )
    _p12s = {
        k: v
        for k, v in pass12_stats.items()
        if k != "placement_records" and k != "_replay_pass12_transaction_id"
    }
    _dd = _p12s.get("pass12_preserved_missing_stub_drop_details") or []
    _rc = _p12s.get("pass12_preserve_drop_reason_counts") or {}
    _pms = _p12s.get("preserve_missing_stub_summary")
    _pms_out: dict[str, Any] = (
        dict(_pms)
        if isinstance(_pms, dict)
        else {
            "drop_count": 0,
            "by_reason": {},
            "by_recoverability": {},
            "by_rejected_reason_subtype": {},
            "local_repack_candidate_count": 0,
        }
    )
    _hop_hist: dict[str, int] = {}
    if isinstance(_dd, list):
        for _row in _dd:
            if not isinstance(_row, dict):
                continue
            if str(_row.get("preserve_drop_reason") or "") != "NO_MATCHING_STUB":
                continue
            _h = _row.get("nearest_same_kind_transport_hops")
            if isinstance(_h, int):
                _k = str(_h)
                _hop_hist[_k] = _hop_hist.get(_k, 0) + 1
    debug_log_event(
        debug_location,
        "pass12_completed",
        {
            "pass12_stats": _p12s,
            "placement_record_count": len(pass12_stats.get("placement_records", {}) or {}),
            "after_pass1_counts": count_layout_cells(map_after_pass1),
            "after_pass2_counts": count_layout_cells(map_after_pass2),
            "pass12_preserve_drop_trace": {
                "drop_count": int(
                    _p12s.get("pass12_preserved_missing_stub_drop_extractor_count") or 0
                ),
                "reason_counts": dict(_rc) if isinstance(_rc, dict) else {},
                "sample": _dd[:3] if isinstance(_dd, list) else [],
                "recovery_success_count": int(
                    _p12s.get("pass12_preserved_recovery_success_count") or 0
                ),
                "no_matching_stub_nearest_hops_histogram": _hop_hist,
                "stub_route_recovery_attempted": int(
                    _p12s.get("pass12_preserved_missing_stub_route_recovery_attempted_count") or 0
                ),
                "stub_route_recovery_success": int(
                    _p12s.get("pass12_preserved_missing_stub_route_recovery_success_count") or 0
                ),
                "stub_route_recovery_queue_rounds": int(
                    _p12s.get("pass12_preserved_missing_stub_route_recovery_queue_rounds") or 0
                ),
                "preserve_missing_stub_summary": _pms_out,
            },
        },
    )
    pass12_skipped = bool(
        pass12_stats.get("pass12_skipped") or pass12_stats.get("pass12_mixed_surface_skipped")
    )
    pass12_mixed_surface_skipped = bool(pass12_stats.get("pass12_mixed_surface_skipped"))
    pass12_phase = "skipped_mixed_surface_mvp" if pass12_skipped else "post_pass2_mvp"
    pass12_status_fields: dict[str, Any] = {
        "pass12_phase": pass12_phase,
        "pass12_skipped": pass12_skipped,
        "pass12_skip_reason": pass12_stats.get("pass12_skip_reason"),
        "pass12_mixed_surface_skipped": pass12_mixed_surface_skipped,
    }
    pl_raw = pass12_stats.get("placement_records")
    placement_records = pl_raw if isinstance(pl_raw, dict) else None
    raw_pass12_txn_id = pass12_stats.get("_replay_pass12_transaction_id")
    pass12_replay_txn_id = (
        raw_pass12_txn_id if isinstance(raw_pass12_txn_id, str) and raw_pass12_txn_id else None
    )
    return Pass12StageResult(
        map_after_pass1=map_after_pass1,
        map_after_pass2=map_after_pass2,
        pass12_stats=pass12_stats,
        pass12_skipped=pass12_skipped,
        pass12_mixed_surface_skipped=pass12_mixed_surface_skipped,
        pass12_phase=pass12_phase,
        pass12_status_fields=pass12_status_fields,
        pre_counts=_pre_pass12_reference_counts(map_timeline),
        post_pass2_counts=count_layout_cells(map_after_pass2),
        placement_records=placement_records,
        pass12_replay_txn_id=pass12_replay_txn_id,
    )
