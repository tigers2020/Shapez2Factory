"""Decode-on-create for AsteroidMapInput."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.decode_adapter import encode_copy_string
from django_apps.asteroid_lab.services.input_service import create_copy_code_map_input


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
    with_xy = sum(
        1
        for e in entries
        if isinstance(e, dict)
        and isinstance(e.get("server_x"), int)
        and isinstance(e.get("server_y"), int)
    )
    assert with_xy == len([e for e in entries if isinstance(e, dict)])
    assert inp.decoded_json.get("_asteroid_lab_summary") is not None
    assert inp.decoded_json.get("_asteroid_lab_coord_system") is not None
