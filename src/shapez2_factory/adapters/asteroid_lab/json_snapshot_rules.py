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
from shapez2_factory.domain.asteroid_lab.mining_extraction_row import MiningExtractionRow

SUPPORTED_SCHEMA_VERSIONS = frozenset({"game_data_snapshot_v1"})
CAPACITY_KEY = "exterior_transport_capacity"
MINING_KEY = "mining_extraction_rules"


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
    def __init__(
        self,
        capacities: dict[tuple[str, int], Decimal],
        mining_rules: dict[str, MiningExtractionRow],
    ) -> None:
        self._capacities = dict(capacities)
        self._mining_rules = dict(mining_rules)

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
        mining_rules = _parse_mining_rows(payload.get(MINING_KEY))
        return cls(capacities, mining_rules)

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

    def mining_extraction_rule(self, *, resource_kind: str) -> MiningExtractionRow:
        row = self._mining_rules.get(resource_kind)
        if row is None:
            msg = f"no mining extraction rule for resource_kind={resource_kind!r}"
            raise LookupError(msg)
        return row


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


def _parse_mining_rows(rows: object) -> dict[str, MiningExtractionRow]:
    if not isinstance(rows, list):
        raise GameDataSnapshotInvalid(
            GameDataSnapshotIssue.MALFORMED,
            f"{MINING_KEY} must be a list",
        )
    rules: dict[str, MiningExtractionRow] = {}
    for row in rows:
        if not isinstance(row, dict):
            raise GameDataSnapshotInvalid(
                GameDataSnapshotIssue.MALFORMED,
                f"{MINING_KEY} row must be an object",
            )
        try:
            resource_kind = str(row["resource_kind"])
            mini_unit_output = Decimal(str(row["mini_unit_output_per_min"]))
            output_unit = str(row["output_unit"])
            max_extension_count = int(row["max_extension_count"])
            source_kind = str(row.get("source_kind", "CANON_MANUAL"))
        except (KeyError, TypeError, ValueError, InvalidOperation) as exc:
            raise GameDataSnapshotInvalid(
                GameDataSnapshotIssue.MALFORMED,
                f"invalid mining row {row!r}: {exc}",
            ) from exc
        rules[resource_kind] = MiningExtractionRow(
            resource_kind=resource_kind,
            mini_unit_output_per_min=mini_unit_output,
            output_unit=output_unit,
            max_extension_count=max_extension_count,
            source_kind=source_kind,
        )
    return rules


__all__ = [
    "CAPACITY_KEY",
    "MINING_KEY",
    "SUPPORTED_SCHEMA_VERSIONS",
    "GameDataSnapshotInvalid",
    "GameDataSnapshotIssue",
    "JsonSnapshotGameDataRulesAdapter",
]
