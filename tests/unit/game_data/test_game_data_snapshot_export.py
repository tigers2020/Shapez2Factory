"""Fail-closed guards for ORM → game_data snapshot export (SHA-13 / BA-8)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import patch

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import Client, override_settings
from django.urls import reverse

from django_apps.asteroid_lab import models as m
from django_apps.game_data.models.exterior_transport_capacity import (
    ExteriorFluidTransportCapacity,
    ExteriorShapeTransportCapacity,
)
from django_apps.game_data.models.mining import MiningExtractionRule
from django_apps.game_data.services.game_data_snapshot_export import (
    GameDataSnapshotExportError,
    GameDataSnapshotExportErrorCode,
    build_game_data_snapshot_payload,
)
from tests.integration.web.test_asteroid_miner_layout_solver import _unique_valid_copy


@pytest.mark.django_db
def test_build_game_data_snapshot_payload_succeeds_with_canon_rows() -> None:
    payload = build_game_data_snapshot_payload()
    assert payload["schema_version"] == "game_data_snapshot_v1"
    assert payload["exterior_transport_capacity"]
    assert payload["mining_extraction_rules"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("deactivate", "expected_code"),
    [
        (
            lambda: ExteriorShapeTransportCapacity.objects.filter(is_active=True).update(
                is_active=False
            ),
            GameDataSnapshotExportErrorCode.MISSING_SHAPE_EVTC,
        ),
        (
            lambda: ExteriorFluidTransportCapacity.objects.filter(is_active=True).update(
                is_active=False
            ),
            GameDataSnapshotExportErrorCode.MISSING_FLUID_EVTC,
        ),
        (
            lambda: MiningExtractionRule.objects.filter(
                resource_kind="shape", is_active=True
            ).update(is_active=False),
            GameDataSnapshotExportErrorCode.MISSING_SHAPE_MINING,
        ),
        (
            lambda: MiningExtractionRule.objects.filter(
                resource_kind="fluid", is_active=True
            ).update(is_active=False),
            GameDataSnapshotExportErrorCode.MISSING_FLUID_MINING,
        ),
    ],
)
def test_build_game_data_snapshot_payload_fails_closed_when_required_rows_missing(
    deactivate,
    expected_code: GameDataSnapshotExportErrorCode,
) -> None:
    deactivate()
    with pytest.raises(GameDataSnapshotExportError) as exc:
        build_game_data_snapshot_payload()
    assert exc.value.code == expected_code


@pytest.mark.django_db
def test_export_game_data_snapshot_command_fails_when_rows_missing(tmp_path) -> None:
    ExteriorShapeTransportCapacity.objects.filter(is_active=True).update(is_active=False)
    out_path = tmp_path / "snapshot.json"
    with pytest.raises(CommandError, match="no active ExteriorShapeTransportCapacity"):
        call_command("export_game_data_snapshot", out=str(out_path))
    assert not out_path.exists()


@pytest.mark.django_db
@override_settings(ASTEROID_LAB_SOLVER_ASYNC_DEFAULT=True)
def test_run_solver_returns_400_when_snapshot_export_fails(client: Client) -> None:
    slug = "export-fail-closed"
    project = m.AsteroidProject.objects.create(name="Export Fail", slug=slug)
    m.AsteroidMapInput.objects.create(project=project, copy_code=_unique_valid_copy())
    ExteriorShapeTransportCapacity.objects.filter(is_active=True).update(is_active=False)

    with patch(
        "django_apps.web.views.public_pages.build_asteroid_game_data_snapshot_with_provenance",
        return_value=SimpleNamespace(snapshot={}, provenance={}, catalog_slice={}),
    ):
        post = client.post(
            reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug}),
            data={},
            content_type="application/json",
        )

    assert post.status_code == 400
    body = post.json()
    assert body["ok"] is False
    assert body["error_code"] == GameDataSnapshotExportErrorCode.MISSING_SHAPE_EVTC.value
