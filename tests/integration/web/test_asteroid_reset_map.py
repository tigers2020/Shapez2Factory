"""POST reset-map purges runtime runs and returns replay bundle."""

from __future__ import annotations

import base64
import gzip
import json

import pytest
from django.test import Client
from django.urls import reverse

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.experiment_service import create_solver_run
from django_apps.asteroid_lab.services.lab_map_reset_service import INSPECTION_ALGORITHM_LABEL
from django_apps.asteroid_lab.services.project_service import create_project_from_copy_code
from django_apps.asteroid_lab.services.replay_pipeline_service import (
    build_initial_replay_for_map_input,
)

pytestmark = pytest.mark.django_db


@pytest.fixture(scope="module", autouse=True)
def _require_game_data_import_batch(imported_game_data_batch_module):
    return imported_game_data_batch_module


@pytest.fixture
def client() -> Client:
    return Client()


def _encode_v4_copy(root: dict) -> str:
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(text)
    b64 = base64.b64encode(gz).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


def _minimal_root(*, version: int = 7) -> dict:
    return {
        "V": version,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
            ],
        },
    }


def test_reset_map_post_returns_ok_and_replay_frames(client: Client) -> None:
    code = _encode_v4_copy(_minimal_root())
    dto = create_project_from_copy_code(code, source_label="reset-http")
    build_initial_replay_for_map_input(int(dto.map_input_id), overwrite=True)
    create_solver_run(
        int(dto.project_id),
        run_key="runtime-http",
        algorithm_label="runtime_v0",
        config={},
    )

    url = reverse(
        "web:asteroid-miner-layout-project-reset-map",
        kwargs={"slug": dto.slug},
    )
    response = client.post(url)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["replay_ok"] is True
    assert data.get("reset_map_url", "").endswith("/reset-map/")
    assert isinstance(data.get("lab_replay_frames_json"), list)
    assert len(data["lab_replay_frames_json"]) >= 1
    assert not m.SolverRun.objects.filter(
        project_id=int(dto.project_id),
        algorithm_label="runtime_v0",
    ).exists()
    assert m.SolverRun.objects.filter(
        project_id=int(dto.project_id),
        algorithm_label=INSPECTION_ALGORITHM_LABEL,
    ).exists()
