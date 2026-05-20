"""Unit tests for ``config.shapez_runtime_flags`` path resolution."""

from __future__ import annotations

from pathlib import Path

from config.shapez_runtime_flags import resolve_path_from_env

_BASE = Path("/repo")


def test_resolve_path_from_env_empty_uses_default() -> None:
    assert resolve_path_from_env("", base_dir=_BASE, default=_BASE / ".graph_preview_cache") == (
        _BASE / ".graph_preview_cache"
    )


def test_resolve_path_from_env_relative_under_base() -> None:
    assert resolve_path_from_env(
        "var/foo",
        base_dir=_BASE,
        default=_BASE / ".graph_preview_cache",
    ) == (_BASE / "var" / "foo")


def test_resolve_path_from_env_absolute_unchanged(tmp_path: Path) -> None:
    abs_path = (tmp_path / "preview_cache").resolve()
    abs_path.mkdir()
    assert (
        resolve_path_from_env(
            str(abs_path),
            base_dir=_BASE,
            default=_BASE / ".graph_preview_cache",
        )
        == abs_path
    )
