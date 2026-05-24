from __future__ import annotations

import pytest

from django_apps.asteroid_lab.contracts.building_catalog_slice import (
    SLICE_VERSION,
    catalog_slice_from_snapshot,
)
from django_apps.asteroid_lab.contracts.building_catalog_slice_hash import (
    catalog_slice_hash,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    RULE_VERSION,
    SCHEMA_VERSION,
    AsteroidGameDataSnapshot,
    BuildingSnapshot,
    TransportRegistryEntry,
    build_snapshot_meta,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot_provenance import (
    GameDataSnapshotProvenance,
    ProvenanceParseError,
    ProvenanceParseErrorCode,
    parse_provenance_config,
    parse_provenance_config_v1,
    provenance_from_snapshot,
    provenance_stub_diagnostic_dict,
    provenance_to_config_dict,
)


def _minimal_snapshot(*, content_hash: str = "a" * 64) -> AsteroidGameDataSnapshot:
    meta = build_snapshot_meta(
        data_revision="rev-hash-001",
        db_alias="default",
        built_at_utc="2026-05-24T00:00:00Z",
        content_hash=content_hash,
        game_version="9.9.9",
    )
    return AsteroidGameDataSnapshot(
        meta=meta,
        buildings=(
            BuildingSnapshot(
                canonical_id="bv:test",
                internal_name="test",
                footprint_cells=(),
                connectors=(),
            ),
        ),
        transport_registry=(
            TransportRegistryEntry("space_belt", "belt", "bv:test"),
        ),
    )


def _provenance_for_snapshot(
    snap: AsteroidGameDataSnapshot,
    *,
    import_batch_id: int = 1,
) -> GameDataSnapshotProvenance:
    catalog_slice = catalog_slice_from_snapshot(snap)
    return provenance_from_snapshot(
        snap,
        import_batch_id=import_batch_id,
        catalog_slice=catalog_slice,
    )


def test_provenance_from_snapshot_maps_all_fields() -> None:
    snap = _minimal_snapshot()
    catalog_slice = catalog_slice_from_snapshot(snap)
    prov = provenance_from_snapshot(
        snap, import_batch_id=99, catalog_slice=catalog_slice
    )
    assert prov.snapshot_schema_version == SCHEMA_VERSION
    assert prov.rule_version == RULE_VERSION
    assert prov.data_revision == "rev-hash-001"
    assert prov.import_batch_id == 99
    assert prov.content_hash == snap.meta.content_hash
    assert prov.game_version == "9.9.9"
    assert prov.db_alias == "default"
    assert prov.built_at_utc == "2026-05-24T00:00:00Z"
    assert prov.catalog_slice_version == SLICE_VERSION
    assert prov.catalog_slice_hash == catalog_slice_hash(catalog_slice)


def test_reproducibility_key_v1_excludes_built_at_utc() -> None:
    snap = _minimal_snapshot()
    a = _provenance_for_snapshot(snap)
    b = GameDataSnapshotProvenance(
        snapshot_schema_version=a.snapshot_schema_version,
        rule_version=a.rule_version,
        data_revision=a.data_revision,
        import_batch_id=a.import_batch_id,
        content_hash=a.content_hash,
        game_version=a.game_version,
        db_alias=a.db_alias,
        built_at_utc="2026-05-25T99:99:99Z",
        catalog_slice_version=a.catalog_slice_version,
        catalog_slice_hash=a.catalog_slice_hash,
    )
    assert a.reproducibility_key_v1() == b.reproducibility_key_v1()


def test_reproducibility_key_b2_includes_catalog_fields() -> None:
    snap = _minimal_snapshot()
    prov = _provenance_for_snapshot(snap)
    key = prov.reproducibility_key()
    assert len(key) == 5
    assert key[3] == SLICE_VERSION
    assert key[4] == prov.catalog_slice_hash


def test_parse_provenance_v2_rejects_v1_only_payload() -> None:
    payload = {
        "snapshot_schema_version": SCHEMA_VERSION,
        "rule_version": RULE_VERSION,
        "data_revision": "rev-hash-001",
        "import_batch_id": "1",
        "content_hash": "a" * 64,
        "game_version": "9.9.9",
        "db_alias": "default",
        "built_at_utc": "2026-05-24T00:00:00Z",
    }
    with pytest.raises(ProvenanceParseError) as exc_info:
        parse_provenance_config(payload)
    assert exc_info.value.code == ProvenanceParseErrorCode.MISSING_FIELD


def test_parse_provenance_v1_historical_eight_keys() -> None:
    payload = {
        "snapshot_schema_version": SCHEMA_VERSION,
        "rule_version": RULE_VERSION,
        "data_revision": "rev-hash-001",
        "import_batch_id": "1",
        "content_hash": "a" * 64,
        "game_version": "9.9.9",
        "db_alias": "default",
        "built_at_utc": "2026-05-24T00:00:00Z",
    }
    parsed = parse_provenance_config_v1(payload)
    assert parsed.import_batch_id == 1
    assert parsed.catalog_slice_hash == ""


def test_parse_provenance_rejects_unknown_keys() -> None:
    payload = provenance_to_config_dict(_provenance_for_snapshot(_minimal_snapshot()))
    payload["extra_field"] = "nope"
    with pytest.raises(ProvenanceParseError) as exc_info:
        parse_provenance_config(payload)
    assert exc_info.value.code == ProvenanceParseErrorCode.UNKNOWN_KEY


def test_parse_provenance_rejects_missing_field() -> None:
    payload = provenance_to_config_dict(_provenance_for_snapshot(_minimal_snapshot()))
    del payload["content_hash"]
    with pytest.raises(ProvenanceParseError) as exc_info:
        parse_provenance_config(payload)
    assert exc_info.value.code == ProvenanceParseErrorCode.MISSING_FIELD


def test_parse_provenance_rejects_non_positive_import_batch_id() -> None:
    payload = provenance_to_config_dict(_provenance_for_snapshot(_minimal_snapshot()))
    payload["import_batch_id"] = "0"
    with pytest.raises(ProvenanceParseError) as exc_info:
        parse_provenance_config(payload)
    assert exc_info.value.code == ProvenanceParseErrorCode.INVALID_VALUE


def test_parse_provenance_rejects_bad_content_hash_length() -> None:
    payload = provenance_to_config_dict(_provenance_for_snapshot(_minimal_snapshot()))
    payload["content_hash"] = "abc"
    with pytest.raises(ProvenanceParseError) as exc_info:
        parse_provenance_config(payload)
    assert exc_info.value.code == ProvenanceParseErrorCode.INVALID_VALUE


def test_parse_provenance_rejects_wrong_schema_version() -> None:
    payload = provenance_to_config_dict(_provenance_for_snapshot(_minimal_snapshot()))
    payload["snapshot_schema_version"] = "game_data_snapshot_v0"
    with pytest.raises(ProvenanceParseError) as exc_info:
        parse_provenance_config(payload)
    assert exc_info.value.code == ProvenanceParseErrorCode.INVALID_VALUE


def test_roundtrip_config_dict_v2() -> None:
    prov = _provenance_for_snapshot(_minimal_snapshot(), import_batch_id=7)
    again = parse_provenance_config(provenance_to_config_dict(prov))
    assert again == prov


@pytest.mark.django_db
def test_provenance_data_revision_matches_pinned_import_batch(
    imported_game_data_batch,
) -> None:
    from django_apps.game_data.selectors.import_batch import pin_latest_import_batch
    from django_apps.web.services.asteroid_game_data_snapshot import (
        build_asteroid_game_data_snapshot_with_provenance,
    )

    batch = pin_latest_import_batch(db_alias="default")
    build = build_asteroid_game_data_snapshot_with_provenance(db_alias="default")
    assert build.provenance.import_batch_id == int(batch.pk)
    assert build.provenance.data_revision == batch.manifest_self_hash


def test_stub_diagnostic_dict_uses_reproducibility_key_v1_fields() -> None:
    prov = _provenance_for_snapshot(_minimal_snapshot(), import_batch_id=3)
    diag = provenance_stub_diagnostic_dict(prov)
    assert diag["content_hash"] == prov.content_hash
    assert diag["import_batch_id"] == "3"
    assert diag["snapshot_schema_version"] == SCHEMA_VERSION
    assert diag["catalog_slice_hash"] == prov.catalog_slice_hash
    assert "built_at_utc" not in diag
