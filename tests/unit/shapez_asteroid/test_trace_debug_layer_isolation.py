"""Regression: mining layout algorithm must not treat trace/NDJSON as primary inputs."""

from __future__ import annotations

import re
from pathlib import Path

_ALGO_REL = Path("django_apps/shapez_asteroid/services/asteroid_mining_layout")
_TRACE_PATH_MARKERS = ("latest.ndjson", "mining_layout_solver_trace.ndjson")
_TRACE_MODULE_ONLY = frozenset({"solver_trace.py"})
_SCRIPTS_PKG = re.compile(r"^\s*(from|import)\s+scripts(\.|$)")
_READ_TEXT_OPEN = re.compile(
    r'(\.open\(\s*["\']r["\']|open\([^)]+\b["\']r["\']|read_text\()',
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def test_algorithm_tree_does_not_embed_trace_output_path_literals() -> None:
    """Only ``solver_trace`` may name canonical NDJSON sink files (append / truncate / prune)."""

    root = _repo_root() / _ALGO_REL
    assert root.is_dir(), root
    offenders: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if path.name in _TRACE_MODULE_ONLY:
            continue
        text = path.read_text(encoding="utf-8")
        for marker in _TRACE_PATH_MARKERS:
            if marker in text:
                offenders.append(f"{path.relative_to(_repo_root())}: contains {marker!r}")
    assert not offenders, "\n".join(offenders)


def test_algorithm_tree_does_not_import_scripts_package() -> None:
    """``scripts/`` readers stay CLI-only; no reverse dependency into ``django_apps``."""

    root = _repo_root() / _ALGO_REL
    bad: list[str] = []
    for path in sorted(root.rglob("*.py")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if _SCRIPTS_PKG.match(stripped):
                bad.append(f"{path.relative_to(_repo_root())}:{line_no}:{stripped}")
    assert not bad, "\n".join(bad)


def test_algorithm_tree_avoids_textual_reads_of_trace_files() -> None:
    """Block NDJSON reads via ``read_text`` / ``open(..., 'r')`` outside ``solver_trace``."""

    root = _repo_root() / _ALGO_REL
    bad: list[str] = []
    for path in sorted(root.rglob("*.py")):
        if path.name in _TRACE_MODULE_ONLY:
            continue
        for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if _READ_TEXT_OPEN.search(line):
                bad.append(f"{path.relative_to(_repo_root())}:{line_no}:{stripped}")
    assert not bad, "\n".join(bad)
