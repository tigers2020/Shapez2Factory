"""CLI smoke for ``scripts/debug/pass12_preserve_recovery_ab.py`` (stub-route A/B + probe)."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
_FIXTURE_PACK = ROOT / "tests" / "fixtures" / "pass12_telemetry_trace_pack"
_FLUID_STRIPED_BP = _FIXTURE_PACK / "fluid_striped_greenfield_bp.json"


def test_probe_replay_input_nonreplayable(tmp_path: Path) -> None:
    p = tmp_path / "trace.ndjson"
    p.write_text('{"kind": "x", "data": 1}\n', encoding="utf-8")
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "debug" / "pass12_preserve_recovery_ab.py"),
        "--probe-replay-input",
        str(p),
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
    assert proc.returncode == 3
    row = json.loads(proc.stdout)
    assert row.get("replayable") is False


def test_stub_route_recovery_ab_striped_smoke() -> None:
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "debug" / "pass12_preserve_recovery_ab.py"),
        "--stub-route-recovery-ab",
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    out = ROOT / "var" / "pass12_stub_route_recovery_ab_experiment.json"
    assert out.is_file()
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload.get("ab_mode") == "stub_route_recovery"
    assert "baseline_route_recovery_off" in payload
    assert "route_recovery_on" in payload


def test_probe_replay_striped_fixture_replayable() -> None:
    bp = ROOT / "tests" / "fixtures" / "pass12_telemetry_trace_pack" / "striped_greenfield_bp.json"
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "debug" / "pass12_preserve_recovery_ab.py"),
        "--probe-replay-input",
        str(bp),
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    row = json.loads(proc.stdout)
    assert row.get("replayable") is True


def test_stub_route_recovery_ab_bp_json_striped_fixture() -> None:
    bp = ROOT / "tests" / "fixtures" / "pass12_telemetry_trace_pack" / "striped_greenfield_bp.json"
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "debug" / "pass12_preserve_recovery_ab.py"),
        "--stub-route-recovery-ab",
        "--bp-json",
        str(bp),
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    out = ROOT / "var" / "pass12_stub_route_recovery_ab_experiment.json"
    payload = json.loads(out.read_text(encoding="utf-8"))
    assert payload.get("input_source", {}).get("kind") == "bp_json"
    assert payload.get("summary_diff", {}).get("decision_hint") is not None


def test_probe_replay_fluid_striped_fixture_replayable() -> None:
    bp = _FLUID_STRIPED_BP
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "debug" / "pass12_preserve_recovery_ab.py"),
        "--probe-replay-input",
        str(bp),
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    row = json.loads(proc.stdout)
    assert row.get("replayable") is True


def test_stub_route_recovery_ab_fluid_striped_ne_stub_attempts_route_on() -> None:
    """existing_fluid_layout + merged 3 miners: NEAR_TRANSPORT drops; route ON attempts recovery."""

    bp = _FLUID_STRIPED_BP
    cmd = [
        sys.executable,
        str(ROOT / "scripts" / "debug" / "pass12_preserve_recovery_ab.py"),
        "--stub-route-recovery-ab",
        "--bp-json",
        str(bp),
    ]
    proc = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr
    out = ROOT / "var" / "pass12_stub_route_recovery_ab_experiment.json"
    payload = json.loads(out.read_text(encoding="utf-8"))
    off = payload["baseline_route_recovery_off"]
    on = payload["route_recovery_on"]
    assert off["pass12_preserved_missing_stub_route_recovery_attempted_count"] == 0
    assert on["pass12_preserved_missing_stub_route_recovery_attempted_count"] >= 1
    assert on["pass12_preserved_missing_stub_route_recovery_success_count"] == 0
    assert (
        on["pass12_preserved_missing_stub_route_recovery_rejected_by_no_stub_space_count"]
        == on["pass12_preserved_missing_stub_route_recovery_attempted_count"]
    )
    assert on["geometry_valid"] is True
    assert on["connectivity_valid"] is True
    assert on["transport_connected"] is True
    assert (
        payload["summary_diff"]["decision_hint"]
        == "attempted_but_no_success_review_rejection_histogram"
    )
