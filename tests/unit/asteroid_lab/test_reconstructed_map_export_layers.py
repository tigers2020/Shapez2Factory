"""export_json vs decoded_json lab layer separation."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string, encode_copy_string
from django_apps.asteroid_lab.adapters.normalization import normalize_decoded_blueprint
from django_apps.asteroid_lab.services.input_service import persist_decoded_snapshot_for_map_input
from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
    persist_reconstructed_asteroid_map,
    run_reconstruction_for_map_input,
)
from django_apps.asteroid_lab.services.reconstructed_map_persist_builder import (
    _scan_forbidden_export_keys,
)


@pytest.fixture
def hole_island_copy() -> str:
    decoded = {
        "V": 21,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_FluidMiner"},
                {"X": 2, "Y": 0, "T": "Layout_FluidMinerExtension"},
                {"X": 1, "Y": 1, "T": "UnknownTile_A"},
                {"X": 2, "Y": 1, "T": "UnknownTile_B"},
            ],
        },
    }
    return encode_copy_string(decoded)


@pytest.mark.django_db
def test_reconstructed_map_export_layers(hole_island_copy: str) -> None:
    proj = m.AsteroidProject.objects.create(name="Layers", slug="recon-layers")
    inp = m.AsteroidMapInput.objects.create(project=proj, copy_code=hole_island_copy)
    norm = normalize_decoded_blueprint(decode_copy_string(hole_island_copy.removesuffix("$")))
    persist_decoded_snapshot_for_map_input(inp.id, norm)

    cleanup, recon = run_reconstruction_for_map_input(inp.id)
    pk = persist_reconstructed_asteroid_map(
        map_input_id=inp.id,
        run_key="layers",
        recon=recon,
        cleanup=cleanup,
    )
    row = m.ReconstructedAsteroidMap.objects.get(pk=pk)

    assert row.decoded_json.get("_asteroid_lab_summary") is not None
    assert row.decoded_json.get("_asteroid_lab_coord_system") is not None
    assert _scan_forbidden_export_keys(row.export_json) == []
    assert row.rebuilt_copy_code.startswith("SHAPEZ2-4-")
    assert row.copy_code == row.rebuilt_copy_code
    assert row.original_copy_code == hole_island_copy

    roundtrip = decode_copy_string(row.rebuilt_copy_code.removesuffix("$")).root
    rt_entries = roundtrip.get("BP", {}).get("Entries") or []
    ex_entries = row.export_json.get("BP", {}).get("Entries") or []
    assert len(rt_entries) == len(ex_entries)
    assert all(str(e.get("T", "")).endswith("MinerExtension") for e in ex_entries)

    assert row.decoded_json["BP"]["Entries"][0].get("server_x") is not None
