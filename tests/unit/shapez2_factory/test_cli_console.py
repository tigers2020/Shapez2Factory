"""PR-CLI-3a (BA-9) ??``cli_console`` formatter + env-gate tests (spec §11).

The formatter is pure-core (stdlib only); these tests inject a fixed timestamp so
the bracketed prefix is deterministic regardless of the host timezone.
"""

from __future__ import annotations

import time

import pytest

from shapez2_factory.adapters.asteroid_lab.cli_console import (
    ENV_CONSOLE_LOG,
    console_logging_enabled,
    emit_cli_line,
)

# Fixed epoch seconds; rendered through the same strftime the formatter uses so the
# expectation is timezone-independent on any CI host.
_FIXED_NOW = 1_748_620_169.0
_EXPECTED_TS = time.strftime("%d/%b/%Y %H:%M:%S", time.localtime(_FIXED_NOW))


def test_emit_writes_single_line_with_bracketed_prefix(
    capsys: pytest.CaptureFixture[str],
) -> None:
    emit_cli_line("validate-artifact start", now=_FIXED_NOW)
    captured = capsys.readouterr()
    assert captured.out == ""
    lines = captured.err.splitlines()
    assert len(lines) == 1
    assert lines[0] == f"[{_EXPECTED_TS}] asteroid_cli validate-artifact start"


def test_emit_renders_fields_in_order(capsys: pytest.CaptureFixture[str]) -> None:
    emit_cli_line("run end", now=_FIXED_NOW, run_key="run-1", exit=0, elapsed_ms=12)
    line = capsys.readouterr().err.strip()
    assert line == (f"[{_EXPECTED_TS}] asteroid_cli run end run_key=run-1 exit=0 elapsed_ms=12")


def test_emit_omits_none_fields(capsys: pytest.CaptureFixture[str]) -> None:
    emit_cli_line("run end", now=_FIXED_NOW, run_key=None, exit=0)
    line = capsys.readouterr().err.strip()
    assert "run_key" not in line
    assert line.endswith("asteroid_cli run end exit=0")


def test_emit_renders_bools_lowercase(capsys: pytest.CaptureFixture[str]) -> None:
    emit_cli_line("run end", now=_FIXED_NOW, ok=True)
    assert capsys.readouterr().err.strip().endswith("ok=true")
    emit_cli_line("run end", now=_FIXED_NOW, ok=False)
    assert capsys.readouterr().err.strip().endswith("ok=false")


@pytest.mark.parametrize("value", ["1", "true", "TRUE", "yes", "", "on"])
def test_console_enabled_for_non_disabling_values(
    monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setenv(ENV_CONSOLE_LOG, value)
    assert console_logging_enabled() is True


def test_console_enabled_when_unset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_CONSOLE_LOG, raising=False)
    assert console_logging_enabled() is True


@pytest.mark.parametrize("value", ["0", "false", "FALSE", "no", "No", " false "])
def test_console_disabled_for_disabling_values(monkeypatch: pytest.MonkeyPatch, value: str) -> None:
    monkeypatch.setenv(ENV_CONSOLE_LOG, value)
    assert console_logging_enabled() is False


def test_emit_is_noop_when_disabled(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv(ENV_CONSOLE_LOG, "0")
    emit_cli_line("validate-artifact start", now=_FIXED_NOW)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
