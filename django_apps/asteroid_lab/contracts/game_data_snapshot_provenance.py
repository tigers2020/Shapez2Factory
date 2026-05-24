"""Frozen provenance for game_data snapshot builds (metadata only — not algorithm input)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    RULE_VERSION,
    SCHEMA_VERSION,
    AsteroidGameDataSnapshot,
)

_REQUIRED_KEYS = frozenset(
    {
        "snapshot_schema_version",
        "rule_version",
        "data_revision",
        "import_batch_id",
        "content_hash",
        "game_version",
        "db_alias",
        "built_at_utc",
    }
)

_CONTENT_HASH_HEX_RE = re.compile(r"^[0-9a-f]{64}$")


class ProvenanceParseErrorCode(StrEnum):
    UNKNOWN_KEY = "unknown_key"
    MISSING_FIELD = "missing_field"
    INVALID_TYPE = "invalid_type"
    INVALID_VALUE = "invalid_value"


class ProvenanceParseError(ValueError):
    def __init__(self, code: ProvenanceParseErrorCode, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class GameDataSnapshotProvenance:
    snapshot_schema_version: str
    rule_version: str
    data_revision: str
    import_batch_id: int
    content_hash: str
    game_version: str
    db_alias: str
    built_at_utc: str

    def reproducibility_key(self) -> tuple[int, str, str]:
        """Reproducibility key — ``built_at_utc`` MUST NOT participate."""
        return (
            self.import_batch_id,
            self.snapshot_schema_version,
            self.content_hash,
        )


def provenance_from_snapshot(
    snapshot: AsteroidGameDataSnapshot,
    *,
    import_batch_id: int,
) -> GameDataSnapshotProvenance:
    meta = snapshot.meta
    return GameDataSnapshotProvenance(
        snapshot_schema_version=meta.schema_version,
        rule_version=meta.rule_version,
        data_revision=meta.data_revision,
        import_batch_id=int(import_batch_id),
        content_hash=meta.content_hash,
        game_version=meta.game_version,
        db_alias=meta.db_alias,
        built_at_utc=meta.built_at_utc,
    )


def provenance_to_config_dict(provenance: GameDataSnapshotProvenance) -> dict[str, str]:
    return {
        "snapshot_schema_version": provenance.snapshot_schema_version,
        "rule_version": provenance.rule_version,
        "data_revision": provenance.data_revision,
        "import_batch_id": str(provenance.import_batch_id),
        "content_hash": provenance.content_hash,
        "game_version": provenance.game_version,
        "db_alias": provenance.db_alias,
        "built_at_utc": provenance.built_at_utc,
    }


def provenance_stub_diagnostic_dict(provenance: GameDataSnapshotProvenance) -> dict[str, str]:
    """Slim deploy diagnostic for P1 RTTP-off responses (not full provenance wire)."""
    batch_id, schema_version, content_hash = provenance.reproducibility_key()
    return {
        "snapshot_schema_version": schema_version,
        "import_batch_id": str(batch_id),
        "content_hash": content_hash,
        "data_revision": provenance.data_revision,
    }


def _validate_parsed_provenance(provenance: GameDataSnapshotProvenance) -> None:
    if provenance.import_batch_id <= 0:
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.INVALID_VALUE,
            "import_batch_id must be positive",
        )
    if not _CONTENT_HASH_HEX_RE.match(provenance.content_hash):
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.INVALID_VALUE,
            "content_hash must be 64 lowercase hex characters",
        )
    if provenance.snapshot_schema_version != SCHEMA_VERSION:
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.INVALID_VALUE,
            f"snapshot_schema_version must be {SCHEMA_VERSION!r}",
        )
    if provenance.rule_version != RULE_VERSION:
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.INVALID_VALUE,
            f"rule_version must be {RULE_VERSION!r}",
        )
    if not provenance.data_revision.strip():
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.INVALID_VALUE,
            "data_revision must be non-empty",
        )
    if not provenance.game_version.strip():
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.INVALID_VALUE,
            "game_version must be non-empty",
        )


def parse_provenance_config(payload: object) -> GameDataSnapshotProvenance:
    if not isinstance(payload, dict):
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.INVALID_TYPE,
            "provenance payload must be dict",
        )
    unknown = set(payload) - _REQUIRED_KEYS
    if unknown:
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.UNKNOWN_KEY,
            f"unknown provenance keys: {sorted(unknown)}",
        )
    missing = _REQUIRED_KEYS - set(payload)
    if missing:
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.MISSING_FIELD,
            f"missing provenance keys: {sorted(missing)}",
        )
    try:
        batch_id = int(str(payload["import_batch_id"]))
    except (TypeError, ValueError) as exc:
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.INVALID_TYPE,
            "import_batch_id must be int-like string",
        ) from exc
    provenance = GameDataSnapshotProvenance(
        snapshot_schema_version=str(payload["snapshot_schema_version"]),
        rule_version=str(payload["rule_version"]),
        data_revision=str(payload["data_revision"]),
        import_batch_id=batch_id,
        content_hash=str(payload["content_hash"]),
        game_version=str(payload["game_version"]),
        db_alias=str(payload["db_alias"]),
        built_at_utc=str(payload["built_at_utc"]),
    )
    _validate_parsed_provenance(provenance)
    return provenance


__all__ = [
    "GameDataSnapshotProvenance",
    "ProvenanceParseError",
    "ProvenanceParseErrorCode",
    "parse_provenance_config",
    "provenance_from_snapshot",
    "provenance_stub_diagnostic_dict",
    "provenance_to_config_dict",
]
