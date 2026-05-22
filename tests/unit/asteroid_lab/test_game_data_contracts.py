from __future__ import annotations

import pytest

from django_apps.asteroid_lab.optimization.game_data_contract_validation import (
    validate_building_snapshot,
)
from django_apps.asteroid_lab.optimization.game_data_contracts import (
    BuildingFootprintCell,
    BuildingSnapshot,
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


def test_content_hash_stable_across_building_order() -> None:
    from django_apps.asteroid_lab.optimization.game_data_contracts import (
        AsteroidGameDataSnapshot,
        BuildingSnapshot,
    )
    from django_apps.asteroid_lab.optimization.game_data_snapshot_hash import (
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
