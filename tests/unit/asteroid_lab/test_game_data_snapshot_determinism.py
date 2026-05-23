"""Deterministic ``snapshot_content_hash`` across repeated snapshot assembly."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.contracts.game_data_snapshot import snapshot_content_hash
from django_apps.game_data.models import ImportBatch
from django_apps.web.services.asteroid_game_data_snapshot import build_asteroid_game_data_snapshot

pytestmark = pytest.mark.django_db


def test_repeated_build_produces_identical_content_hash(
    imported_game_data_batch: ImportBatch,
) -> None:
    first = build_asteroid_game_data_snapshot(db_alias="default")
    second = build_asteroid_game_data_snapshot(db_alias="default")

    assert first.meta.data_revision == imported_game_data_batch.manifest_self_hash
    assert second.meta.data_revision == imported_game_data_batch.manifest_self_hash
    assert snapshot_content_hash(first) == snapshot_content_hash(second)
    assert first.meta.content_hash == second.meta.content_hash
    assert len(first.meta.content_hash) == 64
