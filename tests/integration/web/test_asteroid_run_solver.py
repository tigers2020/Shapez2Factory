"""HTTP POST run-solver integration tests (PR8)."""

from __future__ import annotations

import base64
import gzip
import json
import random

import pytest
from django.test import Client
from django.urls import reverse

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_runtime_entry import SolverRuntimeEntryErrorCode

pytestmark = pytest.mark.django_db


def _encode_v4_copy(root: dict) -> str:
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(text)
    b64 = base64.b64encode(gz).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


def _unique_valid_copy() -> str:
    return _encode_v4_copy(
        {
            "V": random.randint(1, 10_000_000),
            "BP": {
                "$type": "Island",
                "Entries": [
                    {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                    {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
                    {"X": 3, "Y": 1, "T": "Layout_ShapeMinerExtension"},
                ],
            },
        }
    )


def _project_slug_via_create() -> str:
    client = Client()
    copy = _unique_valid_copy()
    client.post(
        reverse("web:asteroid-miner-layout-projects-create"),
        {"copy_code": copy},
        follow=True,
    )
    return str(m.AsteroidProject.objects.get().slug)


def test_post_run_solver_json_persists_and_returns_payload() -> None:
    slug = _project_slug_via_create()
    url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug})
    response = Client().post(url, HTTP_ACCEPT="application/json")

    assert response.status_code == 200
    data = json.loads(response.content.decode())
    assert data["ok"] is True
    assert data["solver_run_id"] is not None
    assert len(data.get("optimization_replay", {}).get("frames") or []) >= 1
    assert isinstance(data.get("solver_summary"), dict)
    assert data["validation_passed"] is True


def test_post_run_solver_unknown_slug_404() -> None:
    url = reverse(
        "web:asteroid-miner-layout-project-run-solver",
        kwargs={"slug": "nonexistent-slug-xyz"},
    )
    response = Client().post(url, HTTP_ACCEPT="application/json")
    assert response.status_code == 404
    data = json.loads(response.content.decode())
    assert data["ok"] is False
    assert data["error_code"] == SolverRuntimeEntryErrorCode.PROJECT_NOT_FOUND.value


def test_post_run_solver_no_map_input_400() -> None:
    proj = m.AsteroidProject.objects.create(name="Empty", slug="run-solver-empty")
    url = reverse(
        "web:asteroid-miner-layout-project-run-solver",
        kwargs={"slug": proj.slug},
    )
    response = Client().post(url, HTTP_ACCEPT="application/json")
    assert response.status_code == 400
    data = json.loads(response.content.decode())
    assert data["ok"] is False
    assert data["error_code"] == SolverRuntimeEntryErrorCode.NO_MAP_INPUT.value


def test_get_project_page_includes_optimization_replay_after_run() -> None:
    slug = _project_slug_via_create()
    run_url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": slug})
    Client().post(run_url, HTTP_ACCEPT="application/json")

    page = Client().get(reverse("web:asteroid-miner-layout-project", kwargs={"slug": slug}))
    assert page.status_code == 200
    assert b'id="lab-optimization-replay-data"' in page.content
