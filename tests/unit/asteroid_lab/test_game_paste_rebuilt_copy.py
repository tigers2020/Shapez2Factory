"""``rebuilt_copy_code`` must be a non-empty in-game paste string (official island export)."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.adapters.normalization import normalize_decoded_blueprint
from django_apps.asteroid_lab.services.input_service import persist_decoded_snapshot_for_map_input
from django_apps.asteroid_lab.services.reconstructed_map_persist_builder import (
    build_reconstructed_map_persist_payload,
)
from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
    persist_reconstructed_asteroid_map,
    run_reconstruction_for_map_input,
)
from django_apps.asteroid_lab.services.replay_pipeline_service import (
    build_initial_replay_for_map_input,
)

_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "asteroid_lab"
    / "miner_extension_column_dup_cleanup.txt"
)


@pytest.mark.django_db
def test_extension_only_import_yields_nonempty_game_copy() -> None:
    """Regression: extension-column game imports had recon.cells=0 → empty paste code."""

    if not _FIXTURE.is_file():
        pytest.skip("fixture missing")

    from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string as dec

    copy_code = _FIXTURE.read_text(encoding="utf-8").strip()
    proj = m.AsteroidProject.objects.create(name="Paste", slug="game-paste-ext-col")
    inp = m.AsteroidMapInput.objects.create(project=proj, copy_code=copy_code)
    norm = normalize_decoded_blueprint(dec(copy_code.removesuffix("$")))
    persist_decoded_snapshot_for_map_input(inp.id, norm)
    inp.refresh_from_db()

    cleanup, recon = run_reconstruction_for_map_input(inp.id)
    assert len(recon.cells) == 0

    payload = build_reconstructed_map_persist_payload(
        map_input_id=inp.id,
        run_key="paste",
        recon=recon,
        cleanup=cleanup,
        source_decoded_json=dict(inp.decoded_json),
    )
    assert len(payload.export_json.get("BP", {}).get("Entries", [])) >= 200
    assert len(payload.rebuilt_copy_code) > 400

    decoded = decode_copy_string(payload.rebuilt_copy_code.removesuffix("$"))
    n = len(decoded.root.get("BP", {}).get("Entries", []))
    assert n >= 200
    assert decoded.root.get("V") == 1137


@pytest.fixture
def hole_island_copy() -> str:
    from django_apps.asteroid_lab.adapters.decode_adapter import encode_copy_string

    decoded = {
        "V": 21,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_FluidMiner"},
                {"X": 2, "Y": 0, "T": "SpacePipe_Forward"},
                {"X": 3, "Y": 0, "T": "Layout_FluidMinerExtension"},
                {"X": 1, "Y": 1, "T": "UnknownTile_A"},
                {"X": 2, "Y": 1, "T": "UnknownTile_B"},
            ],
        },
    }
    return encode_copy_string(decoded)


@pytest.mark.django_db
def test_pipeline_rebuilt_copy_matches_source_entry_count(hole_island_copy: str) -> None:
    proj = m.AsteroidProject.objects.create(name="Hole", slug="game-paste-hole")
    inp = m.AsteroidMapInput.objects.create(project=proj, copy_code=hole_island_copy)
    result = build_initial_replay_for_map_input(inp.id, force=True)
    assert result.status == "ok"
    row = m.ReconstructedAsteroidMap.objects.get(pk=result.reconstructed_asteroid_map_id)
    n_export = len(row.export_json.get("BP", {}).get("Entries", []))
    assert n_export >= 1
    decoded = decode_copy_string(row.rebuilt_copy_code.removesuffix("$"))
    assert len(decoded.root.get("BP", {}).get("Entries", [])) == n_export
