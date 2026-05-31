"""PR-CLI-1 Step 3 ??writer-level collision policy + content_hashes excludes manifest."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from shapez2_factory.adapters.asteroid_lab.artifact_manifest import (
    MANIFEST_SCHEMA_VERSION,
    ArtifactManifest,
)
from shapez2_factory.adapters.asteroid_lab.artifact_writer import (
    ArtifactExistsError,
    AtomicArtifactWriter,
    StagingExistsError,
)
from shapez2_factory.adapters.asteroid_lab.run_status import RunLifecycleStatus

_REPLAY = "output/replay_core.jsonl"


def _draft_manifest(run_key: str) -> ArtifactManifest:
    return ArtifactManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        run_key=run_key,
        lifecycle_status=RunLifecycleStatus.ARTIFACT_WRITING,
        created_at_utc="2026-05-30T14:00:00Z",
        core_build_id="core-0.1.0",
        content_hashes={},
        paths={"replay_core": _REPLAY},
        game_data_provenance={},
        error_code=None,
    )


def _write_one(writer: AtomicArtifactWriter, data: bytes = b"x\n") -> Path:
    writer.open_staging()
    writer.write_output(_REPLAY, data)
    return writer.finalize(_draft_manifest(writer.run_key))


def test_artifact_writer_rejects_existing_dir(tmp_path: Path) -> None:
    (tmp_path / "run1").mkdir(parents=True)
    writer = AtomicArtifactWriter(tmp_path, "run1")
    writer.open_staging()
    writer.write_output(_REPLAY, b"x\n")
    with pytest.raises(ArtifactExistsError):
        writer.finalize(_draft_manifest("run1"))


def test_artifact_writer_replace_existing_dir(tmp_path: Path) -> None:
    _write_one(AtomicArtifactWriter(tmp_path, "run1"), b"old\n")
    _write_one(AtomicArtifactWriter(tmp_path, "run1", replace_existing=True), b"new\n")
    assert (tmp_path / "run1" / _REPLAY).read_bytes() == b"new\n"


def test_artifact_writer_rejects_existing_staging(tmp_path: Path) -> None:
    (tmp_path / ".tmp" / "run1").mkdir(parents=True)
    writer = AtomicArtifactWriter(tmp_path, "run1")
    with pytest.raises(StagingExistsError):
        writer.open_staging()


def test_artifact_writer_replace_existing_staging(tmp_path: Path) -> None:
    stale = tmp_path / ".tmp" / "run1"
    stale.mkdir(parents=True)
    (stale / "leftover.txt").write_text("stale", encoding="utf-8")
    writer = AtomicArtifactWriter(tmp_path, "run1", replace_existing=True)
    _write_one(writer)
    assert (tmp_path / "run1" / _REPLAY).is_file()
    assert not (tmp_path / "run1" / "leftover.txt").exists()


def test_content_hashes_excludes_manifest(tmp_path: Path) -> None:
    final = _write_one(AtomicArtifactWriter(tmp_path, "run1"))
    data = json.loads((final / "manifest.json").read_text(encoding="utf-8"))
    assert "manifest.json" not in data["content_hashes"]
    assert _REPLAY in data["content_hashes"]
