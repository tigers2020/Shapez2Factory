"""Plain JSON artifact manifest reader for Django-side ingest."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path

MANIFEST_FILENAME = "manifest.json"
MANIFEST_SCHEMA_VERSION = 1
ARTIFACT_WRITTEN = "artifact_written"


class ArtifactManifestReadError(Exception):
    """Raised when a finalized artifact manifest is missing or invalid."""


@dataclass(frozen=True, slots=True)
class ArtifactManifestRecord:
    """Django-side manifest DTO that intentionally avoids core imports."""

    schema_version: int
    run_key: str
    lifecycle_status: str
    created_at_utc: str
    core_build_id: str
    content_hashes: dict[str, str] = field(default_factory=dict)
    paths: dict[str, str] = field(default_factory=dict)
    game_data_provenance: dict[str, object] = field(default_factory=dict)
    error_code: str | None = None


def _object_payload(value: object, *, field_name: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ArtifactManifestReadError(f"{field_name} must be an object")
    return dict(value)


def _string_payload(value: object, *, field_name: str) -> str:
    if not isinstance(value, str) or not value:
        raise ArtifactManifestReadError(f"{field_name} must be a non-empty string")
    return value


def parse_artifact_manifest_payload(payload: object) -> ArtifactManifestRecord:
    """Parse manifest payload with fail-closed schema and lifecycle checks."""

    if not isinstance(payload, dict):
        raise ArtifactManifestReadError("manifest top-level must be an object")
    try:
        schema_version = int(payload["schema_version"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ArtifactManifestReadError("manifest schema_version is missing or invalid") from exc
    if schema_version != MANIFEST_SCHEMA_VERSION:
        raise ArtifactManifestReadError(f"unsupported manifest schema_version {schema_version}")

    lifecycle_status = _string_payload(
        payload.get("lifecycle_status"), field_name="lifecycle_status"
    )
    if lifecycle_status != ARTIFACT_WRITTEN:
        raise ArtifactManifestReadError(f"manifest lifecycle_status must be {ARTIFACT_WRITTEN}")

    content_hashes_raw = _object_payload(payload.get("content_hashes"), field_name="content_hashes")
    content_hashes = {
        _string_payload(key, field_name="content_hashes key"): _string_payload(
            value, field_name=f"content_hashes[{key!r}]"
        )
        for key, value in content_hashes_raw.items()
    }
    if MANIFEST_FILENAME in content_hashes:
        raise ArtifactManifestReadError("manifest.json must not be content-hashed")

    return ArtifactManifestRecord(
        schema_version=schema_version,
        run_key=_string_payload(payload.get("run_key"), field_name="run_key"),
        lifecycle_status=lifecycle_status,
        created_at_utc=_string_payload(payload.get("created_at_utc"), field_name="created_at_utc"),
        core_build_id=_string_payload(payload.get("core_build_id"), field_name="core_build_id"),
        content_hashes=content_hashes,
        paths={
            _string_payload(key, field_name="paths key"): _string_payload(
                value, field_name=f"paths[{key!r}]"
            )
            for key, value in _object_payload(payload.get("paths", {}), field_name="paths").items()
        },
        game_data_provenance=_object_payload(
            payload.get("game_data_provenance", {}), field_name="game_data_provenance"
        ),
        error_code=payload.get("error_code") if payload.get("error_code") is not None else None,
    )


def read_artifact_manifest(artifact_dir: Path) -> ArtifactManifestRecord:
    """Read ``manifest.json`` from a finalized artifact directory."""

    path = Path(artifact_dir) / MANIFEST_FILENAME
    if not path.is_file():
        raise ArtifactManifestReadError(f"manifest not found: {path}")
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ArtifactManifestReadError(f"manifest unreadable: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ArtifactManifestReadError(f"manifest malformed: {path}") from exc
    return parse_artifact_manifest_payload(payload)


def verify_manifest_content_hashes(
    artifact_dir: Path,
    manifest: ArtifactManifestRecord,
) -> None:
    """Validate every declared payload hash and reject missing payload files."""

    root = Path(artifact_dir).resolve()
    for relpath, expected_hash in manifest.content_hashes.items():
        payload_path = (root / relpath).resolve()
        try:
            payload_path.relative_to(root)
        except ValueError as exc:
            raise ArtifactManifestReadError(f"manifest path escapes artifact: {relpath}") from exc
        if not payload_path.is_file():
            raise ArtifactManifestReadError(f"manifest payload missing: {relpath}")
        actual_hash = hashlib.sha256(payload_path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            raise ArtifactManifestReadError(f"manifest payload hash mismatch: {relpath}")


def read_verified_artifact_manifest(artifact_dir: Path) -> ArtifactManifestRecord:
    """Read a manifest and verify all declared payload hashes."""

    manifest = read_artifact_manifest(artifact_dir)
    verify_manifest_content_hashes(artifact_dir, manifest)
    return manifest


__all__ = [
    "ARTIFACT_WRITTEN",
    "MANIFEST_FILENAME",
    "MANIFEST_SCHEMA_VERSION",
    "ArtifactManifestReadError",
    "ArtifactManifestRecord",
    "parse_artifact_manifest_payload",
    "read_artifact_manifest",
    "read_verified_artifact_manifest",
    "verify_manifest_content_hashes",
]
