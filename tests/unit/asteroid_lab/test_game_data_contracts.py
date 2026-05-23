from __future__ import annotations

import pytest

from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    validate_building_snapshot,
)
from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    BuildingConnectorSnapshot,
    BuildingFootprintCell,
    BuildingSnapshot,
    TransportRegistryEntry,
    build_snapshot_meta,
)


def test_footprint_sort_key_stable_regardless_of_input_order() -> None:
    cells = (
        BuildingFootprintCell(x=1, y=0, order_index=1),
        BuildingFootprintCell(x=0, y=0, order_index=0),
    )
    b = BuildingSnapshot(
        canonical_id="bv:test",
        internal_name="test_miner",
        footprint_cells=cells,
        connectors=(),
    )
    ordered = validate_building_snapshot(b)
    assert tuple(ordered.footprint_cells) == (
        BuildingFootprintCell(x=0, y=0, order_index=0),
        BuildingFootprintCell(x=1, y=0, order_index=1),
    )


def test_snapshot_meta_hashable_when_frozen() -> None:
    meta = build_snapshot_meta(
        data_revision="abc",
        db_alias="default",
        built_at_utc="2026-05-21T00:00:00Z",
        content_hash="deadbeef",
        game_version="1.0",
    )
    assert hash(meta) == hash(meta)


def test_rejects_list_footprint() -> None:
    with pytest.raises(TypeError):
        BuildingSnapshot(
            canonical_id="x",
            internal_name="y",
            footprint_cells=[],  # type: ignore[arg-type]
            connectors=(),
        )


def test_rejects_list_connectors() -> None:
    with pytest.raises(TypeError):
        BuildingSnapshot(
            canonical_id="x",
            internal_name="y",
            footprint_cells=(),
            connectors=[],  # type: ignore[arg-type]
        )


def test_connector_sort_key_stable_regardless_of_input_order() -> None:
    connectors = (
        BuildingConnectorSnapshot(
            order_index=1,
            connector_role="output",
            tile_direction="east",
            io_channel_type="shape",
            position_x=1,
            position_y=0,
            position_z=0,
        ),
        BuildingConnectorSnapshot(
            order_index=0,
            connector_role="input",
            tile_direction="west",
            io_channel_type="shape",
            position_x=0,
            position_y=0,
            position_z=0,
        ),
    )
    b = BuildingSnapshot(
        canonical_id="bv:test",
        internal_name="test_miner",
        footprint_cells=(),
        connectors=connectors,
    )
    ordered = validate_building_snapshot(b)
    assert tuple(c.order_index for c in ordered.connectors) == (0, 1)


def test_content_hash_stable_across_building_order() -> None:
    from django_apps.asteroid_lab.contracts.game_data_snapshot import (
        AsteroidGameDataSnapshot,
        BuildingSnapshot,
    )
    from django_apps.asteroid_lab.contracts.game_data_snapshot import (
        snapshot_content_hash,
    )

    meta = build_snapshot_meta(
        data_revision="rev1",
        db_alias="default",
        built_at_utc="2026-05-21T00:00:00Z",
        content_hash="placeholder",
        game_version="1.0",
    )
    b_a = BuildingSnapshot(
        canonical_id="bv:a",
        internal_name="aaa",
        footprint_cells=(BuildingFootprintCell(0, 0, 0),),
        connectors=(),
    )
    b_b = BuildingSnapshot(
        canonical_id="bv:b",
        internal_name="bbb",
        footprint_cells=(BuildingFootprintCell(0, 0, 0),),
        connectors=(),
    )
    snap1 = AsteroidGameDataSnapshot(meta=meta, buildings=(b_b, b_a), transport_registry=())
    snap2 = AsteroidGameDataSnapshot(meta=meta, buildings=(b_a, b_b), transport_registry=())
    assert snapshot_content_hash(snap1) == snapshot_content_hash(snap2)


def test_content_hash_stable_when_footprint_order_permuted() -> None:
    from django_apps.asteroid_lab.contracts.game_data_snapshot import (
        AsteroidGameDataSnapshot,
    )
    from django_apps.asteroid_lab.contracts.game_data_snapshot import (
        snapshot_content_hash,
    )

    meta = build_snapshot_meta(
        data_revision="rev1",
        db_alias="default",
        built_at_utc="2026-05-21T00:00:00Z",
        content_hash="placeholder",
        game_version="1.0",
    )
    fp_a = BuildingFootprintCell(x=0, y=0, order_index=0)
    fp_b = BuildingFootprintCell(x=1, y=0, order_index=1)
    b1 = BuildingSnapshot(
        canonical_id="bv:a",
        internal_name="aaa",
        footprint_cells=(fp_b, fp_a),
        connectors=(),
    )
    b2 = BuildingSnapshot(
        canonical_id="bv:a",
        internal_name="aaa",
        footprint_cells=(fp_a, fp_b),
        connectors=(),
    )
    snap1 = AsteroidGameDataSnapshot(meta=meta, buildings=(b1,), transport_registry=())
    snap2 = AsteroidGameDataSnapshot(meta=meta, buildings=(b2,), transport_registry=())
    assert snapshot_content_hash(snap1) == snapshot_content_hash(snap2)


def test_content_hash_stable_when_connector_order_permuted() -> None:
    from django_apps.asteroid_lab.contracts.game_data_snapshot import (
        AsteroidGameDataSnapshot,
    )
    from django_apps.asteroid_lab.contracts.game_data_snapshot import (
        snapshot_content_hash,
    )

    meta = build_snapshot_meta(
        data_revision="rev1",
        db_alias="default",
        built_at_utc="2026-05-21T00:00:00Z",
        content_hash="placeholder",
        game_version="1.0",
    )
    conn_a = BuildingConnectorSnapshot(
        order_index=0,
        connector_role="input",
        tile_direction="west",
        io_channel_type="shape",
        position_x=0,
        position_y=0,
        position_z=0,
    )
    conn_b = BuildingConnectorSnapshot(
        order_index=1,
        connector_role="output",
        tile_direction="east",
        io_channel_type="shape",
        position_x=1,
        position_y=0,
        position_z=0,
    )
    b1 = BuildingSnapshot(
        canonical_id="bv:a",
        internal_name="aaa",
        footprint_cells=(),
        connectors=(conn_b, conn_a),
    )
    b2 = BuildingSnapshot(
        canonical_id="bv:a",
        internal_name="aaa",
        footprint_cells=(),
        connectors=(conn_a, conn_b),
    )
    snap1 = AsteroidGameDataSnapshot(meta=meta, buildings=(b1,), transport_registry=())
    snap2 = AsteroidGameDataSnapshot(meta=meta, buildings=(b2,), transport_registry=())
    assert snapshot_content_hash(snap1) == snapshot_content_hash(snap2)


def test_content_hash_stable_when_transport_registry_order_permuted() -> None:
    from django_apps.asteroid_lab.contracts.game_data_snapshot import (
        AsteroidGameDataSnapshot,
        BuildingSnapshot,
    )
    from django_apps.asteroid_lab.contracts.game_data_snapshot import (
        snapshot_content_hash,
    )

    meta = build_snapshot_meta(
        data_revision="rev1",
        db_alias="default",
        built_at_utc="2026-05-21T00:00:00Z",
        content_hash="placeholder",
        game_version="1.0",
    )
    building = BuildingSnapshot(
        canonical_id="bv:a",
        internal_name="aaa",
        footprint_cells=(),
        connectors=(),
    )
    t_z = TransportRegistryEntry("z_kind", "belt", "bv:a")
    t_a = TransportRegistryEntry("a_kind", "belt", "bv:a")
    snap1 = AsteroidGameDataSnapshot(
        meta=meta,
        buildings=(building,),
        transport_registry=(t_z, t_a),
    )
    snap2 = AsteroidGameDataSnapshot(
        meta=meta,
        buildings=(building,),
        transport_registry=(t_a, t_z),
    )
    assert snapshot_content_hash(snap1) == snapshot_content_hash(snap2)
