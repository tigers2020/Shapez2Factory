"""copy-preview: v2-only ``map_timeline`` + sidecars (minimal contract)."""

from __future__ import annotations

import base64
import gzip
import importlib
import importlib.util
import json

import pytest
from django.test import Client
from django.urls import reverse

from django_apps.shapez_core.services.shapez_copy_decode import SHAPEZ2_COPY_PREFIX_V4

_v2_preview_tl_mod = importlib.import_module(
    "django_apps.shapez_asteroid.services.asteroid_mining_layout_v2.preview_reconstruction_timeline"
)


def _bp(entries: list[dict[str, object]]) -> dict[str, object]:
    return {"V": 1, "BP": {"Entries": entries}}


def _encode_copy(obj: object) -> str:
    body = json.dumps(obj, separators=(",", ":")).encode("utf-8")
    compressed = gzip.compress(body)
    b64 = base64.b64encode(compressed).decode("ascii")
    return f"{SHAPEZ2_COPY_PREFIX_V4}{b64}"


@pytest.mark.django_db
def test_copy_preview_v2_only_returns_sidecar_keys() -> None:
    code = _encode_copy(_bp([{"X": 1, "Y": 0, "T": "Layout_ShapeMiner"}]))
    url = reverse("shapez_asteroid:copy_preview")
    response = Client().post(
        url,
        data=json.dumps({"code": code}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.content.decode())
    assert data["ok"] is True
    assert data["mining_layout_engine"] == "v2"
    assert data["preview_schema_version"] == 2
    assert "reconstruction_summary" in data
    assert data["reconstruction_summary"]["mineable_placement_count"] >= 1
    ela = data["existing_layout_analysis"]
    assert ela["source_kind"] in ("raw_asteroid_field", "existing_shape_layout")

    mt = data["map_timeline"]
    assert isinstance(mt, list)
    assert len(mt) == 3 + len(_v2_preview_tl_mod.V2_PREVIEW_PLACEHOLDER_STEP_IDS)
    seen: set[str] = set()
    for fr in mt:
        assert isinstance(fr.get("id"), str)
        assert fr["id"] not in seen
        seen.add(fr["id"])
        mm = fr.get("mining_map")
        assert isinstance(mm, list)
        assert len(mm) >= 1
        for row in mm:
            assert isinstance(row.get("x"), int)
            assert isinstance(row.get("y"), int)
            assert isinstance(row.get("role"), str)
    assert [fr["id"] for fr in mt] == [
        "v2_recon_transport_shell",
        "v2_recon_interior_void",
        "v2_recon_mineable",
        *_v2_preview_tl_mod.V2_PREVIEW_PLACEHOLDER_STEP_IDS,
    ]
    for fr in mt[:3]:
        assert fr["summary"].get("preview_placeholder") is not True
    for fr in mt[3:]:
        assert fr["summary"].get("preview_placeholder") is True
    assert data["mining_map"] == mt[-1]["mining_map"]
    assert data["summary"] == mt[-1]["summary"]


@pytest.mark.django_db
def test_copy_preview_v2_include_solver_replay_without_v1_package_ok() -> None:
    if _v1_mining_layout_available():
        pytest.skip("v1 package present; degraded path not exercised")
    code = _encode_copy(_bp([{"X": 1, "Y": 0, "T": "Layout_ShapeMiner"}]))
    url = reverse("shapez_asteroid:copy_preview") + "?include_solver_replay=1"
    response = Client().post(
        url,
        data=json.dumps({"code": code}),
        content_type="application/json",
    )
    assert response.status_code == 200
    data = json.loads(response.content.decode())
    assert data["ok"] is True
    assert data.get("solver_layout_package_unavailable") is True
    assert "solver_replay" not in data


def _v1_mining_layout_available() -> bool:
    return (
        importlib.util.find_spec("django_apps.shapez_asteroid.services.asteroid_mining_layout")
        is not None
    )
