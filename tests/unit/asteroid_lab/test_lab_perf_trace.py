"""Lab perf trace — silent by default; JSONL when ASTEROID_LAB_PERF_TRACE enabled."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from django.test import override_settings

from django_apps.asteroid_lab.observability.lab_perf_trace import (
    lab_perf_trace_log_path,
    lab_perf_trace_request,
    perf_span,
    record_perf_meta,
)


@pytest.fixture
def perf_log_path(tmp_path, settings) -> Path:
    settings.BASE_DIR = tmp_path
    return tmp_path / "var" / "log" / "asteroid_lab_perf" / "lab_perf.jsonl"


@override_settings(ASTEROID_LAB_PERF_TRACE=False)
def test_lab_perf_trace_disabled_emits_nothing(perf_log_path: Path) -> None:
    with lab_perf_trace_request(request_kind="test"):
        with perf_span("noop"):
            pass
    assert not perf_log_path.exists()


@override_settings(ASTEROID_LAB_PERF_TRACE=True)
def test_lab_perf_trace_emits_expected_phase_keys(perf_log_path: Path) -> None:
    with lab_perf_trace_request(request_kind="project_page", project_slug="demo"):
        with perf_span("replay_compose_ms"):
            pass
        record_perf_meta(frame_count=3, html_bytes=1000)

    assert perf_log_path.exists()
    line = perf_log_path.read_text(encoding="utf-8").strip().splitlines()[-1]
    record = json.loads(line)
    assert record["event"] == "asteroid_lab_perf"
    assert record["request_kind"] == "project_page"
    assert record["project_slug"] == "demo"
    assert "total_ms" in record
    assert "replay_compose_ms" in record
    assert record["frame_count"] == 3
    assert record["html_bytes"] == 1000


def test_lab_perf_trace_log_path_under_var_log() -> None:
    path = lab_perf_trace_log_path()
    assert "asteroid_lab_perf" in path.as_posix()
    assert path.name == "lab_perf.jsonl"
