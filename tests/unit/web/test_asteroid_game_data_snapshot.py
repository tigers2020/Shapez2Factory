"""Web assembler for ``AsteroidGameDataSnapshot``."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.contracts.game_data_snapshot import (
    SCHEMA_VERSION,
    snapshot_content_hash,
)
from django_apps.game_data.models import ImportBatch
from django_apps.web.services.asteroid_game_data_snapshot import build_asteroid_game_data_snapshot

pytestmark = pytest.mark.django_db


def test_assemble_snapshot_matches_pinned_revision(imported_game_data_batch: ImportBatch) -> None:
    snap = build_asteroid_game_data_snapshot(db_alias="default")

    assert snap.meta.schema_version == SCHEMA_VERSION
    assert snap.meta.data_revision == imported_game_data_batch.manifest_self_hash
    assert snap.meta.db_alias == "default"
    assert snap.meta.built_at_utc.endswith("Z")
    assert len(snap.meta.content_hash) == 64
    assert snap.meta.content_hash == snapshot_content_hash(snap)
    assert len(snap.buildings) > 0

    building_keys = [(b.internal_name, b.canonical_id) for b in snap.buildings]
    assert building_keys == sorted(building_keys)

    snap_again = build_asteroid_game_data_snapshot(db_alias="default")
    assert snap_again.meta.data_revision == snap.meta.data_revision
    assert snap_again.meta.content_hash == snap.meta.content_hash
