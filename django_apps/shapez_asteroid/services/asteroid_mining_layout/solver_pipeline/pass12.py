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
        effective_suppress_pass12_placement_loops,
    )

    suppress_loops = effective_suppress_pass12_placement_loops(existing_layout_analysis)
    map_after_pass1, map_after_pass2, pass12_stats = (
        p1_timeline_integration.integrate_pass12_placement_into_working_map(
            working_map=working_map,
            final_mining_map=final_map,
            is_external=is_external,
            existing_layout_analysis=existing_layout_analysis,
            replay_events=replay_events,
            suppress_pass1_pass2_loops=suppress_loops,
        )
    )
    _p12s = {
        k: v
        for k, v in pass12_stats.items()
        if k != "placement_records" and k != "_replay_pass12_transaction_id"
    }
    _dd = _p12s.get("pass12_preserved_missing_stub_drop_details") or []
    _rc = _p12s.get("pass12_preserve_drop_reason_counts") or {}
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
