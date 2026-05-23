"""GeneticSample: decode-on-clean/save and admin sprite relpath helper."""

from __future__ import annotations

import base64
import gzip
import json

import pytest
from django.core.exceptions import ValidationError

from django_apps.asteroid_lab.admin_lab_sprites import (
    lab_sprite_relpath_from_tile_type,
    lab_sprite_resolve,
    normalize_lab_rotation_q,
)
from django_apps.asteroid_lab.lab_screen_grid import sprite_rotation_deg_from_quarter
from django_apps.asteroid_lab.models import GeneticSample
from django_apps.shapez_core.models import ShapezBasedataRelease


def _encode_v4_copy(root: dict) -> str:
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(text)
    b64 = base64.b64encode(gz).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


@pytest.mark.django_db
def test_lab_sprite_relpath_space_pipe_left_turn(
    lab_sprite_identifiers_for_admin: ShapezBasedataRelease,
) -> None:
    expected = "SpacePipe/SpacePipe_LeftTurn.svg"
    assert lab_sprite_relpath_from_tile_type("SpacePipe_LeftTurn") == expected


@pytest.mark.django_db
def test_lab_sprite_relpath_space_pipe_right_turn(
    lab_sprite_identifiers_for_admin: ShapezBasedataRelease,
) -> None:
    assert lab_sprite_relpath_from_tile_type("SpacePipe_RightTurn") == (
        "SpacePipe/SpacePipe_RightTurn.svg"
    )


@pytest.mark.django_db
def test_lab_sprite_relpath_space_pipe_left_fwd_splitter(
    lab_sprite_identifiers_for_admin: ShapezBasedataRelease,
) -> None:
    assert (
        lab_sprite_relpath_from_tile_type("SpacePipe_LeftFwdSplitter")
        == "SpacePipe/SpacePipe_LeftFwdSplitter.svg"
    )


def test_normalize_lab_rotation_q() -> None:
    assert normalize_lab_rotation_q(None) == 0
    assert normalize_lab_rotation_q(3) == 3
    assert normalize_lab_rotation_q(-1) == 3
    assert normalize_lab_rotation_q(7) == 3


def test_sprite_rotation_deg_from_quarter_matches_normalize() -> None:
    for r in (0, 1, 2, 3, -1, 9):
        assert sprite_rotation_deg_from_quarter(r) == normalize_lab_rotation_q(r) * 90


def test_lab_sprite_relpath_layout_pro_miner_without_db() -> None:
    assert lab_sprite_relpath_from_tile_type("Layout_ProMiner") == ("Miner/Layout_ShapeMiner.svg")


@pytest.mark.django_db
def test_lab_sprite_resolve_uses_t_and_r(
    lab_sprite_identifiers_for_admin: ShapezBasedataRelease,
) -> None:
    rel, q = lab_sprite_resolve(
        tile_type="SpacePipe_Forward",
        cell_kind="space_pipe",
        rotation=3,
    )
    assert rel == "SpacePipe/SpacePipe_Forward.svg"
    assert q == 3


def test_genetic_sample_clean_decodes_with_dollar_suffix() -> None:
    root = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [{"X": 1, "Y": 0, "T": "SpacePipe_Forward", "R": 0}],
        },
    }
    encoded = _encode_v4_copy(root) + "$"
    sample = GeneticSample(name="t", code=encoded)
    sample.full_clean()
    assert sample.decoded_json.get("V") == 1
    bp = sample.decoded_json.get("BP")
    assert isinstance(bp, dict)
    entries = bp.get("Entries")
    assert isinstance(entries, list) and len(entries) == 1
    meta = sample.decoded_json.get("_asteroid_lab_coord_system")
    assert isinstance(meta, dict)
    assert meta.get("frame") == "island_raw"
    row = entries[0]
    assert row.get("X") == 1 and row.get("Y") == 0
    assert "server_x" not in row and "server_y" not in row


def test_genetic_sample_clean_invalid_code() -> None:
    sample = GeneticSample(name="x", code="SHAPEZ2-4-!!!!")
    with pytest.raises(ValidationError):
        sample.full_clean()


@pytest.mark.django_db
def test_genetic_sample_save_populates_decoded_json() -> None:
    root = {
        "V": 2,
        "BP": {"$type": "Island", "Entries": []},
    }
    sample = GeneticSample(code=_encode_v4_copy(root))
    sample.save()
    sample.refresh_from_db()
    assert sample.decoded_json.get("V") == 2
