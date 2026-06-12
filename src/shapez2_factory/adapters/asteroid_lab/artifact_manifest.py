"""``ArtifactManifest`` DTO + (de)serialization (spec §2 manifest.json schema).

``content_hashes`` maps artifact-relative payload paths to sha256 hex and **excludes**
``manifest.json`` itself (the manifest is written last and cannot hash itself).
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field

from shapez2_factory.adapters.asteroid_lab.run_status import RunLifecycleStatus

MANIFEST_SCHEMA_VERSION = 1
MANIFEST_FILENAME = "manifest.json"


@dataclass(frozen=True, slots=True)
class ArtifactManifest:
    schema_version: int
    run_key: str
    lifecycle_status: RunLifecycleStatus
    created_at_utc: str
    core_build_id: str
    content_hashes: dict[str, str] = field(default_factory=dict)
    paths: dict[str, str] = field(default_factory=dict)
    game_data_provenance: dict[str, object] = field(default_factory=dict)
    error_code: str | None = None

    def to_json_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "run_key": self.run_key,
            "lifecycle_status": self.lifecycle_status.value,
            "created_at_utc": self.created_at_utc,
            "core_build_id": self.core_build_id,
            "content_hashes": dict(self.content_hashes),
            "paths": dict(self.paths),
            "game_data_provenance": dict(self.game_data_provenance),
            "error_code": self.error_code,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_json_dict(), indent=2, sort_keys=True, ensure_ascii=False)

    @classmethod
    def from_json_dict(cls, payload: dict[str, object]) -> ArtifactManifest:
        return cls(
            schema_version=int(payload["schema_version"]),
            run_key=str(payload["run_key"]),
            lifecycle_status=RunLifecycleStatus(payload["lifecycle_status"]),
            created_at_utc=str(payload["created_at_utc"]),
            core_build_id=str(payload["core_build_id"]),
            content_hashes=dict(payload.get("content_hashes", {})),
            paths=dict(payload.get("paths", {})),
            game_data_provenance=dict(payload.get("game_data_provenance", {})),
            error_code=payload.get("error_code"),
        )

    @classmethod
    def from_json(cls, text: str) -> ArtifactManifest:
        parsed: dict[str, object] = json.loads(text)
        return cls.from_json_dict(parsed)


class ManifestSchemaVersionError(Exception):
    """Raised when a manifest declares an unsupported ``schema_version``."""


def parse_manifest_checked(text: str) -> ArtifactManifest:
    """Parse a manifest JSON string, rejecting unsupported schema versions.

    Schema version is fail-closed (BA-1/Guard A): an unknown ``schema_version``
    must be rejected rather than best-effort parsed, to avoid silently
    misreading a future/foreign manifest. Unlike :meth:`ArtifactManifest.from_json`,
    a missing or non-int-coercible ``schema_version`` also raises
    :class:`ManifestSchemaVersionError`.

    Genuinely malformed JSON propagates as :class:`json.JSONDecodeError`; a
    well-formed but non-object top-level (e.g. a list or number) is rejected.
    """
    payload: object = json.loads(text)
    if not isinstance(payload, dict):
        raise ManifestSchemaVersionError(
            f"manifest top-level is not a JSON object (got {type(payload).__name__}); "
            f"supported version is {MANIFEST_SCHEMA_VERSION}"
        )
    try:
        schema_version = int(payload["schema_version"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ManifestSchemaVersionError(
            f"manifest schema_version is missing or invalid; "
            f"supported version is {MANIFEST_SCHEMA_VERSION}"
        ) from exc
    if schema_version != MANIFEST_SCHEMA_VERSION:
        raise ManifestSchemaVersionError(
            f"unsupported manifest schema_version {schema_version}; "
            f"supported version is {MANIFEST_SCHEMA_VERSION}"
        )
    return ArtifactManifest.from_json_dict(payload)


__all__ = [
    "MANIFEST_FILENAME",
    "MANIFEST_SCHEMA_VERSION",
    "ArtifactManifest",
    "ManifestSchemaVersionError",
    "parse_manifest_checked",
]
