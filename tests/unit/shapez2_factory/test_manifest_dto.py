"""PR-CLI-1 Step 1 — ArtifactManifest DTO round-trip (manifest.json schema §2)."""

from __future__ import annotations

import json

from shapez2_factory.adapters.asteroid_lab.artifact_manifest import (
    MANIFEST_SCHEMA_VERSION,
    ArtifactManifest,
)
from shapez2_factory.adapters.asteroid_lab.run_status import RunLifecycleStatus


def _sample_manifest() -> ArtifactManifest:
    return ArtifactManifest(
        schema_version=MANIFEST_SCHEMA_VERSION,
        run_key="run_abc",
        lifecycle_status=RunLifecycleStatus.ARTIFACT_WRITTEN,
        created_at_utc="2026-05-30T14:00:00Z",
        core_build_id="core-0.1.0",
        content_hashes={"output/replay_core.jsonl": "a" * 64},
        paths={"replay_core": "output/replay_core.jsonl"},
        game_data_provenance={"snapshot_schema_version": 1},
        error_code=None,
    )


def test_manifest_round_trip_via_json_dict() -> None:
    manifest = _sample_manifest()
    restored = ArtifactManifest.from_json_dict(manifest.to_json_dict())
    assert restored == manifest


def test_manifest_round_trip_via_json_string() -> None:
    manifest = _sample_manifest()
    restored = ArtifactManifest.from_json(manifest.to_json())
    assert restored == manifest


def test_manifest_json_dict_keys_match_schema() -> None:
    payload = _sample_manifest().to_json_dict()
    assert set(payload) == {
        "schema_version",
        "run_key",
        "lifecycle_status",
        "created_at_utc",
        "core_build_id",
        "content_hashes",
        "paths",
        "game_data_provenance",
        "error_code",
    }
    assert payload["schema_version"] == MANIFEST_SCHEMA_VERSION
    assert payload["lifecycle_status"] == "artifact_written"


def test_manifest_to_json_is_valid_json() -> None:
    text = _sample_manifest().to_json()
    assert json.loads(text)["run_key"] == "run_abc"
