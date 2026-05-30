"""PR-CLI-3a — CLI shell + ``validate-artifact`` command (BA-1 pure core).

These tests build real artifacts with :class:`AtomicArtifactWriter` and drive the
CLI ``main()`` entry point, asserting fail-closed validation behaviour and the
typed exit codes (``ExitCode``).
"""

from __future__ import annotations

import json
from pathlib import Path

from shapez2_factory.adapters.asteroid_lab.artifact_manifest import (
    MANIFEST_FILENAME,
    MANIFEST_SCHEMA_VERSION,
    ArtifactManifest,
)
from shapez2_factory.adapters.asteroid_lab.artifact_writer import AtomicArtifactWriter
from shapez2_factory.adapters.asteroid_lab.run_status import RunLifecycleStatus
from shapez2_factory.interfaces.cli.asteroid_solve import ExitCode, main


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


def test_validate_artifact_rejects_tampered_file(tmp_path: Path) -> None:
    final = _build_valid_artifact(tmp_path)
    (final / "outputs" / "a.json").write_bytes(b'{"x":999}')
    assert main(["validate-artifact", "--dir", str(final)]) == ExitCode.VALIDATION_FAILED


def test_validate_artifact_rejects_missing_payload_file(tmp_path: Path) -> None:
    final = _build_valid_artifact(tmp_path)
    (final / "outputs" / "a.json").unlink()
    assert main(["validate-artifact", "--dir", str(final)]) == ExitCode.VALIDATION_FAILED


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


def test_run_subcommand_returns_stack_unavailable(tmp_path: Path) -> None:
    assert (
        main(["run", "--artifact-root", str(tmp_path), "--run-key", "run-1"])
        == ExitCode.STACK_UNAVAILABLE
    )


def test_run_subcommand_rejects_unsafe_run_key(tmp_path: Path) -> None:
    assert (
        main(["run", "--artifact-root", str(tmp_path), "--run-key", "../evil"])
        == ExitCode.VALIDATION_FAILED
    )
