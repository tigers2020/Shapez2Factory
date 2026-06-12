"""Asteroid Lab structured trace logging contracts."""

from __future__ import annotations

import json
from pathlib import Path

from django_apps.asteroid_lab.services.trace_logging import AsteroidLabTraceLogger


def _jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_trace_logger_writes_stage_jsonl_and_summary(tmp_path) -> None:
    logger = AsteroidLabTraceLogger(
        run_id="lab-test-run",
        root_dir=tmp_path,
        project_slug="proj-a",
        solver_run_id=42,
    )
    logger.event(
        stage="decode.coord_projection",
        event="coord_projected",
        source={"module": "m", "function": "f"},
    )
    logger.close()

    run_dir = tmp_path / "runs" / "lab-test-run"
    rows = _jsonl(run_dir / "01_decode.jsonl")
    assert rows[0]["run_id"] == "lab-test-run"
    assert rows[0]["project_slug"] == "proj-a"
    assert rows[0]["solver_run_id"] == 42
    assert rows[0]["stage"] == "decode.coord_projection"
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["event_count"] == 1
    assert summary["stage_counts"]["decode.coord_projection"] == 1


def test_trace_logger_caps_events(tmp_path) -> None:
    logger = AsteroidLabTraceLogger(
        run_id="lab-cap-run",
        root_dir=tmp_path,
        max_events=1,
    )
    logger.event(stage="request", event="run_started")
    logger.event(stage="decode.raw", event="raw_blueprint_loaded")
    logger.close()

    run_dir = tmp_path / "runs" / "lab-cap-run"
    request_rows = _jsonl(run_dir / "00_request.jsonl")
    assert [r["event"] for r in request_rows] == ["run_started", "trace_log_truncated"]
    summary = json.loads((run_dir / "summary.json").read_text(encoding="utf-8"))
    assert summary["truncated"] is True


class _FakeReconEv:
    def __init__(
        self,
        trace_event_type: str,
        *,
        coords: frozenset[tuple[int, int]] | None = None,
    ) -> None:
        self.trace_event_type = trace_event_type
        self.summary_json = {"k": trace_event_type}
        self.coords = frozenset() if coords is None else coords


def test_record_reconstruction_trace_keeps_final_beyond_sample_limit(tmp_path) -> None:
    from django_apps.asteroid_lab.services.trace_logging import record_reconstruction_trace_events

    logger = AsteroidLabTraceLogger(
        run_id="lab-recon-tail",
        root_dir=tmp_path,
        sample_limit=8,
    )
    filler = [_FakeReconEv(f"noise_{i}") for i in range(40)]
    final = _FakeReconEv(
        "reconstruction_final",
        coords=frozenset({(1, 1), (2, 2)}),
    )
    record_reconstruction_trace_events(logger, filler + [final])
    logger.close()

    rows = _jsonl(tmp_path / "runs" / "lab-recon-tail" / "03_reconstruction.jsonl")
    assert any(r.get("event") == "reconstruction_final" for r in rows)
    tail = [r for r in rows if r.get("event") == "reconstruction_final"][-1]
    assert tail.get("coord_count") == 2
