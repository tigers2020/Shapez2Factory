"""Persist reconstructed asteroid maps via inspection replay pipeline."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string, encode_copy_string
from django_apps.asteroid_lab.adapters.normalization import normalize_decoded_blueprint
from django_apps.asteroid_lab.adapters.reconstruction_blueprint_export import (
    load_reconstruction_cells_from_decoded_json,
    reconstruction_cell_keys,
)
from django_apps.asteroid_lab.services.input_service import persist_decoded_snapshot_for_map_input
from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
    load_reconstructed_asteroid_cells,
    persist_reconstructed_asteroid_map,
    run_reconstruction_for_map_input,
)
from django_apps.asteroid_lab.services.replay_pipeline_service import (
    build_initial_replay_for_map_input,
)


@pytest.fixture
def hole_island_decoded() -> dict:
    """Ring of UnknownTile around (2,2) + fluid miner — yields filled asteroid field after recon."""

    return {
        "V": 21,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_FluidMiner"},
                {"X": 2, "Y": 0, "T": "SpacePipe_Forward"},
                {"X": 3, "Y": 0, "T": "Layout_FluidMinerExtension"},
                {"X": 1, "Y": 1, "T": "UnknownTile_A"},
                {"X": 2, "Y": 1, "T": "UnknownTile_B"},
                {"X": 3, "Y": 1, "T": "UnknownTile_C"},
                {"X": 1, "Y": 2, "T": "UnknownTile_D"},
                {"X": 3, "Y": 2, "T": "UnknownTile_E"},
                {"X": 1, "Y": 3, "T": "UnknownTile_F"},
                {"X": 2, "Y": 3, "T": "UnknownTile_G"},
                {"X": 3, "Y": 3, "T": "UnknownTile_H"},
            ],
        },
    }


@pytest.fixture
def hole_island_copy(hole_island_decoded: dict) -> str:
    return encode_copy_string(hole_island_decoded)


@pytest.mark.django_db
def test_persist_reconstructed_map_idempotent(hole_island_copy: str) -> None:
    proj = m.AsteroidProject.objects.create(name="Recon", slug="recon-persist")
    inp = m.AsteroidMapInput.objects.create(
        project=proj,
        copy_code=hole_island_copy,
        source_kind=m.AsteroidMapInput.SourceKind.COPY_CODE,
    )
    norm = normalize_decoded_blueprint(decode_copy_string(hole_island_copy.removesuffix("$")))
    persist_decoded_snapshot_for_map_input(inp.id, norm)

    cleanup, recon = run_reconstruction_for_map_input(inp.id)
    pk1 = persist_reconstructed_asteroid_map(
        map_input_id=inp.id,
        run_key="manual-1",
        recon=recon,
        cleanup=cleanup,
        cleanup_summary=dict(cleanup.summary_json),
    )
    pk2 = persist_reconstructed_asteroid_map(
        map_input_id=inp.id,
        run_key="manual-1",
        recon=recon,
        cleanup=cleanup,
        cleanup_summary=dict(cleanup.summary_json),
    )
    assert pk1 == pk2
    assert m.ReconstructedAsteroidMap.objects.filter(map_input=inp).count() == 1
    row = m.ReconstructedAsteroidMap.objects.get(pk=pk1)
    assert row.copy_code.endswith("$")
    assert row.original_copy_code == hole_island_copy.strip()
    assert row.original_decoded_json.get("BP")
    assert row.decoded_json.get("BP", {}).get("Entries")


@pytest.mark.django_db
def test_pipeline_persists_reconstructed_map(hole_island_copy: str) -> None:
    proj = m.AsteroidProject.objects.create(name="Pipe", slug="recon-pipe")
    inp = m.AsteroidMapInput.objects.create(
        project=proj,
        copy_code=hole_island_copy,
        source_kind=m.AsteroidMapInput.SourceKind.COPY_CODE,
    )
    result = build_initial_replay_for_map_input(inp.id, force=True)
    assert result.status == "ok"
    assert result.reconstructed_asteroid_map_id is not None
    row = m.ReconstructedAsteroidMap.objects.get(pk=result.reconstructed_asteroid_map_id)
    assert row.run_key == result.run_key
    loaded = load_reconstructed_asteroid_cells(pk=row.pk)
    kinds = {c.cell_kind for c in loaded}
    assert "asteroid_shape_field" in kinds or "asteroid_fluid_field" in kinds


@pytest.mark.django_db
def test_load_orm_row_imports_field_kinds_not_miner_extension(hole_island_copy: str) -> None:
    proj = m.AsteroidProject.objects.create(name="Load", slug="recon-load")
    inp = m.AsteroidMapInput.objects.create(project=proj, copy_code=hole_island_copy)
    norm = normalize_decoded_blueprint(decode_copy_string(hole_island_copy.removesuffix("$")))
    persist_decoded_snapshot_for_map_input(inp.id, norm)
    cleanup, recon = run_reconstruction_for_map_input(inp.id)
    pk = persist_reconstructed_asteroid_map(
        map_input_id=inp.id,
        run_key="load-test",
        recon=recon,
        cleanup=cleanup,
    )
    cells = load_reconstructed_asteroid_cells(pk=pk)
    assert "shape_miner_extension" not in {c.cell_kind for c in cells}
    row = m.ReconstructedAsteroidMap.objects.get(pk=pk)
    direct = load_reconstruction_cells_from_decoded_json(dict(row.decoded_json))
    assert reconstruction_cell_keys(cells) == reconstruction_cell_keys(direct)
