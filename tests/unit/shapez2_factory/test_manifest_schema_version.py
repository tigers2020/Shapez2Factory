"""PR-CLI-3a Guard A — fail-closed manifest schema-version parse (BA-1)."""

from __future__ import annotations

import json

import pytest

from shapez2_factory.adapters.asteroid_lab.artifact_manifest import (
    MANIFEST_SCHEMA_VERSION,
    ArtifactManifest,
    ManifestSchemaVersionError,
    parse_manifest_checked,
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


def test_parse_manifest_checked_accepts_supported_version() -> None:
    text = _sample_manifest().to_json()
    restored = parse_manifest_checked(text)
    assert isinstance(restored, ArtifactManifest)
    assert restored.run_key == "run_abc"


def test_manifest_rejects_unknown_schema_version() -> None:
    payload = _sample_manifest().to_json_dict()
    payload["schema_version"] = 999
    text = json.dumps(payload)
    with pytest.raises(ManifestSchemaVersionError) as exc_info:
        parse_manifest_checked(text)
    message = str(exc_info.value)
    assert "1" in message
    assert "999" in message


def test_parse_manifest_checked_rejects_missing_schema_version() -> None:
    payload = _sample_manifest().to_json_dict()
    del payload["schema_version"]
    text = json.dumps(payload)
    with pytest.raises(ManifestSchemaVersionError):
        parse_manifest_checked(text)


def test_parse_manifest_checked_rejects_non_int_schema_version() -> None:
    payload = _sample_manifest().to_json_dict()
    payload["schema_version"] = "abc"
    text = json.dumps(payload)
    with pytest.raises(ManifestSchemaVersionError):
        parse_manifest_checked(text)
