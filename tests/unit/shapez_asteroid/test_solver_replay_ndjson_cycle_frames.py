"""NDJSON replay parser + cycle_frames contract (STEP10 v12)."""

from __future__ import annotations

import json
from pathlib import Path

from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_events import (  # noqa: E501
    SolverMutationEventKind,
    build_cycle_frames_from_events,
    prepare_replay_events_for_snapshot,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_replay_ndjson import (  # noqa: E501
    parse_replay_ndjson_file,
    parse_replay_ndjson_text,
)
from django_apps.shapez_asteroid.services.asteroid_mining_layout.solver.solver_trace import (
    trace_bind_replay_events,
    trace_event,
    trace_run_id_current,
    trace_run_scope,
)


def test_parse_stub_only_ndjson_pass_snapshot_fallback(tmp_path: Path) -> None:
    lines = []
    for _ in range(3):
        lines.append(
            json.dumps(
                {
                    "location": "pass12",
                    "message": "bundle_reject_invalid_stub",
                    "data": {"stub_cell": [1, 2], "computation_cycle": 1},
                },
                ensure_ascii=False,
            )
        )
    p = tmp_path / "t.ndjson"
    p.write_text("\n".join(lines) + "\n", encoding="utf-8")
    r = parse_replay_ndjson_file(p)
    assert r["replay_frame_count"] == 0
    assert r["frame_source"] == "pass_snapshot_fallback"
    assert r["fallback_reason"] == "no_replay_frames"


def test_parse_debug_action_is_debug_log_invalid(tmp_path: Path) -> None:
    p = tmp_path / "d.ndjson"
    p.write_text(
        json.dumps({"kind": "action", "location": "x", "action": "run_start", "data": {}}) + "\n",
        encoding="utf-8",
    )
    r = parse_replay_ndjson_file(p)
    assert r["frame_source"] == "debug_log_invalid"


def test_synthetic_replay_frames_at_least_eleven() -> None:
    rows = []
    for n in range(1, 111):
        rows.append(
            {
                "location": "x",
                "message": "replay_frame" if n % 10 == 0 else "phase_checkpoint",
                "data": {
                    "computation_cycle": n,
                    "event_type": "replay_frame" if n % 10 == 0 else "x",
                },
            }
        )
    text = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n"
    parsed = parse_replay_ndjson_text(text)
    assert parsed["replay_frame_count"] == 11
    assert parsed["frame_source"] == "replay_trace"


def test_prepare_replay_events_replay_frame_yields_cycle_frames() -> None:
    events: list[dict] = []
    for i in range(12):
        events.append(
            {
                "kind": SolverMutationEventKind.REPLAY_FRAME.value,
                "phase": "pass12",
                "payload": {
                    "frame_kind": "cycle_snapshot",
                    "trace_computation_cycle": (i + 1) * 10,
                    "metrics": {"extractor_count": i},
                },
            }
        )
    prepare_replay_events_for_snapshot(events)
    cf = build_cycle_frames_from_events(events)
    assert len(cf) == 12
    assert all(isinstance(x.get("replay_event_index"), int) for x in cf)


def test_trace_run_scope_emits_replay_frame_every_ten_cycles(
    tmp_path, monkeypatch, settings
) -> None:
    settings.BASE_DIR = tmp_path
    monkeypatch.setenv("SHAPEZ_SOLVER_ALGO_DEBUG", "1")
    sink: list[dict] = []
    with trace_run_scope():
        rid = trace_run_id_current()
        assert rid is not None
        trace_bind_replay_events(sink)
        for k in range(25):
            trace_event("loc", "phase_checkpoint", {"k": k})
        replay_run = tmp_path / "var" / "asteroid_mining_layout_replay" / f"{rid}.ndjson"
        wire_txt = replay_run.read_text(encoding="utf-8")
    rf_lines: list[dict] = []
    for line in wire_txt.splitlines():
        if not line.strip():
            continue
        o = json.loads(line)
        if o.get("message") == "replay_frame":
            rf_lines.append(o)
    rf_ndjson = len(rf_lines)
    assert (
        len([e for e in sink if e.get("kind") == SolverMutationEventKind.REPLAY_FRAME.value]) == 2
    )
    assert rf_ndjson == 2
    for row in rf_lines:
        d = row.get("data") or {}
        assert "mining_map" not in d
        assert d.get("mining_map_row_count") is None
