"""Persist path must not query replay ORM tables."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

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
def tiny_copy() -> str:
    root = {
        "V": 21,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_FluidMiner"},
                {"X": 1, "Y": 1, "T": "UnknownTile_A"},
            ],
        },
    }
    return encode_copy_string(root)


@pytest.mark.django_db
def test_persistence_does_not_read_replay_frames(tiny_copy: str) -> None:
    proj = m.AsteroidProject.objects.create(name="NoReplay", slug="no-replay-persist")
    inp = m.AsteroidMapInput.objects.create(project=proj, copy_code=tiny_copy)
    norm = normalize_decoded_blueprint(decode_copy_string(tiny_copy.removesuffix("$")))
    persist_decoded_snapshot_for_map_input(inp.id, norm)
    cleanup, recon = run_reconstruction_for_map_input(inp.id)

    with patch.object(m.ReplayFrame.objects, "filter", MagicMock()) as mock_filter:
        persist_reconstructed_asteroid_map(
            map_input_id=inp.id,
            run_key="no-replay",
            recon=recon,
            cleanup=cleanup,
        )
        mock_filter.assert_not_called()
