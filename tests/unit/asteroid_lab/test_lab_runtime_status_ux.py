"""Lab Run Solver runtime status UX (C1): log tail panel contract."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
TEMPLATE = REPO / "django_apps" / "web" / "templates" / "web" / "asteroid_miner_layout_solver.html"
JS = REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"


def test_lab_template_has_replay_run_log_panel() -> None:
    html = TEMPLATE.read_text(encoding="utf-8")
    assert 'id="lab-replay-run-log"' in html


def test_lab_js_renders_log_tail_with_text_content_only() -> None:
    js = JS.read_text(encoding="utf-8")
    assert "function truncateLabStatusLogTail" in js
    assert "function renderReplayRunLogTail" in js
    assert 'getElementById("lab-replay-run-log")' in js
    assert ".textContent" in js[js.index("function renderReplayRunLogTail") : js.index("function renderReplayRunStatus")]
    assert "innerHTML" not in js[js.index("function renderReplayRunLogTail") : js.index("function renderReplayRunStatus")]


def test_render_replay_run_status_uses_log_tail_when_running() -> None:
    js = JS.read_text(encoding="utf-8")
    block = js[js.index("function renderReplayRunStatus") : js.index("function getCookie")]
    assert "renderReplayRunLogTail" in block
    assert "feedback.log_tail" in block or "log_tail" in block


def test_poll_solver_run_status_uses_pending_finalize_timer() -> None:
    js = JS.read_text(encoding="utf-8")
    block = js[js.index("function pollSolverRunStatus") : js.index("const runSolverBtn")]
    assert "LAB_STATUS_LONG_POLL_MS" in block
    assert "pending_finalize" in block
    assert "setInterval" in block or "setTimeout" in block
    assert "clearTimeout" in block or "clearInterval" in block
    assert "elapsed_seconds" in block


def test_poll_solver_run_status_does_not_overlap_fetches() -> None:
    js = JS.read_text(encoding="utf-8")
    block = js[js.index("function pollSolverRunStatus") : js.index("const runSolverBtn")]
    assert "Promise.all" not in block
    assert "parallel" not in block.lower()
