"""Pass12 stub-route recovery: default gate + solver_summary trace fields (NEAR_TRANSPORT / NMS)."""

from __future__ import annotations

import json
from pathlib import Path

from django.test import override_settings

from django_apps.shapez_asteroid.services.asteroid_mining_layout import build_solver_timeline

_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "pass12_telemetry_trace_pack"
    / "fluid_striped_greenfield_bp.json"
)


def _fluid_striped_decoded() -> dict[str, object]:
    return json.loads(_FIXTURE.read_text(encoding="utf-8"))


@override_settings(
    SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY=True,
    SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY=True,
)
def test_fluid_striped_near_transport_stub_route_recovery_attempts_with_trace() -> None:
    """NEAR_TRANSPORT + NO_MATCHING_STUB miners: recovery runs; trace mirrors legacy counters."""

    out = build_solver_timeline(_fluid_striped_decoded())
    ss = out["solver_summary"]
    fv = out["final_validation"]

    assert ss.get("pass12_stub_route_recovery_enabled") is True
    assert ss.get("pass12_stub_route_recovery_disabled_by_flag") is False
    elig = int(ss.get("pass12_stub_route_recovery_eligible_count") or 0)
    assert elig >= 2
    att = int(ss.get("pass12_stub_route_recovery_attempted_count") or 0)
    qr = int(ss.get("pass12_stub_route_recovery_queue_rounds") or 0)
    assert att > 0 or qr > 0
    assert int(ss.get("pass12_preserved_missing_stub_route_recovery_attempted_count") or 0) == att
    assert int(ss.get("pass12_preserved_missing_stub_route_recovery_queue_rounds") or 0) == qr
    assert int(fv.get("missing_stub_count") or 0) == 0
    assert int(fv.get("overlap_violation_count") or 0) == 0


@override_settings(
    SHAPEZ_MINING_PASS12_PRESERVE_STUB_RECOVERY=True,
    SHAPEZ_MINING_PASS12_PRESERVE_STUB_ROUTE_RECOVERY=False,
)
def test_fluid_striped_route_recovery_off_explains_zero_attempts_via_trace() -> None:
    out = build_solver_timeline(_fluid_striped_decoded())
    ss = out["solver_summary"]
    assert ss.get("pass12_stub_route_recovery_enabled") is False
    assert ss.get("pass12_stub_route_recovery_disabled_by_flag") is True
    assert int(ss.get("pass12_stub_route_recovery_eligible_count") or 0) >= 2
    assert int(ss.get("pass12_stub_route_recovery_attempted_count") or 0) == 0
    assert int(ss.get("pass12_stub_route_recovery_queue_rounds") or 0) == 0
