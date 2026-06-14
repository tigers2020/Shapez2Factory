"""GameDataBundleGate — path resolve and fail-closed integrity checks."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from django_apps.game_data.importers.source_loader import sha256_file
from django_apps.game_data.services.bundle_gate import (
    GameDataBundleInvalid,
    GameDataBundleInvalidCode,
    resolve_game_data_source_dir,
    validate_game_data_bundle,
)
from tests.unit.game_data.dump_paths import resolve_game_data_source_dir as resolve_for_tests


def test_resolve_game_data_source_dir_auto_finds_tracked_bundle() -> None:
    source = resolve_for_tests()
    assert source is not None
    resolved = resolve_game_data_source_dir(explicit=None)
    assert resolved == source
    assert (resolved / "manifest.json").is_file()


def test_validate_game_data_bundle_passes_tracked_bundle() -> None:
    source = resolve_for_tests()
    if source is None:
        pytest.skip("game_data bundle not present")

    bundle = validate_game_data_bundle(source=source)
    assert bundle.source_dir == source.resolve()
    assert bundle.manifest_hash.startswith("sha256:")
    assert isinstance(bundle.manifest.get("file_hashes"), dict)


def test_validate_game_data_bundle_rejects_hash_mismatch(tmp_path: Path) -> None:
    source = resolve_for_tests()
    if source is None:
        pytest.skip("game_data bundle not present")

    bundle_copy = tmp_path / "bundle"
    bundle_copy.mkdir()
    for item in source.iterdir():
        if item.is_file():
            bundle_copy.joinpath(item.name).write_bytes(item.read_bytes())

    bad_file = bundle_copy / "fluids.json"
    assert bad_file.is_file()
    bad_file.write_text('["corrupt"]', encoding="utf-8")

    with pytest.raises(GameDataBundleInvalid) as exc_info:
        validate_game_data_bundle(source=bundle_copy)

    assert exc_info.value.code == GameDataBundleInvalidCode.FILE_HASH_MISMATCH
    assert "fluids.json" in str(exc_info.value)


def test_validate_game_data_bundle_allows_incomplete_missing(tmp_path: Path) -> None:
    manifest = {
        "dump_timestamp_utc": "2026-01-01T00:00:00Z",
        "file_hashes": {
            "present.json": sha256_file.__doc__,  # placeholder replaced below
        },
        "incomplete_sections": ["missing.json"],
    }
    present = tmp_path / "present.json"
    present.write_text("{}", encoding="utf-8")
    manifest["file_hashes"]["present.json"] = sha256_file(present)
    manifest_path = tmp_path / "manifest.json"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    bundle = validate_game_data_bundle(source=tmp_path)
    assert bundle.manifest_hash == sha256_file(manifest_path)


def test_validate_game_data_bundle_rejects_missing_not_incomplete(tmp_path: Path) -> None:
    present = tmp_path / "present.json"
    present.write_text("{}", encoding="utf-8")
    manifest = {
        "dump_timestamp_utc": "2026-01-01T00:00:00Z",
        "file_hashes": {
            "present.json": sha256_file(present),
            "gone.json": "sha256:deadbeef",
        },
        "incomplete_sections": [],
    }
    (tmp_path / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(GameDataBundleInvalid) as exc_info:
        validate_game_data_bundle(source=tmp_path)

    assert exc_info.value.code == GameDataBundleInvalidCode.FILE_MISSING
    assert "gone.json" in str(exc_info.value)


def test_resolve_game_data_source_dir_explicit_missing_manifest(tmp_path: Path) -> None:
    with pytest.raises(GameDataBundleInvalid) as exc_info:
        resolve_game_data_source_dir(explicit=tmp_path)

    assert exc_info.value.code == GameDataBundleInvalidCode.BUNDLE_NOT_FOUND
