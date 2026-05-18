"""Anchor selection from cleanup-removed miner evidence."""

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


@pytest.fixture
def miner_and_pipe_copy() -> str:
    decoded = {
        "V": 21,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_FluidMiner"},
                {"X": 2, "Y": 0, "T": "SpacePipe_Forward"},
                {"X": 3, "Y": 0, "T": "Layout_FluidMinerExtension"},
                {"X": 1, "Y": 1, "T": "UnknownTile_A"},
            ],
        },
    }
    return encode_copy_string(decoded)


@pytest.mark.django_db
def test_reconstructed_anchor_selection(miner_and_pipe_copy: str) -> None:
    proj = m.AsteroidProject.objects.create(name="Anchor", slug="recon-anchor")
    inp = m.AsteroidMapInput.objects.create(project=proj, copy_code=miner_and_pipe_copy)
    norm = normalize_decoded_blueprint(decode_copy_string(miner_and_pipe_copy.removesuffix("$")))
    persist_decoded_snapshot_for_map_input(inp.id, norm)

    cleanup, recon = run_reconstruction_for_map_input(inp.id)
    removed_miners = [
        c
        for c in cleanup.removed_building_cells
        if c.cell_kind
        in ("fluid_miner", "shape_miner", "fluid_miner_extension", "shape_miner_extension")
    ]
    assert removed_miners
    expected = min(removed_miners, key=lambda c: (c.x, c.y))

    pk = persist_reconstructed_asteroid_map(
        map_input_id=inp.id,
        run_key="anchor",
        recon=recon,
        cleanup=cleanup,
    )
    row = m.ReconstructedAsteroidMap.objects.get(pk=pk)
    assert row.anchor_raw_x == expected.x
    assert row.anchor_raw_y == expected.y
    assert row.summary_json.get("anchor_fallback") is not True

    pipe_removed = [c for c in cleanup.removed_building_cells if c.cell_kind == "space_pipe"]
    assert pipe_removed
    assert row.anchor_raw_x != pipe_removed[0].x or row.anchor_raw_y != pipe_removed[0].y
