"""Validate a game_data JSON bundle on disk before any ORM import."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from django.conf import settings

from django_apps.game_data.importers.source_loader import load_json, sha256_file

GAME_DATA_SOURCE_CANDIDATES: tuple[str, ...] = (
    "documents/game_data",
    "documents/knowledge/raw/game_data",
)


class GameDataBundleInvalidCode(StrEnum):
    BUNDLE_NOT_FOUND = "bundle_not_found"
    MANIFEST_INVALID = "manifest_invalid"
    FILE_MISSING = "file_missing"
    FILE_HASH_MISMATCH = "file_hash_mismatch"


class GameDataBundleInvalid(Exception):
    def __init__(self, code: GameDataBundleInvalidCode, message: str) -> None:
        self.code = code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class GameDataBundle:
    source_dir: Path
    manifest: dict[str, object]
    manifest_hash: str


def _repo_root() -> Path:
    return Path(settings.BASE_DIR)


def resolve_game_data_source_dir(*, explicit: Path | None = None) -> Path:
    """Resolve bundle directory from explicit path or repo-standard candidates."""

    if explicit is not None:
        source = explicit.resolve()
        if not (source / "manifest.json").is_file():
            msg = f"manifest.json not found in {source}"
            raise GameDataBundleInvalid(GameDataBundleInvalidCode.BUNDLE_NOT_FOUND, msg)
        return source

    root = _repo_root()
    for rel in GAME_DATA_SOURCE_CANDIDATES:
        candidate = (root / rel).resolve()
        if (candidate / "manifest.json").is_file():
            return candidate

    tried = ", ".join(str(root / rel) for rel in GAME_DATA_SOURCE_CANDIDATES)
    msg = f"no game_data bundle found; tried: {tried}"
    raise GameDataBundleInvalid(GameDataBundleInvalidCode.BUNDLE_NOT_FOUND, msg)


def validate_game_data_bundle(*, source: Path | None = None) -> GameDataBundle:
    """Load manifest and verify file_hashes integrity (fail-closed)."""

    source_dir = resolve_game_data_source_dir(explicit=source)
    manifest_path = source_dir / "manifest.json"
    manifest_hash = sha256_file(manifest_path)

    raw = load_json(manifest_path)
    if not isinstance(raw, dict):
        msg = "manifest.json must be a JSON object"
        raise GameDataBundleInvalid(GameDataBundleInvalidCode.MANIFEST_INVALID, msg)

    file_hashes = raw.get("file_hashes")
    if not isinstance(file_hashes, dict):
        msg = "manifest.json missing file_hashes object"
        raise GameDataBundleInvalid(GameDataBundleInvalidCode.MANIFEST_INVALID, msg)

    incomplete_sections = {str(section) for section in (raw.get("incomplete_sections") or [])}

    missing_errors: list[str] = []
    mismatch_errors: list[str] = []
    for filename, expected in file_hashes.items():
        name = str(filename)
        expected_hash = str(expected)
        fpath = source_dir / name
        if not fpath.is_file():
            if name in incomplete_sections:
                continue
            missing_errors.append(f"{name}: missing (not in incomplete_sections)")
            continue
        actual_hash = sha256_file(fpath)
        if actual_hash != expected_hash:
            mismatch_errors.append(
                f"{name}: hash mismatch (expected {expected_hash!r}, got {actual_hash!r})"
            )

    if mismatch_errors or missing_errors:
        errors = mismatch_errors + missing_errors
        code = (
            GameDataBundleInvalidCode.FILE_HASH_MISMATCH
            if mismatch_errors
            else GameDataBundleInvalidCode.FILE_MISSING
        )
        msg = "game_data bundle integrity failed:\n  " + "\n  ".join(errors)
        raise GameDataBundleInvalid(code, msg)

    return GameDataBundle(
        source_dir=source_dir,
        manifest=raw,
        manifest_hash=manifest_hash,
    )


__all__ = [
    "GAME_DATA_SOURCE_CANDIDATES",
    "GameDataBundle",
    "GameDataBundleInvalid",
    "GameDataBundleInvalidCode",
    "resolve_game_data_source_dir",
    "validate_game_data_bundle",
]
