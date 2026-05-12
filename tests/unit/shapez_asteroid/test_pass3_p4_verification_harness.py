"""Pass3/P4 trace harness: STEP4 committed → Pass3 eligible → explicit P4 diagnostics.

회귀 목적: ``step4_not_committed`` / ``pass3_not_eligible``로 Pass3·P4가 조용히 건너뛰지
않았는지 solver_summary·타임라인 계약 키로 검증한다 (라우팅/배치 튜닝 없음).
"""

from __future__ import annotations

from typing import Any
from unittest.mock import patch

import pytest

from django_apps.shapez_asteroid.services.asteroid_mining_layout.foundation.constants import (
    P3E3_REJECT_NO_INTERNAL_TRANSPORT_GAIN,
    SOLVER_FRAME_PASS3_TRANSPORT,
    SOLVER_FRAME_STEP4_ROUTING,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_service import (
    build_solver_timeline,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    trace_run_scope,
)
from tests.unit.shapez_asteroid.test_pass1_timeline_integration import (
    _decoded_miners_with_belt_escape,
)


def _patch_validation_recovery_attempts_zero():
    """단일 정방향 레그(검증 재시도 루프 없음) — ``test_pass3_transport``와 동일."""

    return patch(
        "django_apps.shapez_asteroid.services.asteroid_mining_layout.solver_pipeline."
        "recovery_orchestrator.MAX_VALIDATION_RECOVERY_ATTEMPTS",
        0,
    )


def _assert_no_silent_pass3_skip(ss: dict[str, Any]) -> None:
    if ss.get("pass3_skipped") and ss.get("pass3_skip_reason") is None:
        pytest.fail("Pass3 skipped without explicit pass3_skip_reason (silent skip)")


def _assert_pass3_internal_metrics(ss: dict[str, Any]) -> None:
    for k in (
        "before_internal_transport_count",
        "after_internal_transport_count",
        "pass3_internal_transport_saved",
    ):
        v = ss.get(k)
        assert isinstance(v, int) and not isinstance(
            v, bool
        ), f"solver_summary[{k!r}] must be int, got {v!r}"


def _assert_p3e3_internal_delta_gate_normal_mode(ss: dict[str, Any]) -> None:
    """delta>=0이면 게이트 거부 문자열이 있어야 하고 guarded commit은 금지."""

    if not ss.get("p3e3_internal_transport_delta_gate_evaluated"):
        return
    delta = ss.get("p3e3_candidate_internal_transport_delta")
    if not isinstance(delta, int):
        return
    if delta < 0:
        return
    reject = ss.get("p3e3_internal_transport_delta_gate_reject")
    assert (
        reject == P3E3_REJECT_NO_INTERNAL_TRANSPORT_GAIN
    ), f"delta>=0 reject must record {P3E3_REJECT_NO_INTERNAL_TRANSPORT_GAIN!r} (got {reject!r})"
    guarded = ss.get("p3e3_guarded_committed")
    assert guarded is not True, (
        "normal mode must not guarded-commit atomic candidate with non-negative internal delta "
        f"(delta={delta}, guarded={guarded!r})"
    )


def _assert_p4_trace_or_explicit_skip(ss: dict[str, Any]) -> None:
    if not ss.get("p4_reclaim_shadow_enabled"):
        sr = ss.get("p4_reclaim_shadow_skip_reason")
        assert isinstance(sr, str) and sr.strip(), (
            "P4 shadow disabled but p4_reclaim_shadow_skip_reason missing or empty "
            f"(silent skip: {sr!r})"
        )
        return

    cc = ss.get("p4_reclaim_candidate_count")
    assert cc is not None, "p4_reclaim_shadow_enabled but p4_reclaim_candidate_count is None"
    reasons = ss.get("p4_reclaim_zero_candidate_reasons")
    has_candidates = isinstance(cc, int) and cc > 0
    has_zero_reasons = isinstance(reasons, list) and len(reasons) > 0
    assert has_candidates or has_zero_reasons, (
        "P4 enabled: need p4_reclaim_candidate_count>0 or non-empty "
        f"p4_reclaim_zero_candidate_reasons (cc={cc!r}, reasons={reasons!r})"
    )
    if isinstance(cc, int) and cc == 0:
        msg = "p4_reclaim_candidate_count==0 requires p4_reclaim_zero_candidate_reasons"
        assert has_zero_reasons, msg


def _run_harness(decoded: dict[str, Any]) -> dict[str, Any]:
    with trace_run_scope(), _patch_validation_recovery_attempts_zero():
        return build_solver_timeline(decoded)


def test_pass3_p4_verification_harness_belt_escape_fixture() -> None:
    """공용 ``_decoded_miners_with_belt_escape`` — STEP4 커밋 후 Pass3·P4 계약 키 검증."""

    out = _run_harness(_decoded_miners_with_belt_escape())
    ss: dict[str, Any] = out["solver_summary"]

    assert ss.get("step4_committed") is True, (
        "fixture must keep STEP4 complete commit; "
        "if this fails, replace or extend the decoded fixture for this harness"
    )

    step4_fr = next(f for f in out["solver_timeline"] if f["id"] == SOLVER_FRAME_STEP4_ROUTING)
    assert step4_fr["summary"].get("step4_committed") is True

    assert ss.get("pass3_skip_reason") != "step4_not_committed"
    assert ss.get("pass3_skip_reason") != "pass3_not_eligible"
    _assert_no_silent_pass3_skip(ss)

    assert ss.get("pass3_skipped") is False, (
        f"expected Pass3 to run when STEP4 committed (pass3_skipped={ss.get('pass3_skipped')!r}, "
        f"reason={ss.get('pass3_skip_reason')!r})"
    )

    _assert_pass3_internal_metrics(ss)
    _assert_p3e3_internal_delta_gate_normal_mode(ss)

    p3_fr = next(f for f in out["solver_timeline"] if f["id"] == SOLVER_FRAME_PASS3_TRANSPORT)
    p3s: dict[str, Any] = p3_fr["summary"]
    _assert_pass3_internal_metrics(p3s)
    _assert_p3e3_internal_delta_gate_normal_mode(p3s)

    _assert_p4_trace_or_explicit_skip(ss)
    _assert_p4_trace_or_explicit_skip(p3s)
