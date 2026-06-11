"""Decode regression for frozen inner quad template fixtures (T1–T4, Q1–Q4)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from shapez2_factory.domain.asteroid_lab.copy_decode import decode_copy_string

_FIXTURE_ROOT = (
    Path(__file__).resolve().parents[2] / "fixtures" / "asteroid_lab" / "inner_quad_templates"
)
_MANIFEST_PATH = _FIXTURE_ROOT / "manifest.json"


def _load_manifest() -> dict[str, Any]:
    return json.loads(_MANIFEST_PATH.read_text(encoding="utf-8"))


def _classify_entries(entries: list[dict[str, Any]]) -> tuple[int, int, int, set[str]]:
    miner_count = 0
    extension_count = 0
    transport_count = 0
    transport_types: set[str] = set()
    for entry in entries:
        kind = entry.get("T", "")
        if kind == "Layout_ShapeMiner":
            miner_count += 1
        elif kind == "Layout_ShapeMinerExtension":
            extension_count += 1
        else:
            transport_count += 1
            transport_types.add(kind)
    return miner_count, extension_count, transport_count, transport_types


def _template_ids() -> tuple[str, ...]:
    manifest = _load_manifest()
    return tuple(sorted(manifest["templates"].keys()))


@pytest.mark.parametrize("template_id", _template_ids())
def test_inner_quad_template_decodes_to_manifest_counts(template_id: str) -> None:
    manifest = _load_manifest()
    spec = manifest["templates"][template_id]
    copy_path = _FIXTURE_ROOT / spec["copy_file"]
    assert copy_path.is_file(), f"missing fixture {copy_path}"

    copy_text = copy_path.read_text(encoding="utf-8").strip()
    root = decode_copy_string(copy_text).root
    assert "BP" in root
    bp = root["BP"]
    assert bp.get("$type") == "Island"
    entries = bp["Entries"]
    assert isinstance(entries, list)

    miners, extensions, transport, transport_types = _classify_entries(entries)
    assert miners == spec["miner_count"]
    assert extensions == spec["extension_count"]
    assert transport == spec["transport_count"]
    assert len(entries) == spec["entry_count"]
    assert transport_types == set(spec["transport_types"])


def test_inner_quad_manifest_covers_eight_templates() -> None:
    manifest = _load_manifest()
    assert manifest["schema_version"] == "inner_quad_template_v1"
    assert set(manifest["templates"]) == {"T1", "T2", "T3", "T4", "Q1", "Q2", "Q3", "Q4"}


def test_q_family_templates_include_extensions() -> None:
    manifest = _load_manifest()
    for template_id in ("Q1", "Q2", "Q3", "Q4"):
        assert manifest["templates"][template_id]["extension_count"] > 0


def test_t_family_templates_are_junction_only() -> None:
    manifest = _load_manifest()
    for template_id in ("T1", "T2", "T3", "T4"):
        assert manifest["templates"][template_id]["extension_count"] == 0
