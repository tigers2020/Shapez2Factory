"""Solver run persists ``game_data_snapshot_meta`` provenance (v0; not algorithm input)."""

from __future__ import annotations

import base64
import gzip
import json
import random

import pytest
from django.test import Client
from django.urls import reverse

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.services.sample_gene_exhaustive_generator import (
    generate_exhaustive_sample_genes,
)
from django_apps.asteroid_lab.services.solver_run_config_keys import (
    SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_META_KEY,
)
from django_apps.asteroid_lab.services.solver_runtime_entry import run_solver_runtime_for_project
from django_apps.web.services.asteroid_game_data_snapshot import build_asteroid_game_data_snapshot

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def seed_gene_templates_db() -> None:
    genes, _ = generate_exhaustive_sample_genes(
        max_extensions=0, transport_kinds=("belt",), generator_version="exhaustive_sample_gene_v1"
    )
    for g in genes:
        m.GeneticSample.objects.update_or_create(
            gene_key=g.key,
            defaults={
                "name": g.name,
                "code": g.encoded_copy_string,
                "metadata_json": dict(g.metadata),
            },
        )


def _encode_v4_copy(root: dict) -> str:
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(text)
    b64 = base64.b64encode(gz).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


def _project_with_map_input() -> m.AsteroidProject:
    copy = _encode_v4_copy(
        {
            "V": random.randint(1, 10_000_000),
            "BP": {
                "$type": "Island",
                "Entries": [
                    {"X": 1, "Y": 0, "T": "Layout_ProMiner"},
                    {"X": 2, "Y": 0, "T": "SpaceBelt_Left"},
                ],
            },
        }
    )
    client = Client()
    client.post(
        reverse("web:asteroid-miner-layout-projects-create"),
        {"copy_code": copy},
        follow=True,
    )
    return m.AsteroidProject.objects.latest("id")


def test_run_solver_runtime_entry_persists_game_data_snapshot_meta(
    imported_game_data_batch,
) -> None:
    proj = _project_with_map_input()
    snapshot = build_asteroid_game_data_snapshot()

    result = run_solver_runtime_for_project(
        int(proj.pk),
        game_data_snapshot=snapshot,
    )

    assert result.ok is True
    assert result.solver_run_id is not None
    run = m.SolverRun.objects.get(pk=int(result.solver_run_id))
    meta = run.config_json.get(SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_META_KEY)
    assert meta == {
        "schema_version": snapshot.meta.schema_version,
        "data_revision": snapshot.meta.data_revision,
        "content_hash": snapshot.meta.content_hash,
    }
    assert meta["data_revision"] == imported_game_data_batch.manifest_self_hash


def test_post_run_solver_persists_game_data_snapshot_meta(
    imported_game_data_batch,
) -> None:
    proj = _project_with_map_input()
    url = reverse("web:asteroid-miner-layout-project-run-solver", kwargs={"slug": proj.slug})
    response = Client().post(url, HTTP_ACCEPT="application/json")
    assert response.status_code == 200
    data = json.loads(response.content.decode())
    assert data["ok"] is True
    run = m.SolverRun.objects.get(pk=int(data["solver_run_id"]))
    meta = run.config_json.get(SOLVER_RUN_CONFIG_GAME_DATA_SNAPSHOT_META_KEY)
    assert isinstance(meta, dict)
    assert meta["data_revision"] == imported_game_data_batch.manifest_self_hash
    assert len(meta.get("content_hash") or "") == 64
