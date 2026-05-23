"""POST run_solver returns SOLVER_NOT_AVAILABLE (HTTP 200, never 500)."""

from __future__ import annotations

import pytest
from django.test import Client
from django.urls import reverse

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_runtime_entry import SolverRuntimeEntryErrorCode

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module):
    """run-solver view builds game_data snapshot from pinned import batch."""

    return imported_game_data_batch_module


@pytest.fixture
def client() -> Client:
    return Client()


def _project_slug_via_create() -> str:
    proj = m.AsteroidProject.objects.create(
        name="ReplayTimelineSmoke",
        slug="replay-timeline-smoke",
    )
    m.AsteroidMapInput.objects.create(project=proj, copy_code="SHAPEZ2-4-e30=")
    return str(proj.slug)


def test_run_solver_post_returns_solver_not_available(client: Client) -> None:
    proj = m.AsteroidProject.objects.create(name="RunSolver", slug="run-solver-stub")
    m.AsteroidMapInput.objects.create(project=proj, copy_code="SHAPEZ2-4-e30=")
    url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": proj.slug})
    response = client.post(url)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["error_code"] == SolverRuntimeEntryErrorCode.SOLVER_NOT_AVAILABLE.value
    assert "reconstruction is still available" in data.get("message", "").lower()
