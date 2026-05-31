"""Shim + test-fixture loaders for reconstruction topology (PR-CLI-2f).

The pure algorithm (decode + topology set construction + diffs) is relocated to
``shapez2_factory.domain.asteroid_lab.reconstruction.topology_contract`` and re-exported here.
The fixture-file loaders stay Django-side because they read ``tests/fixtures`` paths, which a
pure core module must not reach into.
"""

from __future__ import annotations

from pathlib import Path

from shapez2_factory.domain.asteroid_lab.reconstruction.topology_contract import (
    NormalizedReconstructionTopology,
    build_normalized_reconstruction_topology,
    decode_shapez_copy_string,
    diff_topology,
    normalize_topology_for_compare,
    raw_coords_from_snapshot,
    topology_diff_is_empty,
)

_DEFAULT_FIXTURES_DIR = Path(__file__).resolve().parents[3] / "tests" / "fixtures" / "asteroid_lab"


def _fixtures_dir(fixtures_dir: Path | None) -> Path:
    return fixtures_dir if fixtures_dir is not None else _DEFAULT_FIXTURES_DIR


def load_shapez_copy_string_fixture_lines(path: Path | str) -> tuple[str, ...]:
    """All non-empty lines; trailing ``$`` stripped."""

    text = Path(path).read_text(encoding="utf-8")
    return tuple(ln.strip().removesuffix("$") for ln in text.splitlines() if ln.strip())


def load_shapez_copy_string_fixture(path: Path | str) -> str:
    """First non-empty line (single-map helper)."""

    lines = load_shapez_copy_string_fixture_lines(path)
    if not lines:
        msg = f"fixture has no copy string lines: {path}"
        raise ValueError(msg)
    return lines[0]


def load_reconstruction_fixture_line_pairs(
    required_name: str = "reconstruction_required_.txt",
    solved_name: str = "reconstruction_complete_solved.txt",
    *,
    fixtures_dir: Path | None = None,
) -> tuple[tuple[str, str], ...]:
    """``(required_copy, solved_copy)`` per line index."""

    base = _fixtures_dir(fixtures_dir)
    req_lines = load_shapez_copy_string_fixture_lines(base / required_name)
    sol_lines = load_shapez_copy_string_fixture_lines(base / solved_name)
    if len(req_lines) != len(sol_lines):
        msg = (
            f"fixture line count mismatch: {required_name} has {len(req_lines)} lines, "
            f"{solved_name} has {len(sol_lines)} lines"
        )
        raise ValueError(msg)
    return tuple(zip(req_lines, sol_lines, strict=True))


__all__ = [
    "NormalizedReconstructionTopology",
    "build_normalized_reconstruction_topology",
    "decode_shapez_copy_string",
    "diff_topology",
    "load_reconstruction_fixture_line_pairs",
    "load_shapez_copy_string_fixture",
    "load_shapez_copy_string_fixture_lines",
    "normalize_topology_for_compare",
    "raw_coords_from_snapshot",
    "topology_diff_is_empty",
]
