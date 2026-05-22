"""Integration: Run Solver persists game_data snapshot meta in config_json."""

from __future__ import annotations

import base64
import gzip
import json
import random
from pathlib import Path

import pytest
from django.test import Client
from django.urls import reverse

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_META_KEY,
)
from django_apps.game_data.selectors.import_batch import pin_latest_import_batch

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


def _game_data_dir() -> Path:
    root = Path(__file__).resolve().parents[3]
    data_dir = root / "documents" / "game_data"
    if not (data_dir / "manifest.json").is_file():
        pytest.skip("documents/game_data not present")
    return data_dir


@pytest.mark.django_db
def test_run_solver_persists_game_data_snapshot_meta() -> None:
    from django_apps.game_data.importers import GameDataImporter

    GameDataImporter(_game_data_dir(), batch_name="pytest-integration-snapshot").run()
    batch = pin_latest_import_batch()
    client = Client()
    copy_code = _unique_valid_copy()
    create_url = reverse("web:asteroid-miner-layout-projects-create")
    client.post(create_url, {"copy_code": copy_code}, follow=True)
    project = m.AsteroidProject.objects.get()
    run_url = reverse(
        "web:asteroid-miner-layout-project-run-solver",
        kwargs={"slug": project.slug},
    )
    response = client.post(run_url)
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    run_id = body["solver_run_id"]
    assert run_id is not None
    run = m.SolverRun.objects.get(pk=int(run_id))
    meta = (run.config_json or {}).get(SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_META_KEY)
    assert meta is not None
    assert meta["data_revision"] == batch.manifest_self_hash
    assert meta["schema_version"] == "game_data_snapshot_v1"
    assert len(meta["content_hash"]) == 64
