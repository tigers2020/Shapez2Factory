"""Decode-on-create for AsteroidMapInput."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.decode_adapter import encode_copy_string
from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input
from django_apps.asteroid_lab.snapshots.layout_fingerprint import (
    COORD_SYSTEM_ISLAND_BBOX_LEFT_BOTTOM,
)


@pytest.fixture
def tiny_island_copy() -> str:
    root = {
        "V": 21,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 1, "Y": 0, "T": "Layout_FluidMiner"},
                {"X": 2, "Y": 0, "T": "Layout_FluidMinerExtension"},
            ],
        },
    }
    return encode_copy_string(root)


@pytest.mark.django_db
def test_create_copy_code_map_input_populates_decoded_json(tiny_island_copy: str) -> None:
    proj = m.AsteroidProject.objects.create(name="DecodeOnCreate", slug="decode-on-create")
    inp = create_copy_code_map_input(proj, tiny_island_copy)

    assert inp.source_kind == m.AsteroidMapInput.SourceKind.DECODED_JSON
    assert inp.decoded_json.get("BP", {}).get("Entries")
    entries = inp.decoded_json["BP"]["Entries"]
    assert len(entries) >= 2
    assert inp.decoded_json.get("_asteroid_lab_summary") is not None
    meta = inp.decoded_json.get("_asteroid_lab_coord_system")
    assert isinstance(meta, dict)
    assert meta.get("coord_system") == COORD_SYSTEM_ISLAND_BBOX_LEFT_BOTTOM
