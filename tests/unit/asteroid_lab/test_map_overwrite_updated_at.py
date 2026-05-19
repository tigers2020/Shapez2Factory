"""Overwrite existing map inputs / reconstructed maps and touch updated_at."""

from __future__ import annotations

import time

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.decode_adapter import encode_copy_string
from django_apps.asteroid_lab.services.input_service import (
    refresh_map_input_from_copy_code,
    upsert_map_input_for_project,
)
from django_apps.asteroid_lab.services.project_service import create_project_from_copy_code
from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
    persist_reconstructed_asteroid_map,
    refresh_reconstructed_map_for_map_input,
    run_reconstruction_for_map_input,
)
from django_apps.asteroid_lab.services.replay_pipeline_service import (
    build_initial_replay_for_map_input,
)


def _island_copy(x: int = 1) -> str:
    return encode_copy_string(
        {
            "V": 21,
            "BP": {
                "$type": "Island",
                "Entries": [
                    {"X": x, "Y": 0, "T": "Layout_FluidMiner"},
                    {"X": x + 1, "Y": 0, "T": "Layout_FluidMinerExtension"},
                    {"X": x, "Y": 1, "T": "UnknownTile_A"},
                ],
            },
        }
    )


@pytest.mark.django_db
def test_upsert_overwrites_existing_map_input_decoded_json() -> None:
    proj = m.AsteroidProject.objects.create(name="Upsert", slug="map-upsert")
    code_a = _island_copy(1)
    inp1, created1 = upsert_map_input_for_project(proj, code_a)
    assert created1 is True
    t0 = inp1.updated_at
    time.sleep(0.01)
    inp2, created2 = upsert_map_input_for_project(proj, code_a)
    assert created2 is False
    assert inp2.pk == inp1.pk
    assert inp2.updated_at > t0
    assert inp2.decoded_json.get("BP", {}).get("Entries")

    code_b = _island_copy(2)
    inp3, created3 = upsert_map_input_for_project(proj, code_b)
    assert created3 is True
    assert inp3.pk != inp1.pk


@pytest.mark.django_db
def test_refresh_map_input_updates_copy_and_decoded() -> None:
    proj = m.AsteroidProject.objects.create(name="Refresh", slug="map-refresh")
    code = _island_copy(3)
    dto = create_project_from_copy_code(code)
    inp = m.AsteroidMapInput.objects.get(pk=dto.map_input_id)
    refreshed = refresh_map_input_from_copy_code(int(inp.pk), _island_copy(4))
    assert refreshed.pk == inp.pk
    assert refreshed.decoded_json.get("_asteroid_lab_summary") is not None


@pytest.mark.django_db
def test_pipeline_overwrite_reuses_run_key_and_reconstructed_row() -> None:
    code = _island_copy(5)
    dto = create_project_from_copy_code(code)
    r1 = build_initial_replay_for_map_input(dto.map_input_id)
    assert r1.status == "ok"
    assert r1.reconstructed_asteroid_map_id is not None
    recon_pk = int(r1.reconstructed_asteroid_map_id)
    run_key = r1.run_key

    r2 = build_initial_replay_for_map_input(dto.map_input_id, overwrite=True)
    assert r2.status == "ok"
    assert r2.run_key == run_key
    assert r2.reconstructed_asteroid_map_id == recon_pk
    row = m.ReconstructedAsteroidMap.objects.get(pk=recon_pk)
    assert row.decoded_json.get("BP")
    assert row.updated_at is not None


@pytest.mark.django_db
def test_refresh_reconstructed_map_overwrites_layers() -> None:
    code = _island_copy(6)
    dto = create_project_from_copy_code(code)
    cleanup, recon = run_reconstruction_for_map_input(dto.map_input_id)
    pk1 = persist_reconstructed_asteroid_map(
        map_input_id=dto.map_input_id,
        run_key="refresh-run",
        recon=recon,
        cleanup=cleanup,
    )
    row1 = m.ReconstructedAsteroidMap.objects.get(pk=pk1)
    t0 = row1.updated_at
    time.sleep(0.01)
    pk2 = refresh_reconstructed_map_for_map_input(
        dto.map_input_id,
        run_key="refresh-run",
    )
    assert pk1 == pk2
    row2 = m.ReconstructedAsteroidMap.objects.get(pk=pk2)
    assert row2.updated_at > t0
    assert row2.decoded_json.get("BP", {}).get("Entries")
