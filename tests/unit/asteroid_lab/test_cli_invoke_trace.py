"""Console trace for Django-side solver invocations."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.observability.cli_invoke_trace import cli_invoke_trace


def test_cli_invoke_trace_emits_start_and_end(capsys: pytest.CaptureFixture[str]) -> None:
    with cli_invoke_trace(
        surface="http_run_solver",
        command="run_solver",
        slug="trace-slug",
    ) as trace:
        trace.update(exit=0, solver_run_id=42, ok=True)

    stderr = capsys.readouterr().err
    assert "asteroid_cli run_solver start surface=http_run_solver slug=trace-slug" in stderr
    assert "asteroid_cli run_solver end surface=http_run_solver slug=trace-slug" in stderr
    assert "exit=0" in stderr
    assert "solver_run_id=42" in stderr
    assert "ok=true" in stderr


def test_cli_invoke_trace_emits_exception_end(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(RuntimeError):
        with cli_invoke_trace(
            surface="http_run_solver",
            command="run_solver",
            slug="trace-error",
        ):
            raise RuntimeError("boom")

    stderr = capsys.readouterr().err
    assert "asteroid_cli run_solver end surface=http_run_solver slug=trace-error" in stderr
    assert "exit=1" in stderr
    assert "error_code=RuntimeError" in stderr
    assert "ok=false" in stderr
