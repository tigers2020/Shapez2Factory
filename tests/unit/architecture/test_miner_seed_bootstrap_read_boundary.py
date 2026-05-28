"""Bootstrap miner pattern file must only be read by the ingest management command."""

from __future__ import annotations

from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
_DJANGO_APPS = _REPO / "django_apps"
_BOOTSTRAP_NAME = "default_miner_pattern.txt"
_ALLOWED_READERS = {
    _REPO / "django_apps" / "asteroid_lab" / "management" / "commands" / "seed_miner_patterns.py",
}


def _py_files_under(root: Path) -> list[Path]:
    return [p for p in root.rglob("*.py") if p.is_file()]


def test_runtime_solver_paths_do_not_reference_bootstrap_file() -> None:
    violations: list[str] = []
    for path in _py_files_under(_DJANGO_APPS):
        if path in _ALLOWED_READERS:
            continue
        if "management" in path.parts and "commands" in path.parts:
            if path.name != "seed_miner_patterns.py":
                continue
        text = path.read_text(encoding="utf-8")
        if _BOOTSTRAP_NAME in text:
            violations.append(str(path.relative_to(_REPO)))
    assert violations == [], f"bootstrap file referenced outside ingest command: {violations}"
