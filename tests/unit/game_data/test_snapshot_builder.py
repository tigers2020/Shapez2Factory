"""Snapshot row bundle builder — determinism and fail-fast."""

from __future__ import annotations

import pytest


@pytest.mark.django_db
def test_builder_deterministic_rows(imported_game_data_batch_module):
    from django_apps.game_data.snapshots.builder import build_game_data_row_bundle

    b1 = build_game_data_row_bundle(imported_game_data_batch_module.pk)
    b2 = build_game_data_row_bundle(imported_game_data_batch_module.pk)
    assert b1 == b2


@pytest.mark.django_db
def test_builder_fails_when_footprint_missing_variant(imported_game_data_batch_module):
    from types import SimpleNamespace
    from unittest.mock import patch

    from django_apps.game_data.selectors.buildings import (
        BuildingRowsBundle,
        fetch_building_rows_for_batch,
    )
    from django_apps.game_data.snapshots.builder import build_game_data_row_bundle
    from django_apps.game_data.snapshots.errors import SnapshotBuildError, SnapshotBuildErrorCode

    real = fetch_building_rows_for_batch(imported_game_data_batch_module.pk)
    orphan_fp = SimpleNamespace(
        building_variant_id=999999999,
        x=0,
        y=0,
        order_index=0,
    )
    injected = BuildingRowsBundle(
        variants=real.variants,
        footprints=[*real.footprints, orphan_fp],
        connectors=real.connectors,
    )

    with patch(
        "django_apps.game_data.snapshots.builder.fetch_building_rows_for_batch",
        return_value=injected,
    ):
        with pytest.raises(SnapshotBuildError) as exc:
            build_game_data_row_bundle(imported_game_data_batch_module.pk)
    assert exc.value.code == SnapshotBuildErrorCode.ORPHAN_FOOTPRINT
