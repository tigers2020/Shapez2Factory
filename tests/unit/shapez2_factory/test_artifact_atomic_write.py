"""PR-CLI-1 Step 2 — AtomicArtifactWriter BA-5 protocol round-trip."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from shapez2_factory.adapters.asteroid_lab.artifact_manifest import (
    MANIFEST_SCHEMA_VERSION,
    ArtifactManifest,
)
from shapez2_factory.adapters.asteroid_lab.artifact_writer import AtomicArtifactWriter
from shapez2_factory.adapters.asteroid_lab.run_status import RunLifecycleStatus

_REPLAY = "output/replay_core.jsonl"
_SUMMARY = "output/solver_summary.json"


def _draft_manifest(run_key: str) -> ArtifactManifest:
    return ArtifactManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        run_key=run_key,
        lifecycle_status=RunLifecycleStatus.ARTIFACT_WRITING,
        created_at_utc="2026-05-30T14:00:00Z",
        core_build_id="core-0.1.0",
        content_hashes={},
        paths={"replay_core": _REPLAY, "solver_summary": _SUMMARY},
        game_data_provenance={},
        error_code=None,
    )


def test_no_final_dir_until_finalize(tmp_path: Path) -> None:
    writer = AtomicArtifactWriter(tmp_path, "run1")
    writer.open_staging()
    writer.write_output(_REPLAY, b'{"frame_index": 0}\n')
    final_dir = tmp_path / "run1"
    assert not final_dir.exists()

    returned = writer.finalize(_draft_manifest("run1"))
    assert returned == final_dir
    assert final_dir.is_dir()


def test_staging_removed_after_finalize(tmp_path: Path) -> None:
    writer = AtomicArtifactWriter(tmp_path, "run1")
    writer.open_staging()
    writer.write_output(_REPLAY, b'{"frame_index": 0}\n')
    writer.finalize(_draft_manifest("run1"))
    assert not (tmp_path / ".tmp" / "run1").exists()


def test_manifest_written_last_with_hashes(tmp_path: Path) -> None:
    payload = b'{"frame_index": 0}\n'
    writer = AtomicArtifactWriter(tmp_path, "run1")
    writer.open_staging()
    writer.write_output(_REPLAY, payload)
    writer.finalize(_draft_manifest("run1"))

    manifest_path = tmp_path / "run1" / "manifest.json"
    assert manifest_path.is_file()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert data["lifecycle_status"] == RunLifecycleStatus.ARTIFACT_WRITTEN.value
    assert data["content_hashes"][_REPLAY] == hashlib.sha256(payload).hexdigest()


def test_hashes_match_written_payload(tmp_path: Path) -> None:
    writer = AtomicArtifactWriter(tmp_path, "run1")
    writer.open_staging()
    writer.write_output(_REPLAY, b"line-a\n")
    writer.write_output(_SUMMARY, b'{"ok": true}')
    writer.finalize(_draft_manifest("run1"))

    final_dir = tmp_path / "run1"
    data = json.loads((final_dir / "manifest.json").read_text(encoding="utf-8"))
    for relpath, digest in data["content_hashes"].items():
        actual = hashlib.sha256((final_dir / relpath).read_bytes()).hexdigest()
        assert actual == digest
