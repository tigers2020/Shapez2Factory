"""Django-side wrapper for invoking the Asteroid Lab pure CLI."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from django.conf import settings

from django_apps.asteroid_lab.services.subprocess_stream_tee import (
    DetachedSubprocessHandle,
    SubprocessTeeResult,
    run_subprocess_with_tee,
    spawn_subprocess_with_log_tee,
)

CLI_MODULE = "shapez2_factory.interfaces.cli.asteroid_solve"
_RUN_KEY_RE = re.compile(r"^[A-Za-z0-9._-]+$")


class SolverSubprocessError(Exception):
    """Raised when a subprocess run cannot be started safely or fails."""


@dataclass(frozen=True, slots=True)
class SolverSubprocessRequest:
    """Input bundle needed to invoke the pure CLI solver."""

    run_key: str
    copy_code: str
    game_data_snapshot: dict[str, Any]
    artifact_root: Path
    allowed_root: Path
    timeout_seconds: float
    replace_existing: bool = False
    verbose: bool = False
    throughput_target_percent: int | None = None


@dataclass(frozen=True, slots=True)
class SolverSubprocessResult:
    """Completed subprocess invocation plus resolved artifact paths."""

    run_key: str
    artifact_dir: Path
    subprocess_log_path: Path
    completed: SubprocessTeeResult


@dataclass(frozen=True, slots=True)
class SolverSubprocessSpawnResult:
    """Detached subprocess handle (caller must not wait on the child)."""

    run_key: str
    artifact_dir: Path
    sidecar_log_path: Path
    handle: DetachedSubprocessHandle


def resolve_subprocess_artifact_dir(
    *,
    allowed_root: Path,
    artifact_root: Path,
    run_key: str,
) -> Path:
    """Validate ``run_key`` and ensure final artifact path stays under allowed root."""

    if run_key in (".", "..") or "/" in run_key or "\\" in run_key:
        raise SolverSubprocessError(f"unsafe run_key: {run_key!r}")
    if not _RUN_KEY_RE.fullmatch(run_key):
        raise SolverSubprocessError(f"unsafe run_key: {run_key!r}")
    root = Path(allowed_root).resolve()
    artifact_dir = (Path(artifact_root) / run_key).resolve()
    try:
        artifact_dir.relative_to(root)
    except ValueError as exc:
        raise SolverSubprocessError(f"artifact path escapes allowed root: {run_key!r}") from exc
    return artifact_dir


def default_artifact_root() -> Path:
    """Return the configured Django artifact root for CLI subprocess runs."""

    return Path(getattr(settings, "ASTEROID_LAB_ARTIFACT_ROOT", settings.BASE_DIR / "var" / "runs"))


def _write_inputs(request: SolverSubprocessRequest) -> tuple[Path, Path]:
    input_dir = request.artifact_root / ".subprocess_inputs" / request.run_key
    input_dir.mkdir(parents=True, exist_ok=True)
    copy_path = input_dir / "copy.txt"
    snapshot_path = input_dir / "game_data_snapshot.json"
    copy_path.write_text(request.copy_code.strip() + "\n", encoding="utf-8")
    snapshot_path.write_text(
        json.dumps(request.game_data_snapshot, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return copy_path, snapshot_path


def build_solver_cli_args(
    request: SolverSubprocessRequest,
    *,
    copy_path: Path,
    snapshot_path: Path,
) -> list[str]:
    """Build the exact ``sys.executable -m ...`` invocation."""

    args = [
        sys.executable,
        "-m",
        CLI_MODULE,
        "run",
        "--artifact-root",
        str(request.artifact_root),
        "--allowed-root",
        str(request.allowed_root),
        "--run-key",
        request.run_key,
        "--copy-file",
        str(copy_path),
        "--snapshot",
        str(snapshot_path),
    ]
    if request.replace_existing:
        args.append("--replace-existing")
    if request.verbose:
        args.append("--verbose")
    if request.throughput_target_percent is not None:
        args.extend(
            [
                "--throughput-target-percent",
                str(int(request.throughput_target_percent)),
            ]
        )
    return args


def run_solver_subprocess(
    request: SolverSubprocessRequest,
    *,
    cwd: Path | None = None,
    tee_to_parent_stderr: bool = False,
) -> SolverSubprocessResult:
    """Invoke the CLI and copy the combined subprocess log into the final artifact."""

    artifact_dir = resolve_subprocess_artifact_dir(
        allowed_root=request.allowed_root,
        artifact_root=request.artifact_root,
        run_key=request.run_key,
    )
    copy_path, snapshot_path = _write_inputs(request)
    sidecar_log_path = request.artifact_root / ".subprocess_logs" / f"{request.run_key}.log"
    args = build_solver_cli_args(request, copy_path=copy_path, snapshot_path=snapshot_path)
    try:
        completed = run_subprocess_with_tee(
            args,
            log_path=sidecar_log_path,
            cwd=Path(cwd or settings.BASE_DIR),
            timeout=request.timeout_seconds,
            tee_to_parent_stderr=tee_to_parent_stderr,
        )
    except subprocess.TimeoutExpired as exc:
        msg = (
            f"solver subprocess timed out run_key={request.run_key!r} "
            f"after {request.timeout_seconds}s"
        )
        raise SolverSubprocessError(msg) from exc
    final_log_path = artifact_dir / "logs" / "subprocess.log"
    if artifact_dir.exists():
        final_log_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(sidecar_log_path, final_log_path)
    if completed.returncode != 0:
        raise SolverSubprocessError(
            f"solver subprocess failed run_key={request.run_key!r} exit={completed.returncode}"
        )
    return SolverSubprocessResult(
        run_key=request.run_key,
        artifact_dir=artifact_dir,
        subprocess_log_path=final_log_path if final_log_path.exists() else sidecar_log_path,
        completed=completed,
    )


def spawn_solver_subprocess_detached(
    request: SolverSubprocessRequest,
    *,
    cwd: Path | None = None,
    tee_to_parent_stderr: bool = False,
) -> SolverSubprocessSpawnResult:
    """Spawn the CLI without blocking; logs go to the sidecar path until finalize."""

    artifact_dir = resolve_subprocess_artifact_dir(
        allowed_root=request.allowed_root,
        artifact_root=request.artifact_root,
        run_key=request.run_key,
    )
    copy_path, snapshot_path = _write_inputs(request)
    sidecar_log_path = request.artifact_root / ".subprocess_logs" / f"{request.run_key}.log"
    args = build_solver_cli_args(request, copy_path=copy_path, snapshot_path=snapshot_path)
    handle = spawn_subprocess_with_log_tee(
        args,
        log_path=sidecar_log_path,
        cwd=Path(cwd or settings.BASE_DIR),
        tee_to_parent_stderr=tee_to_parent_stderr,
    )
    return SolverSubprocessSpawnResult(
        run_key=request.run_key,
        artifact_dir=artifact_dir,
        sidecar_log_path=sidecar_log_path,
        handle=handle,
    )


__all__ = [
    "CLI_MODULE",
    "SolverSubprocessError",
    "SolverSubprocessRequest",
    "SolverSubprocessResult",
    "build_solver_cli_args",
    "default_artifact_root",
    "resolve_subprocess_artifact_dir",
    "run_solver_subprocess",
    "SolverSubprocessSpawnResult",
    "spawn_solver_subprocess_detached",
]
