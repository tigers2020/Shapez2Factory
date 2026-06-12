"""Resolve pinned Tier B dump and Tier A import source paths for pytest."""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]

# Canon per runbook; legacy checkout keeps dump under documents/knowledge/raw/.
_GAME_DATA_DUMP_CANDIDATES: tuple[Path, ...] = (
    _REPO_ROOT / "game_data_backup" / "game_data_dump.json",
    _REPO_ROOT / "documents" / "knowledge" / "raw" / "game_data_backup" / "game_data_dump.json",
)

_GAME_DATA_SOURCE_CANDIDATES: tuple[Path, ...] = (
    _REPO_ROOT / "documents" / "game_data",
    _REPO_ROOT / "documents" / "knowledge" / "raw" / "game_data",
)


def resolve_game_data_dump_path() -> Path | None:
    for path in _GAME_DATA_DUMP_CANDIDATES:
        if path.is_file():
            return path
    return None


def resolve_game_data_source_dir() -> Path | None:
    for path in _GAME_DATA_SOURCE_CANDIDATES:
        if (path / "manifest.json").is_file():
            return path
    return None


__all__ = ["resolve_game_data_dump_path", "resolve_game_data_source_dir"]
