"""PR-CLI-2b ??L2 capacity from a frozen snapshot (no DB) + fail-closed adapter contract."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

import pytest

from shapez2_factory.adapters.asteroid_lab.json_snapshot_rules import (
    GameDataSnapshotInvalid,
    GameDataSnapshotIssue,
    JsonSnapshotGameDataRulesAdapter,
)

_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "asteroid_lab"
    / "game_data_snapshot_min.json"
)

_VALID_PAYLOAD = {
    "schema_version": "game_data_snapshot_v1",
    "game_data_dump_hash": "sha256:abc",
    "exterior_transport_capacity": [
        {"resource_kind": "shape", "speed_tier": 1, "per_connector_capacity_per_min": "5760"},
    ],
    "mining_extraction_rules": [
        {
            "resource_kind": "shape",
            "mini_unit_output_per_min": "30.0000",
            "output_unit": "shapes_per_min",
            "max_extension_count": 3,
            "source_kind": "CANON_MANUAL",
        },
    ],
}


def test_adapter_reads_shape_capacity_from_fixture() -> None:
    adapter = JsonSnapshotGameDataRulesAdapter.from_file(_FIXTURE)

    row = adapter.exterior_connector_capacity(resource_kind="shape", speed_tier=1)

    assert row.resource_kind == "shape"
    assert row.speed_tier == 1
    assert row.per_connector_capacity_per_min == Decimal("5760")


def test_adapter_reads_fluid_capacity_from_fixture() -> None:
    adapter = JsonSnapshotGameDataRulesAdapter.from_file(_FIXTURE)

    row = adapter.exterior_connector_capacity(resource_kind="fluid", speed_tier=1)

    assert row.per_connector_capacity_per_min == Decimal("7200")


def test_resolve_per_connector_capacity_uses_injected_port() -> None:
    from shapez2_factory.application.asteroid_lab.layers.layer_02_exterior_transport import (
        capacity,
    )

    adapter = JsonSnapshotGameDataRulesAdapter.from_file(_FIXTURE)

    got = capacity.resolve_per_connector_capacity(
        rules=adapter,
        resource_kind="shape",
        speed_tier=1,
    )

    assert got.shortfall_reason is None
    assert got.capacity_per_min == Decimal("5760")


def test_missing_row_raises_lookup_error() -> None:
    adapter = JsonSnapshotGameDataRulesAdapter.from_payload(_VALID_PAYLOAD)

    with pytest.raises(LookupError):
        adapter.exterior_connector_capacity(resource_kind="shape", speed_tier=99)


def test_missing_file_is_fail_closed() -> None:
    with pytest.raises(GameDataSnapshotInvalid) as exc:
        JsonSnapshotGameDataRulesAdapter.from_file(_FIXTURE.parent / "does_not_exist.json")

    assert exc.value.issue is GameDataSnapshotIssue.MISSING


def test_unsupported_schema_is_fail_closed() -> None:
    payload = {**_VALID_PAYLOAD, "schema_version": "game_data_snapshot_v999"}

    with pytest.raises(GameDataSnapshotInvalid) as exc:
        JsonSnapshotGameDataRulesAdapter.from_payload(payload)

    assert exc.value.issue is GameDataSnapshotIssue.UNSUPPORTED_SCHEMA


def test_hash_mismatch_is_fail_closed() -> None:
    with pytest.raises(GameDataSnapshotInvalid) as exc:
        JsonSnapshotGameDataRulesAdapter.from_payload(_VALID_PAYLOAD, expected_hash="sha256:other")

    assert exc.value.issue is GameDataSnapshotIssue.HASH_MISMATCH


def test_hash_match_accepts_payload() -> None:
    adapter = JsonSnapshotGameDataRulesAdapter.from_payload(
        _VALID_PAYLOAD,
        expected_hash="sha256:abc",
    )

    row = adapter.exterior_connector_capacity(resource_kind="shape", speed_tier=1)
    assert row.per_connector_capacity_per_min == Decimal("5760")


def test_adapter_reads_shape_mining_rule_from_fixture() -> None:
    adapter = JsonSnapshotGameDataRulesAdapter.from_file(_FIXTURE)

    row = adapter.mining_extraction_rule(resource_kind="shape")

    assert row.mini_unit_output_per_min == Decimal("30")
    assert row.output_unit == "shapes_per_min"
    assert row.max_extension_count == 3


def test_malformed_mining_row_is_fail_closed() -> None:
    payload = {
        "schema_version": "game_data_snapshot_v1",
        "exterior_transport_capacity": [
            {"resource_kind": "shape", "speed_tier": 1, "per_connector_capacity_per_min": "5760"},
        ],
        "mining_extraction_rules": [{"resource_kind": "shape"}],
    }

    with pytest.raises(GameDataSnapshotInvalid) as exc:
        JsonSnapshotGameDataRulesAdapter.from_payload(payload)

    assert exc.value.issue is GameDataSnapshotIssue.MALFORMED


def test_malformed_capacity_row_is_fail_closed() -> None:
    payload = {
        "schema_version": "game_data_snapshot_v1",
        "exterior_transport_capacity": [{"resource_kind": "shape"}],
    }

    with pytest.raises(GameDataSnapshotInvalid) as exc:
        JsonSnapshotGameDataRulesAdapter.from_payload(payload)

    assert exc.value.issue is GameDataSnapshotIssue.MALFORMED
