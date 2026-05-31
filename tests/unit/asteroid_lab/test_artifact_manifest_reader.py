"""Django-side artifact manifest reader gates."""

from __future__ import annotations

import ast
import hashlib
import json
from pathlib import Path

import pytest

from django_apps.asteroid_lab.services import artifact_manifest_reader as reader

_MODULE_PATH = (
    Path(__file__).resolve().parents[3]
    / "django_apps"
    / "asteroid_lab"
    / "services"
    / "artifact_manifest_reader.py"
)


def _manifest_payload(*, lifecycle_status: str = "artifact_written") -> dict[str, object]:
    return {
        "schema_version": 1,
        "run_key": "run-1",
        "lifecycle_status": lifecycle_status,
        "created_at_utc": "2026-05-30T00:00:00Z",
        "core_build_id": "test",
        "content_hashes": {},
        "paths": {},
        "game_data_provenance": {},
        "error_code": None,
    }


def test_artifact_manifest_reader_imports_no_core_modules() -> None:
    tree = ast.parse(_MODULE_PATH.read_text(encoding="utf-8-sig"))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("shapez2_factory"):
                offenders.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("shapez2_factory"):
                    offenders.append(alias.name)
    assert offenders == []


def test_read_verified_artifact_manifest_accepts_hashed_payload(tmp_path: Path) -> None:
    output = tmp_path / "output" / "solver_summary.json"
    output.parent.mkdir(parents=True)
    output.write_text('{"ok": true}\n', encoding="utf-8")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    payload = _manifest_payload()
    payload["content_hashes"] = {"output/solver_summary.json": digest}
    (tmp_path / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")

    manifest = reader.read_verified_artifact_manifest(tmp_path)

    assert manifest.run_key == "run-1"
    assert manifest.lifecycle_status == "artifact_written"
    assert manifest.content_hashes == {"output/solver_summary.json": digest}


@pytest.mark.parametrize(  # type: ignore[untyped-decorator]
    ("field", "value", "match"),
    [
        ("schema_version", 2, "unsupported manifest schema_version"),
        ("lifecycle_status", "PARTIAL", "lifecycle_status"),
        ("content_hashes", {"manifest.json": "abc"}, "manifest.json"),
    ],
)
def test_parse_manifest_payload_rejects_invalid_contract(
    field: str,
    value: object,
    match: str,
) -> None:
    payload = _manifest_payload()
    payload[field] = value

    with pytest.raises(reader.ArtifactManifestReadError, match=match):
        reader.parse_artifact_manifest_payload(payload)


def test_read_verified_artifact_manifest_rejects_hash_mismatch(tmp_path: Path) -> None:
    output = tmp_path / "output" / "solver_summary.json"
    output.parent.mkdir(parents=True)
    output.write_text('{"ok": false}\n', encoding="utf-8")
    payload = _manifest_payload()
    payload["content_hashes"] = {"output/solver_summary.json": "0" * 64}
    (tmp_path / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(reader.ArtifactManifestReadError, match="hash mismatch"):
        reader.read_verified_artifact_manifest(tmp_path)


def test_read_verified_artifact_manifest_rejects_escaped_payload(tmp_path: Path) -> None:
    payload = _manifest_payload()
    payload["content_hashes"] = {"../outside.txt": "0" * 64}
    (tmp_path / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(reader.ArtifactManifestReadError, match="escapes artifact"):
        reader.read_verified_artifact_manifest(tmp_path)
