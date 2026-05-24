"""Frozen provenance for game_data snapshot builds (metadata only — not algorithm input)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum

from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    SLICE_VERSION,
    BuildingCatalogSlice,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice_hash import (
    catalog_slice_hash,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    RULE_VERSION,
    SCHEMA_VERSION,
    AsteroidGameDataSnapshot,
)

_REQUIRED_KEYS_V1 = frozenset(
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

_REQUIRED_KEYS_V2 = _REQUIRED_KEYS_V1 | frozenset(
    {
        "catalog_slice_version",
        "catalog_slice_hash",
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
    catalog_slice_version: str
    catalog_slice_hash: str

    def reproducibility_key_v1(self) -> tuple[int, str, str]:
        """Track A reproducibility key (3-tuple). ``built_at_utc`` excluded."""

        return (
            self.import_batch_id,
            self.snapshot_schema_version,
            self.content_hash,
        )

    def reproducibility_key(self) -> tuple[int, str, str, str, str]:
        """Track B2 reproducibility key (5-tuple). ``built_at_utc`` excluded."""

        return (
            self.import_batch_id,
            self.snapshot_schema_version,
            self.content_hash,
            self.catalog_slice_version,
            self.catalog_slice_hash,
        )


def provenance_from_snapshot(
    snapshot: AsteroidGameDataSnapshot,
    *,
    import_batch_id: int,
    catalog_slice: BuildingCatalogSlice,
) -> GameDataSnapshotProvenance:
    meta = snapshot.meta
    slice_hash = catalog_slice_hash(catalog_slice)
    if catalog_slice.slice_version != SLICE_VERSION:
        msg = f"catalog_slice.slice_version must be {SLICE_VERSION!r}"
        raise ValueError(msg)
    return GameDataSnapshotProvenance(
        snapshot_schema_version=meta.schema_version,
        rule_version=meta.rule_version,
        data_revision=meta.data_revision,
        import_batch_id=int(import_batch_id),
        content_hash=meta.content_hash,
        game_version=meta.game_version,
        db_alias=meta.db_alias,
        built_at_utc=meta.built_at_utc,
        catalog_slice_version=catalog_slice.slice_version,
        catalog_slice_hash=slice_hash,
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
        "catalog_slice_version": provenance.catalog_slice_version,
        "catalog_slice_hash": provenance.catalog_slice_hash,
    }


def provenance_stub_diagnostic_dict(provenance: GameDataSnapshotProvenance) -> dict[str, str]:
    """Slim deploy diagnostic for P1 RTTP-off responses (not full provenance wire)."""
    batch_id, schema_version, content_hash = provenance.reproducibility_key_v1()
    return {
        "snapshot_schema_version": schema_version,
        "import_batch_id": str(batch_id),
        "content_hash": content_hash,
        "data_revision": provenance.data_revision,
        "catalog_slice_hash": provenance.catalog_slice_hash,
    }


def _validate_parsed_provenance_base(provenance: GameDataSnapshotProvenance) -> None:
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


def _validate_parsed_provenance_v2(provenance: GameDataSnapshotProvenance) -> None:
    _validate_parsed_provenance_base(provenance)
    if provenance.catalog_slice_version != SLICE_VERSION:
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.INVALID_VALUE,
            f"catalog_slice_version must be {SLICE_VERSION!r}",
        )
    if not _CONTENT_HASH_HEX_RE.match(provenance.catalog_slice_hash):
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.INVALID_VALUE,
            "catalog_slice_hash must be 64 lowercase hex characters",
        )


def _parse_provenance_payload(
    payload: dict[str, object],
    *,
    required_keys: frozenset[str],
) -> GameDataSnapshotProvenance:
    unknown = set(payload) - required_keys
    if unknown:
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.UNKNOWN_KEY,
            f"unknown provenance keys: {sorted(unknown)}",
        )
    missing = required_keys - set(payload)
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
    catalog_version = (
        str(payload["catalog_slice_version"]) if "catalog_slice_version" in required_keys else ""
    )
    catalog_hash = (
        str(payload["catalog_slice_hash"]) if "catalog_slice_hash" in required_keys else ""
    )
    return GameDataSnapshotProvenance(
        snapshot_schema_version=str(payload["snapshot_schema_version"]),
        rule_version=str(payload["rule_version"]),
        data_revision=str(payload["data_revision"]),
        import_batch_id=batch_id,
        content_hash=str(payload["content_hash"]),
        game_version=str(payload["game_version"]),
        db_alias=str(payload["db_alias"]),
        built_at_utc=str(payload["built_at_utc"]),
        catalog_slice_version=catalog_version,
        catalog_slice_hash=catalog_hash,
    )


def parse_provenance_config_v1(payload: object) -> GameDataSnapshotProvenance:
    """Historical Track A wire (8 keys). Read-only for pre-B2 ``SolverRun`` rows."""

    if not isinstance(payload, dict):
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.INVALID_TYPE,
            "provenance payload must be dict",
        )
    provenance = _parse_provenance_payload(payload, required_keys=_REQUIRED_KEYS_V1)
    _validate_parsed_provenance_base(provenance)
    return provenance


def parse_provenance_config(payload: object) -> GameDataSnapshotProvenance:
    """Latest strict parser — Track B2 provenance v2 (10 keys). RTTP persist/readback."""

    if not isinstance(payload, dict):
        raise ProvenanceParseError(
            ProvenanceParseErrorCode.INVALID_TYPE,
            "provenance payload must be dict",
        )
    provenance = _parse_provenance_payload(payload, required_keys=_REQUIRED_KEYS_V2)
    _validate_parsed_provenance_v2(provenance)
    return provenance


def parse_provenance_config_latest(payload: object) -> GameDataSnapshotProvenance:
    """Alias for ``parse_provenance_config`` (v2 strict)."""

    return parse_provenance_config(payload)


__all__ = [
    "GameDataSnapshotProvenance",
    "ProvenanceParseError",
    "ProvenanceParseErrorCode",
    "parse_provenance_config",
    "parse_provenance_config_latest",
    "parse_provenance_config_v1",
    "provenance_from_snapshot",
    "provenance_stub_diagnostic_dict",
    "provenance_to_config_dict",
]
