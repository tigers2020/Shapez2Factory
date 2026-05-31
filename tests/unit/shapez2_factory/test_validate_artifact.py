"""PR-CLI-3a ??CLI shell + ``validate-artifact`` command (BA-1 pure core).

These tests build real artifacts with :class:`AtomicArtifactWriter` and drive the
CLI ``main()`` entry point, asserting fail-closed validation behaviour and the
typed exit codes (``ExitCode``).
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from shapez2_factory.adapters.asteroid_lab.artifact_manifest import (
    MANIFEST_FILENAME,
    MANIFEST_SCHEMA_VERSION,
    ArtifactManifest,
)
from shapez2_factory.adapters.asteroid_lab.artifact_writer import AtomicArtifactWriter
from shapez2_factory.adapters.asteroid_lab.run_status import RunLifecycleStatus
from shapez2_factory.interfaces.cli.asteroid_solve import ExitCode, main

_REPO = Path(__file__).resolve().parents[3]
_COPY_FIXTURE = _REPO / "tests" / "fixtures" / "asteroid_lab" / "reconstruction_required_.txt"
_SNAPSHOT_FIXTURE = _REPO / "tests" / "fixtures" / "asteroid_lab" / "game_data_snapshot_min.json"


def _build_valid_artifact(tmp_path: Path, run_key: str = "run-1") -> Path:
    writer = AtomicArtifactWriter(tmp_path, run_key)
    writer.open_staging()
    writer.write_output("outputs/a.json", b'{"x":1}')
    manifest = ArtifactManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        run_key=run_key,
        lifecycle_status=RunLifecycleStatus.ARTIFACT_WRITTEN,
        created_at_utc="2026-05-30T00:00:00Z",
        core_build_id="test",
    )
    return writer.finalize(manifest)


def test_validate_artifact_accepts_valid_artifact(tmp_path: Path) -> None:
    final = _build_valid_artifact(tmp_path)
    assert main(["validate-artifact", "--dir", str(final)]) == ExitCode.OK


def test_validate_artifact_rejects_tampered_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    final = _build_valid_artifact(tmp_path)
    (final / "outputs" / "a.json").write_bytes(b'{"x":999}')
    assert main(["validate-artifact", "--dir", str(final)]) == ExitCode.VALIDATION_FAILED
    stderr = capsys.readouterr().err
    assert "hash mismatch" in stderr
    assert "outputs/a.json" in stderr


def test_validate_artifact_rejects_missing_payload_file(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    final = _build_valid_artifact(tmp_path)
    (final / "outputs" / "a.json").unlink()
    assert main(["validate-artifact", "--dir", str(final)]) == ExitCode.VALIDATION_FAILED
    stderr = capsys.readouterr().err
    assert "missing" in stderr
    assert "outputs/a.json" in stderr


def test_validate_artifact_rejects_non_written_lifecycle(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "running"
    artifact_dir.mkdir()
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "run_key": "run-1",
        "lifecycle_status": "running",
        "created_at_utc": "2026-05-30T00:00:00Z",
        "core_build_id": "test",
        "content_hashes": {},
        "paths": {},
        "game_data_provenance": {},
        "error_code": None,
    }
    (artifact_dir / MANIFEST_FILENAME).write_text(json.dumps(manifest), encoding="utf-8")
    assert main(["validate-artifact", "--dir", str(artifact_dir)]) == ExitCode.VALIDATION_FAILED


def test_validate_artifact_rejects_unknown_schema_version(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "future"
    artifact_dir.mkdir()
    manifest = {
        "schema_version": 999,
        "run_key": "run-1",
        "lifecycle_status": "artifact_written",
        "created_at_utc": "2026-05-30T00:00:00Z",
        "core_build_id": "test",
        "content_hashes": {},
        "paths": {},
        "game_data_provenance": {},
        "error_code": None,
    }
    (artifact_dir / MANIFEST_FILENAME).write_text(json.dumps(manifest), encoding="utf-8")
    assert main(["validate-artifact", "--dir", str(artifact_dir)]) == ExitCode.VALIDATION_FAILED


def test_validate_artifact_rejects_missing_manifest(tmp_path: Path) -> None:
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    assert main(["validate-artifact", "--dir", str(empty_dir)]) == ExitCode.VALIDATION_FAILED


def test_validate_artifact_rejects_malformed_json(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "broken"
    artifact_dir.mkdir()
    (artifact_dir / MANIFEST_FILENAME).write_text("{not json", encoding="utf-8")
    assert main(["validate-artifact", "--dir", str(artifact_dir)]) == ExitCode.VALIDATION_FAILED


def test_validate_artifact_rejects_unknown_lifecycle_value(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "bogus_lifecycle"
    artifact_dir.mkdir()
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "run_key": "run-1",
        "lifecycle_status": "bogus",
        "created_at_utc": "2026-05-30T00:00:00Z",
        "core_build_id": "test",
        "content_hashes": {},
        "paths": {},
        "game_data_provenance": {},
        "error_code": None,
    }
    (artifact_dir / MANIFEST_FILENAME).write_text(json.dumps(manifest), encoding="utf-8")
    assert main(["validate-artifact", "--dir", str(artifact_dir)]) == ExitCode.VALIDATION_FAILED


def test_validate_artifact_rejects_traversal_relpath(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    final = _build_valid_artifact(tmp_path)
    # Out-of-tree file that genuinely exists, with a *matching* hash. Without a
    # containment guard, validation would hash this file and wrongly succeed (OK);
    # the guard must reject the traversal relpath first ??VALIDATION_FAILED.
    escape_bytes = b"out-of-tree secret"
    escape_file = final.parent / "escape.txt"
    escape_file.write_bytes(escape_bytes)
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "run_key": "run-1",
        "lifecycle_status": "artifact_written",
        "created_at_utc": "2026-05-30T00:00:00Z",
        "core_build_id": "test",
        "content_hashes": {"../escape.txt": hashlib.sha256(escape_bytes).hexdigest()},
        "paths": {},
        "game_data_provenance": {},
        "error_code": None,
    }
    (final / MANIFEST_FILENAME).write_text(json.dumps(manifest), encoding="utf-8")
    assert main(["validate-artifact", "--dir", str(final)]) == ExitCode.VALIDATION_FAILED
    stderr = capsys.readouterr().err
    assert "../escape.txt" in stderr


def test_validate_artifact_rejects_missing_required_field(tmp_path: Path) -> None:
    artifact_dir = tmp_path / "missing_field"
    artifact_dir.mkdir()
    manifest = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "lifecycle_status": "artifact_written",
        "created_at_utc": "2026-05-30T00:00:00Z",
        "core_build_id": "test",
        "content_hashes": {},
        "paths": {},
        "game_data_provenance": {},
        "error_code": None,
    }
    (artifact_dir / MANIFEST_FILENAME).write_text(json.dumps(manifest), encoding="utf-8")
    assert main(["validate-artifact", "--dir", str(artifact_dir)]) == ExitCode.VALIDATION_FAILED


def test_validate_artifact_emits_ba9_start_and_end_lines(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    # BA-9: additive stderr observability around a successful validate-artifact run.
    final = _build_valid_artifact(tmp_path)
    assert main(["validate-artifact", "--dir", str(final)]) == ExitCode.OK
    stderr = capsys.readouterr().err
    assert "asteroid_cli validate-artifact start" in stderr
    end_lines = [ln for ln in stderr.splitlines() if "validate-artifact end" in ln]
    assert len(end_lines) == 1
    assert "exit=0" in end_lines[0]
    assert "ok=true" in end_lines[0]


def test_validate_artifact_emits_ba9_end_line_on_failure(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    empty_dir = tmp_path / "empty"
    empty_dir.mkdir()
    assert main(["validate-artifact", "--dir", str(empty_dir)]) == ExitCode.VALIDATION_FAILED
    stderr = capsys.readouterr().err
    end_lines = [ln for ln in stderr.splitlines() if "validate-artifact end" in ln]
    assert len(end_lines) == 1
    assert "exit=10" in end_lines[0]
    assert "ok=false" in end_lines[0]


def test_validate_artifact_ba9_disabled_emits_no_console_line(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ASTEROID_LAB_CLI_CONSOLE_LOG", "0")
    final = _build_valid_artifact(tmp_path)
    assert main(["validate-artifact", "--dir", str(final)]) == ExitCode.OK
    assert "asteroid_cli" not in capsys.readouterr().err


def test_run_subcommand_writes_artifact(tmp_path: Path) -> None:
    assert (
        main(
            [
                "run",
                "--allowed-root",
                str(tmp_path),
                "--artifact-root",
                str(tmp_path),
                "--run-key",
                "run-1",
                "--copy-file",
                str(_COPY_FIXTURE),
                "--snapshot",
                str(_SNAPSHOT_FIXTURE),
            ]
        )
        == ExitCode.OK
    )
    final = tmp_path / "run-1"
    assert (final / "manifest.json").is_file()
    assert (final / "output" / "replay_core.jsonl").is_file()
    assert main(["validate-artifact", "--dir", str(final)]) == ExitCode.OK


def test_run_subcommand_rejects_unsafe_run_key(tmp_path: Path) -> None:
    assert (
        main(
            [
                "run",
                "--artifact-root",
                str(tmp_path),
                "--run-key",
                "../evil",
                "--copy-file",
                str(_COPY_FIXTURE),
                "--snapshot",
                str(_SNAPSHOT_FIXTURE),
            ]
        )
        == ExitCode.VALIDATION_FAILED
    )


def test_run_subcommand_rejects_out_of_root_artifact_root(tmp_path: Path) -> None:
    # Two sibling dirs: artifact_root is NOT nested under allowed_root, so Guard C
    # threat-2 containment must reject even a syntactically valid run_key.
    allowed = tmp_path / "allowed"
    outside = tmp_path / "outside"
    allowed.mkdir()
    outside.mkdir()
    assert (
        main(
            [
                "run",
                "--allowed-root",
                str(allowed),
                "--artifact-root",
                str(outside),
                "--run-key",
                "run-1",
                "--copy-file",
                str(_COPY_FIXTURE),
                "--snapshot",
                str(_SNAPSHOT_FIXTURE),
            ]
        )
        == ExitCode.VALIDATION_FAILED
    )
