"""POST run_solver config validation (PR-2c throughput target percent)."""

from __future__ import annotations

import base64
import gzip
import json

import pytest
from django.test import Client, override_settings
from django.urls import reverse

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module):
    return imported_game_data_batch_module


@pytest.fixture
def client() -> Client:
    return Client()


def _minimal_valid_copy() -> str:
    payload = json.dumps(
        {
            "V": 1,
            "BP": {
                "$type": "Island",
                "Entries": [
                    {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                    {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
                ],
            },
        },
        separators=(",", ":"),
    ).encode("utf-8")
    b64 = base64.b64encode(gzip.compress(payload)).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_rejects_percent_below_10(client: Client) -> None:
    proj = m.AsteroidProject.objects.create(name="PctLow", slug="pct-low")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": proj.slug})
    response = client.post(
        url,
        data=json.dumps({"throughput_target_percent": 5}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_throughput_target_percent"


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_rejects_percent_above_80(client: Client) -> None:
    proj = m.AsteroidProject.objects.create(name="PctHigh", slug="pct-high")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": proj.slug})
    response = client.post(
        url,
        data=json.dumps({"throughput_target_percent": 85}),
        content_type="application/json",
    )
    assert response.status_code == 400
    assert response.json()["error"] == "invalid_throughput_target_percent"
