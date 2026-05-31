"""Subprocess execution with a durable combined stream log."""

from __future__ import annotations

import subprocess
import sys
import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


@dataclass(frozen=True, slots=True)
class SubprocessTeeResult:
    """Result from a child process whose output was logged."""

    args: tuple[str, ...]
    returncode: int
    elapsed_ms: int
    stdout: str
    stderr: str


def run_subprocess_with_tee(
    args: Sequence[str],
    *,
    log_path: Path,
    cwd: Path,
    timeout: float,
    tee_to_parent_stderr: bool = False,
) -> SubprocessTeeResult:
    """Run a child process with ``shell=False`` and persist stdout/stderr."""

    started = time.monotonic()
    log_path.parent.mkdir(parents=True, exist_ok=True)
    stdout_parts: list[str] = []
    stderr_parts: list[str] = []
    log_lock = threading.Lock()

    process = subprocess.Popen(
        list(args),
        cwd=str(cwd),
        shell=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    with log_path.open("w", encoding="utf-8", newline="\n") as stream:

        def drain_pipe(pipe: TextIO | None, buffer: list[str]) -> None:
            if pipe is None:
                return
            for chunk in iter(pipe.readline, ""):
                if not chunk:
                    break
                buffer.append(chunk)
                with log_lock:
                    stream.write(chunk)
                    stream.flush()
                if tee_to_parent_stderr:
                    print(chunk, file=sys.stderr, end="")

        stdout_thread = threading.Thread(
            target=drain_pipe,
            args=(process.stdout, stdout_parts),
            daemon=True,
        )
        stderr_thread = threading.Thread(
            target=drain_pipe,
            args=(process.stderr, stderr_parts),
            daemon=True,
        )
        stdout_thread.start()
        stderr_thread.start()
        try:
            returncode = process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            returncode = process.wait()
            raise
        finally:
            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)

    stdout = "".join(stdout_parts)
    stderr = "".join(stderr_parts)
    return SubprocessTeeResult(
        args=tuple(str(arg) for arg in args),
        returncode=int(returncode),
        elapsed_ms=int((time.monotonic() - started) * 1000),
        stdout=stdout,
        stderr=stderr,
    )


__all__ = ["SubprocessTeeResult", "run_subprocess_with_tee"]
