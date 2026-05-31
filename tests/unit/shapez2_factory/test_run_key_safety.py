"""TDD for Guard C ??run_key + artifact-root safety.

Verifies that ``resolve_artifact_dir`` rejects unsafe run_keys and any
artifact_root that does not actually nest under the allowed_root, using
``Path.relative_to`` containment (not string prefix matching).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from shapez2_factory.adapters.asteroid_lab.run_key_safety import (
    ArtifactPathError,
    resolve_artifact_dir,
)


def test_valid_run_key_resolves_under_root(tmp_path: Path) -> None:
    allowed_root = tmp_path / "runs"
    allowed_root.mkdir()
    artifact_root = allowed_root

    result = resolve_artifact_dir(allowed_root, artifact_root, "run-abc_1.2")

    assert result == (allowed_root / "run-abc_1.2").resolve()


def test_rejects_dot_and_dotdot(tmp_path: Path) -> None:
    allowed_root = tmp_path / "runs"
    allowed_root.mkdir()

    for bad in (".", ".."):
        with pytest.raises(ArtifactPathError):
            resolve_artifact_dir(allowed_root, allowed_root, bad)


def test_rejects_path_separators(tmp_path: Path) -> None:
    allowed_root = tmp_path / "runs"
    allowed_root.mkdir()

    for bad in ("a/b", "a\\b"):
        with pytest.raises(ArtifactPathError):
            resolve_artifact_dir(allowed_root, allowed_root, bad)


def test_rejects_invalid_chars(tmp_path: Path) -> None:
    allowed_root = tmp_path / "runs"
    allowed_root.mkdir()

    for bad in ("a b", "a$b"):
        with pytest.raises(ArtifactPathError):
            resolve_artifact_dir(allowed_root, allowed_root, bad)


def test_rejects_trailing_newline_and_control_chars(tmp_path: Path) -> None:
    allowed_root = tmp_path / "runs"
    allowed_root.mkdir()

    for bad in ("abc\n", ""):
        with pytest.raises(ArtifactPathError):
            resolve_artifact_dir(allowed_root, allowed_root, bad)


def test_run_key_safety_rejects_sibling_prefix_dir(tmp_path: Path) -> None:
    # artifact_root ("runs2") shares the "runs" string prefix with allowed_root
    # but is NOT nested under it. A naive str.startswith check would wrongly
    # accept this; relative_to containment correctly rejects it.
    allowed_root = tmp_path / "runs"
    allowed_root.mkdir()
    artifact_root = tmp_path / "runs2"
    artifact_root.mkdir()

    with pytest.raises(ArtifactPathError):
        resolve_artifact_dir(allowed_root, artifact_root, "run-abc_1.2")
