from __future__ import annotations

import base64
import gzip
import json

from django.test import Client, override_settings

from django_apps.shapez_asteroid.services.style_classifier import asteroid_map_style_catalog
from django_apps.shapez_core.services.shapez_copy_decode import SHAPEZ2_COPY_PREFIX_V4


def _encode_copy(obj: object) -> str:
    body = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    compressed = gzip.compress(body)
    b64 = base64.b64encode(compressed).decode("ascii")
    return f"{SHAPEZ2_COPY_PREFIX_V4}{b64}"


def _post_json(client: Client, payload: dict) -> object:
    token = client.cookies.get("csrftoken")
    assert token is not None
    return client.post(
        "/api/asteroid/copy-preview/",
        data=json.dumps(payload),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token.value,
    )


def test_copy_preview_success() -> None:
    client = Client()
    client.get("/asteroid/")
    data = {
        "V": 1,
        "BP": {
            "$type": "Island",
            "Entries": [{"X": 1, "Y": 2, "T": "Layout_ShapeMiner"}],
        },
    }
    response = _post_json(client, {"code": _encode_copy(data)})

    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["summary"] == {
        "entry_count": 1,
        "x_min": 1,
        "x_max": 1,
        "y_min": 2,
        "y_max": 2,
    }
    assert body["mining_map"] == [
        {"x": 1, "y": 2, "role": "occupied", "surface": "shape", "t": "Layout_ShapeMiner"},
    ]
    assert body["style_catalog"] == asteroid_map_style_catalog()
    assert "occupied" in body["style_catalog"]
    assert "inferred" in body["style_catalog"]


def test_copy_preview_unknown_t_zero_extraction() -> None:
    client = Client()
    client.get("/asteroid/")
    data = {
        "V": 1,
        "BP": {"$type": "Island", "Entries": [{"X": 1, "Y": 2, "T": "t"}]},
    }
    response = _post_json(client, {"code": _encode_copy(data)})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["summary"]["entry_count"] == 0
    assert body["mining_map"] == []
    assert "style_catalog" in body


def test_copy_preview_invalid_copy() -> None:
    client = Client()
    client.get("/asteroid/")
    response = _post_json(client, {"code": "SHAPEZ2-4-@@@@"})

    assert response.status_code == 400
    assert response.json()["ok"] is False


def test_copy_preview_invalid_json() -> None:
    client = Client()
    client.get("/asteroid/")
    token = client.cookies.get("csrftoken")
    assert token is not None
    response = client.post(
        "/api/asteroid/copy-preview/",
        data="{",
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token.value,
    )

    assert response.status_code == 400
    assert response.json()["error"] == "invalid json"


def test_copy_preview_code_not_string() -> None:
    client = Client()
    client.get("/asteroid/")
    response = _post_json(client, {"code": 1})

    assert response.status_code == 400
    assert response.json()["error"] == "code must be a string"


def test_copy_preview_debug_dump_writes_encrypt_and_json(tmp_path) -> None:
    client = Client()
    client.get("/asteroid/")
    data = {
        "V": 1,
        "BP": {"$type": "Island", "Entries": [{"X": 1, "Y": 2, "T": "Layout_ShapeMiner"}]},
    }
    code = _encode_copy(data)
    with override_settings(SHAPEZ_COPY_DEBUG_DIR=str(tmp_path)):
        response = _post_json(client, {"code": code})

    assert response.status_code == 200
    txt_files = sorted(tmp_path.glob("copy_preview_*_encrypt_code.txt"))
    json_files = sorted(tmp_path.glob("copy_preview_*_decoded.json"))
    assert len(txt_files) == 1
    assert len(json_files) == 1
    assert txt_files[0].read_text(encoding="utf-8").strip() == code.strip()
    saved = json.loads(json_files[0].read_text(encoding="utf-8"))
    assert saved == data
