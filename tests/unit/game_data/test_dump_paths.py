"""Tier B dump and Tier A source path resolution."""

from __future__ import annotations

from pathlib import Path

from tests.unit.game_data.dump_paths import (
    resolve_game_data_dump_path,
    resolve_game_data_source_dir,
)

_REPO_ROOT = Path(__file__).resolve().parents[3]


def test_resolve_game_data_dump_path_finds_tracked_dump() -> None:
    path = resolve_game_data_dump_path()
    assert path is not None
    assert path.is_file()
    assert path.name == "game_data_dump.json"


def test_resolve_game_data_source_dir_finds_tracked_bundle() -> None:
    source = resolve_game_data_source_dir()
    assert source is not None
    assert (source / "manifest.json").is_file()
    assert source.is_relative_to(_REPO_ROOT)
