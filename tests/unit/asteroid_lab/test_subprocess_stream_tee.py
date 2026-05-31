"""Subprocess stream tee behavior."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

from django_apps.asteroid_lab.services.subprocess_stream_tee import run_subprocess_with_tee


def test_run_subprocess_with_tee_writes_combined_log_and_parent_stderr(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    result = run_subprocess_with_tee(
        [
            sys.executable,
            "-c",
            "import sys; print('child-out'); print('child-err', file=sys.stderr)",
        ],
        log_path=tmp_path / "logs" / "subprocess.log",
        cwd=tmp_path,
        timeout=5,
        tee_to_parent_stderr=True,
    )

    assert result.returncode == 0
    assert "child-out" in result.stdout
    assert "child-err" in result.stderr
    log_text = (tmp_path / "logs" / "subprocess.log").read_text(encoding="utf-8")
    assert "child-out" in log_text
    assert "child-err" in log_text
    assert "child-out" in capsys.readouterr().err
