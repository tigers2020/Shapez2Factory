"""Selectors for game_data snapshot materialization."""

from __future__ import annotations

import pytest


@pytest.mark.django_db
def test_pin_import_batch_returns_manifest_self_hash(imported_game_data_batch):
    from django_apps.game_data.selectors.import_batch import pin_latest_import_batch

    batch = pin_latest_import_batch(db_alias="default")
    assert batch.manifest_self_hash == imported_game_data_batch.manifest_self_hash


@pytest.mark.django_db
def test_building_rows_split_queries(imported_game_data_batch):
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    from django_apps.game_data.selectors.buildings import fetch_building_rows_for_batch

    with CaptureQueriesContext(connection) as ctx:
        rows = fetch_building_rows_for_batch(imported_game_data_batch.pk)
    assert len(ctx) <= 3
    assert len({r.id for r in rows.variants}) == len(rows.variants)


@pytest.mark.django_db
def test_transport_registry_ordered_by_kind(imported_game_data_batch):
    from django_apps.game_data.selectors.transport_registry import (
        fetch_transport_rows_for_batch,
    )

    rows = fetch_transport_rows_for_batch(imported_game_data_batch.pk)
    kinds = [row.transport_kind for row in rows]
    assert kinds == sorted(kinds)
