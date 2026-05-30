"""``JsonSnapshotGameDataRulesAdapter`` — core game-data rules from a frozen snapshot (BA-8).

Reads a ``game_data_snapshot`` payload (file or dict) and answers ``GameDataRulesPort`` queries from
the carried resolver output. Fail-closed: missing file / unsupported ``schema_version`` / hash
mismatch / malformed payload raise ``GameDataSnapshotInvalid`` with a typed
``GameDataSnapshotIssue``. A valid snapshot that simply lacks a requested
``(resource_kind, speed_tier)`` row raises ``LookupError`` (the L2 caller maps it to
``MISSING_EVTC_ROW``).
"""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path

from shapez2_factory.domain.asteroid_lab.exterior_capacity_row import ExteriorCapacityRow

SUPPORTED_SCHEMA_VERSIONS = frozenset({"game_data_snapshot_v1"})
CAPACITY_KEY = "exterior_transport_capacity"


class GameDataSnapshotIssue(StrEnum):
    MISSING = "missing"
    UNSUPPORTED_SCHEMA = "unsupported_schema"
    HASH_MISMATCH = "hash_mismatch"
    MALFORMED = "malformed"


class GameDataSnapshotInvalid(Exception):
    def __init__(self, issue: GameDataSnapshotIssue, message: str) -> None:
        self.issue = issue
        super().__init__(f"{issue.value}: {message}")


class JsonSnapshotGameDataRulesAdapter:
    def __init__(self, capacities: dict[tuple[str, int], Decimal]) -> None:
        self._capacities = dict(capacities)

    @classmethod
    def from_payload(
        cls,
        payload: object,
        *,
        expected_hash: str | None = None,
    ) -> JsonSnapshotGameDataRulesAdapter:
        if not isinstance(payload, dict):
            raise GameDataSnapshotInvalid(
                GameDataSnapshotIssue.MALFORMED,
                "snapshot payload must be a JSON object",
            )
        schema_version = payload.get("schema_version")
        if schema_version not in SUPPORTED_SCHEMA_VERSIONS:
            raise GameDataSnapshotInvalid(
                GameDataSnapshotIssue.UNSUPPORTED_SCHEMA,
                f"schema_version {schema_version!r} not in {sorted(SUPPORTED_SCHEMA_VERSIONS)}",
            )
        if expected_hash is not None and payload.get("game_data_dump_hash") != expected_hash:
            raise GameDataSnapshotInvalid(
                GameDataSnapshotIssue.HASH_MISMATCH,
                f"game_data_dump_hash {payload.get('game_data_dump_hash')!r} != {expected_hash!r}",
            )
        capacities = _parse_capacity_rows(payload.get(CAPACITY_KEY))
        return cls(capacities)

    @classmethod
    def from_file(
        cls,
        path: str | Path,
        *,
        expected_hash: str | None = None,
    ) -> JsonSnapshotGameDataRulesAdapter:
        file_path = Path(path)
        if not file_path.is_file():
            raise GameDataSnapshotInvalid(
                GameDataSnapshotIssue.MISSING,
                f"snapshot file not found: {file_path}",
            )
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise GameDataSnapshotInvalid(
                GameDataSnapshotIssue.MALFORMED,
                f"invalid JSON in {file_path}: {exc}",
            ) from exc
        return cls.from_payload(payload, expected_hash=expected_hash)

    def exterior_connector_capacity(
        self,
        *,
        resource_kind: str,
        speed_tier: int,
    ) -> ExteriorCapacityRow:
        capacity = self._capacities.get((resource_kind, speed_tier))
        if capacity is None:
            msg = f"no capacity row for resource_kind={resource_kind!r} speed_tier={speed_tier!r}"
            raise LookupError(msg)
        return ExteriorCapacityRow(
            resource_kind=resource_kind,
            speed_tier=speed_tier,
            per_connector_capacity_per_min=capacity,
        )


def _parse_capacity_rows(rows: object) -> dict[tuple[str, int], Decimal]:
    if not isinstance(rows, list):
        raise GameDataSnapshotInvalid(
            GameDataSnapshotIssue.MALFORMED,
            f"{CAPACITY_KEY} must be a list",
        )
    capacities: dict[tuple[str, int], Decimal] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise GameDataSnapshotInvalid(
                GameDataSnapshotIssue.MALFORMED,
                f"{CAPACITY_KEY} row must be an object",
            )
        try:
            resource_kind = str(row["resource_kind"])
            speed_tier = int(row["speed_tier"])
            capacity = Decimal(str(row["per_connector_capacity_per_min"]))
        except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
            raise GameDataSnapshotInvalid(
                GameDataSnapshotIssue.MALFORMED,
                f"invalid capacity row {row!r}: {exc}",
            ) from exc
        capacities[(resource_kind, speed_tier)] = capacity
    return capacities


__all__ = [
    "CAPACITY_KEY",
    "SUPPORTED_SCHEMA_VERSIONS",
    "GameDataSnapshotInvalid",
    "GameDataSnapshotIssue",
    "JsonSnapshotGameDataRulesAdapter",
]
