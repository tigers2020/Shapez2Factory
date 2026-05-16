"""Pure copy decode + normalization (A3); no mining v2 imports.

Real-world copy/decoded samples for humans live under ``var/asteroid_mining_layout_debug/``;
tests use only synthetic payloads built in this file.
"""

from __future__ import annotations

import base64
import gzip
import json

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.decode_adapter import (
    AsteroidLabCopyDecodeError,
    decode_copy_string,
)
from django_apps.asteroid_lab.adapters.normalization import normalize_decoded_blueprint
from django_apps.asteroid_lab.services import project_service
from django_apps.asteroid_lab.services.dto import RawDecodedBlueprintDTO
from django_apps.asteroid_lab.services.input_service import persist_decoded_snapshot


def _encode_v4_copy(root: dict) -> str:
    text = json.dumps(root, separators=(",", ":")).encode("utf-8")
    gz = gzip.compress(text)
    b64 = base64.b64encode(gz).decode("ascii")
    return f"SHAPEZ2-4-{b64}"


def test_decode_copy_string_roundtrip_minimal() -> None:
    root = {
        "V": 42,
        "BP": {"$type": "Island", "Entries": [{"X": 0, "Y": 0, "T": "SpacePipe_Forward"}]},
    }
    raw = decode_copy_string(_encode_v4_copy(root))
    assert raw.root["V"] == 42
    assert raw.root["BP"]["$type"] == "Island"
    assert len(raw.root["BP"]["Entries"]) == 1


def test_decode_copy_string_whitespace_stripped() -> None:
    root = {"V": 1, "BP": {"$type": "Island", "Entries": []}}
    encoded = _encode_v4_copy(root)
    body = encoded[len("SHAPEZ2-4-") :]
    spaced = "SHAPEZ2-4-\n" + body[:20] + "\n" + body[20:]
    raw = decode_copy_string(spaced)
    assert raw.root["V"] == 1


@pytest.mark.parametrize(
    ("bad", "msg_part"),
    [
        ("", "empty"),
        ("NOPE", "must start with"),
        ("SHAPEZ2-4-", "missing payload"),
        ("SHAPEZ2-4-!!!!", "invalid base64"),
    ],
)
def test_decode_copy_string_errors(bad: str, msg_part: str) -> None:
    with pytest.raises(AsteroidLabCopyDecodeError) as exc:
        decode_copy_string(bad)
    assert msg_part in str(exc.value).lower()


def test_decode_requires_bp_shape() -> None:
    root = {"V": 1, "BP": {"Entries": []}}
    with pytest.raises(AsteroidLabCopyDecodeError, match="\\$type"):
        decode_copy_string(_encode_v4_copy(root))


def test_normalize_summary_counts() -> None:
    root = {
        "V": 9,
        "BP": {
            "$type": "Island",
            "Entries": [
                {"X": 0, "Y": 0, "T": "Layout_ProMiner"},
                {"X": 0, "Y": 1, "T": "SpaceBelt_Left"},
                {"X": 0, "Y": 0, "T": "SpacePipe_Right"},
                {"X": 2, "Y": 0, "T": "Foo_MinerExtension_Bar"},
            ],
        },
    }
    raw = RawDecodedBlueprintDTO(root=root)
    norm = normalize_decoded_blueprint(raw)
    s = norm.decoded_json["_asteroid_lab_summary"]
    assert s["miner_count"] == 1
    assert s["belt_count"] == 1
    assert s["pipe_count"] == 1
    assert s["extension_count"] == 1
    assert s["entry_count"] == 4
    assert s["cell_count"] == 3
    assert s["bbox"]["width"] == 3
    assert s["bbox"]["height"] == 2


@pytest.mark.django_db
def test_persist_decoded_snapshot_updates_latest_map_input() -> None:
    root = {"V": 3, "BP": {"$type": "Island", "Entries": []}}
    code = _encode_v4_copy(root)
    dto_proj = project_service.create_project_from_copy_code(code, source_label="t")
    raw = decode_copy_string(code)
    norm = normalize_decoded_blueprint(raw)
    inp = persist_decoded_snapshot(dto_proj.project_id, norm)

    assert inp.id == dto_proj.map_input_id
    assert inp.source_kind == m.AsteroidMapInput.SourceKind.DECODED_JSON
    assert inp.decoded_json["_asteroid_lab_summary"]["binary_version"] == 3
