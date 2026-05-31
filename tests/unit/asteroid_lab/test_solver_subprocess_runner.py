"""BA-7 subprocess runner gates."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

import pytest
from django.test import override_settings

from django_apps.asteroid_lab.services import solver_subprocess_runner as runner
from django_apps.asteroid_lab.services.subprocess_stream_tee import SubprocessTeeResult


def _request(tmp_path: Path, *, run_key: str = "run-1") -> runner.SolverSubprocessRequest:
    return runner.SolverSubprocessRequest(
        run_key=run_key,
        copy_code="SHAPEZ2-4-e30=",
        game_data_snapshot={"schema_version": "game_data_snapshot_v1"},
        artifact_root=tmp_path / "runs",
        allowed_root=tmp_path / "runs",
        timeout_seconds=3,
    )


def test_resolve_subprocess_artifact_dir_rejects_traversal(tmp_path: Path) -> None:
    with pytest.raises(runner.SolverSubprocessError, match="unsafe run_key"):
        runner.resolve_subprocess_artifact_dir(
            allowed_root=tmp_path / "runs",
            artifact_root=tmp_path / "runs",
            run_key="../escape",
        )


def test_build_solver_cli_args_uses_python_module_and_list_args(tmp_path: Path) -> None:
    request = _request(tmp_path)
    args = runner.build_solver_cli_args(
        request,
        copy_path=tmp_path / "copy.txt",
        snapshot_path=tmp_path / "snapshot.json",
    )

    assert args[0]
    assert args[1:4] == ["-m", runner.CLI_MODULE, "run"]
    assert "--artifact-root" in args
    assert "--copy-file" in args
    assert "--snapshot" in args
    assert "--verbose" not in args


def test_build_solver_cli_args_passes_throughput_target_percent(tmp_path: Path) -> None:
    request = runner.SolverSubprocessRequest(
        run_key="run-tp",
        copy_code="SHAPEZ2-4-e30=",
        game_data_snapshot={"schema_version": "game_data_snapshot_v1"},
        artifact_root=tmp_path / "runs",
        allowed_root=tmp_path / "runs",
        timeout_seconds=3,
        throughput_target_percent=88,
    )
    args = runner.build_solver_cli_args(
        request,
        copy_path=tmp_path / "copy.txt",
        snapshot_path=tmp_path / "snapshot.json",
    )

    idx = args.index("--throughput-target-percent")
    assert args[idx + 1] == "88"


@override_settings(BASE_DIR=Path("F:/Python_Projects/shapez2Factory"))
def test_run_solver_subprocess_invokes_tee_with_safe_arguments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []

    def fake_run_subprocess_with_tee(*args: Any, **kwargs: Any) -> SubprocessTeeResult:
        calls.append({"args": args, "kwargs": kwargs})
        artifact_dir = tmp_path / "runs" / "run-1"
        artifact_dir.mkdir(parents=True)
        log_path = Path(kwargs["log_path"])
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text("asteroid_cli run end exit=0\n", encoding="utf-8")
        return SubprocessTeeResult(
            args=tuple(str(part) for part in args[0]),
            returncode=0,
            elapsed_ms=12,
            stdout="",
            stderr="asteroid_cli run end exit=0\n",
        )

    monkeypatch.setattr(runner, "run_subprocess_with_tee", fake_run_subprocess_with_tee)

    result = runner.run_solver_subprocess(
        _request(tmp_path),
        cwd=tmp_path,
        tee_to_parent_stderr=True,
    )

    assert result.artifact_dir == tmp_path / "runs" / "run-1"
    assert result.subprocess_log_path == tmp_path / "runs" / "run-1" / "logs" / "subprocess.log"
    assert result.subprocess_log_path.read_text(encoding="utf-8")
    assert calls
    call = calls[0]
    assert isinstance(call["args"], tuple)
    assert call["args"][0][1:4] == ["-m", runner.CLI_MODULE, "run"]
    assert call["kwargs"]["timeout"] == 3
    assert call["kwargs"]["tee_to_parent_stderr"] is True


def test_run_solver_subprocess_timeout_raises_solver_subprocess_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run_subprocess_with_tee(*_args: Any, **_kwargs: Any) -> SubprocessTeeResult:
        raise subprocess.TimeoutExpired(cmd=["python"], timeout=3)

    monkeypatch.setattr(runner, "run_subprocess_with_tee", fake_run_subprocess_with_tee)

    with pytest.raises(runner.SolverSubprocessError, match="timed out"):
        runner.run_solver_subprocess(_request(tmp_path), cwd=tmp_path)
