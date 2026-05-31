"""PR-CLI-3b: typed CLI exit-code mapping for ``asteroid_solve run``."""

from __future__ import annotations

from pathlib import Path

from shapez2_factory.interfaces.cli.asteroid_solve import ExitCode, main

_REPO = Path(__file__).resolve().parents[3]
_COPY_FIXTURE = _REPO / "tests" / "fixtures" / "asteroid_lab" / "reconstruction_required_.txt"
_SNAPSHOT_FIXTURE = _REPO / "tests" / "fixtures" / "asteroid_lab" / "game_data_snapshot_min.json"


def test_run_returns_ok_for_written_artifact(tmp_path: Path) -> None:
    assert (
        main(
            [
                "run",
                "--allowed-root",
                str(tmp_path),
                "--artifact-root",
                str(tmp_path),
                "--run-key",
                "exit-ok",
                "--copy-file",
                str(_COPY_FIXTURE),
                "--snapshot",
                str(_SNAPSHOT_FIXTURE),
            ]
        )
        == ExitCode.OK
    )


def test_run_returns_validation_failed_for_missing_snapshot(tmp_path: Path) -> None:
    assert (
        main(
            [
                "run",
                "--allowed-root",
                str(tmp_path),
                "--artifact-root",
                str(tmp_path),
                "--run-key",
                "exit-missing-snapshot",
                "--copy-file",
                str(_COPY_FIXTURE),
                "--snapshot",
                str(tmp_path / "missing.json"),
            ]
        )
        == ExitCode.VALIDATION_FAILED
    )


def test_run_returns_validation_failed_for_snapshot_hash_mismatch(tmp_path: Path) -> None:
    assert (
        main(
            [
                "run",
                "--allowed-root",
                str(tmp_path),
                "--artifact-root",
                str(tmp_path),
                "--run-key",
                "exit-hash-mismatch",
                "--copy-file",
                str(_COPY_FIXTURE),
                "--snapshot",
                str(_SNAPSHOT_FIXTURE),
                "--expected-snapshot-hash",
                "sha256:not-the-fixture-hash",
            ]
        )
        == ExitCode.VALIDATION_FAILED
    )
