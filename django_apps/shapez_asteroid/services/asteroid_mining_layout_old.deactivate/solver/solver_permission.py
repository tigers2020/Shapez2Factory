"""Solver 단계 실행 권한 판정 헬퍼."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    MAX_POST_RECLAIM_PASS3_RERUNS,
    P3E3_GUARDED_COMMIT_ENABLED_DEFAULT,
)


def p3e3_guarded_commit_effective_enabled(p3e3_guarded_commit_enabled: bool | None) -> bool:
    """P3-E3 guarded lex commit: ``None``이면 기본값, 아니면 호출부 오버라이드."""

    return (
        P3E3_GUARDED_COMMIT_ENABLED_DEFAULT
        if p3e3_guarded_commit_enabled is None
        else p3e3_guarded_commit_enabled
    )


def pass3_permission_snapshot(
    *,
    pass12_skipped: bool,
    unfinalized_placement_count: int,
    report_step4: Any,
    step4_committed: bool = True,
) -> dict[str, Any]:
    """Pass3 실행 권한과 trace용 판정 근거를 한 곳에서 만든다."""

    geometry_valid = bool(getattr(report_step4, "geometry_valid", False))
    connectivity_valid = bool(getattr(report_step4, "connectivity_valid", False))
    eligible = (
        not pass12_skipped
        and step4_committed
        and unfinalized_placement_count == 0
        and geometry_valid
        and connectivity_valid
    )
    return {
        "eligible": eligible,
        "pass12_skipped": pass12_skipped,
        "step4_committed": step4_committed,
        "unfinalized_placement_count": unfinalized_placement_count,
        "pre_pass3_geometry_valid": geometry_valid,
        "pre_pass3_connectivity_valid": connectivity_valid,
        "skip_reason": _pass3_skip_reason(
            pass12_skipped=pass12_skipped,
            step4_committed=step4_committed,
            unfinalized_placement_count=unfinalized_placement_count,
            geometry_valid=geometry_valid,
            connectivity_valid=connectivity_valid,
        ),
    }


def p4_reclaim_permission_snapshot(
    *,
    eligible_pass3: bool,
    pass3_summary: dict[str, Any],
    pass3_trace: dict[str, Any],
) -> dict[str, Any]:
    """P4 reclaim 진입 권한과 실패 시 placeholder reason을 계산한다."""

    _ = pass3_trace
    if not eligible_pass3:
        return {"eligible": False, "skip_reason": "pass3_not_eligible"}
    if pass3_summary.get("pass3_reverted"):
        return {"eligible": False, "skip_reason": "pass3_reverted"}
    if pass3_summary.get("pass3_skipped"):
        return {
            "eligible": False,
            "skip_reason": str(pass3_summary.get("pass3_skip_reason") or "pass3_skipped"),
        }
    if not pass3_summary.get("pass3_map_accepted"):
        return {"eligible": False, "skip_reason": "pass3_map_not_accepted"}
    return {"eligible": True, "skip_reason": None}


def post_reclaim_pass3_permission(
    *,
    eligible_pass3: bool,
    pass3_summary: dict[str, Any],
    pass3_trace: dict[str, Any],
) -> bool:
    """P4 이후 Pass3 재실행 권한의 공통 전제만 판정한다."""

    _ = pass3_trace
    return (
        eligible_pass3
        and not pass3_summary.get("pass3_reverted")
        and not pass3_summary.get("pass3_skipped")
        and bool(pass3_summary.get("pass3_map_accepted"))
    )


def post_reclaim_pass3_gate(
    pass3_summary: dict[str, Any],
    *,
    post_reclaim_reruns_lifetime_used: int = 0,
) -> tuple[bool, str | None]:
    """Return (run_pass3, skip_reason). Reclaim §12.5 minimal gate on solver path."""

    if post_reclaim_reruns_lifetime_used >= MAX_POST_RECLAIM_PASS3_RERUNS:
        return False, "max_post_reclaim_pass3_reruns_lifetime"
    reruns = int(pass3_summary.get("post_reclaim_pass3_reruns_used") or 0)
    if reruns >= MAX_POST_RECLAIM_PASS3_RERUNS:
        return False, "max_post_reclaim_pass3_reruns_reached"
    commits = int(pass3_summary.get("p4_reclaim_loop_successful_commits") or 0)
    if commits <= 0:
        return False, "reclaim_commits_zero"
    p4_add = int(pass3_summary.get("p4_reclaim_loop_internal_transport_cumulative_added") or 0)
    if p4_add <= 0:
        return False, "reclaim_internal_transport_not_added"
    prov = pass3_summary.get("provisional_net_internal_transport_saved_after_reclaim")
    if prov is None:
        return False, "provisional_net_internal_transport_missing"
    if int(prov) <= 0:
        return False, "provisional_net_internal_transport_nonpositive"
    return True, None


def _pass3_skip_reason(
    *,
    pass12_skipped: bool,
    step4_committed: bool,
    unfinalized_placement_count: int,
    geometry_valid: bool,
    connectivity_valid: bool,
) -> str | None:
    """Pass3 권한 거부 사유를 기존 공개 문자열로 유지한다."""

    if pass12_skipped:
        return "pass12_skipped"
    if not step4_committed:
        return "step4_not_committed"
    if unfinalized_placement_count > 0:
        return "unfinalized_placement"
    if not geometry_valid or not connectivity_valid:
        return "pre_pass3_validation_failed"
    return None
