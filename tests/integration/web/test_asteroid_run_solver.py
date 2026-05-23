"""POST run_solver — RTTP disabled stub or RTTP run (HTTP 200, never 500)."""

from __future__ import annotations

import base64
import gzip
import json

import pytest
from django.test import Client, override_settings
from django.urls import reverse

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input
from django_apps.asteroid_lab.services.solver_runtime_entry import SolverRuntimeEntryErrorCode

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module):
    """run-solver view builds game_data snapshot from pinned import batch."""

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


def _project_slug_via_create() -> str:
    proj = m.AsteroidProject.objects.create(
        name="ReplayTimelineSmoke",
        slug="replay-timeline-smoke",
    )
    create_copy_code_map_input(proj, _minimal_valid_copy())
    return str(proj.slug)


@override_settings(ASTEROID_LAB_RTTP_ENABLED=False)
def test_run_solver_post_returns_solver_not_available_when_rttp_disabled(client: Client) -> None:
    proj = m.AsteroidProject.objects.create(name="RunSolver", slug="run-solver-stub")
    m.AsteroidMapInput.objects.create(project=proj, copy_code="SHAPEZ2-4-e30=")
    url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": proj.slug})
    response = client.post(url)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["error_code"] == SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE.value
    assert "reconstruction is still available" in data.get("message", "").lower()


@override_settings(ASTEROID_LAB_RTTP_ENABLED=True)
def test_run_solver_post_rttp_does_not_return_solver_not_available(client: Client) -> None:
    proj = m.AsteroidProject.objects.create(name="RunSolverRttp", slug="run-solver-rttp")
    create_copy_code_map_input(proj, _minimal_valid_copy())
    url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": proj.slug})
    response = client.post(url)
    assert response.status_code == 200
    data = response.json()
    assert data.get("error_code") != SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE.value
    assert data.get("solver_run_id") is not None
