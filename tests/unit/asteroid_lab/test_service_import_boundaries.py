"""Guardrails: asteroid lab services must not depend on mining solver packages."""

from __future__ import annotations

from pathlib import Path


def _iter_lab_py_files(lab_root: Path) -> list[Path]:
    roots = (
        lab_root / "services",
        lab_root / "adapters",
        lab_root / "replay",
    )
    paths: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.py")):
            if "__pycache__" in path.parts:
                continue
            paths.append(path)
    return paths


def test_services_python_files_avoid_mining_solver_paths() -> None:
    lab_root = Path(__file__).resolve().parents[3] / "django_apps" / "asteroid_lab"
    forbidden_substrings = (
        "django_apps.shapez_asteroid",
        "django_apps.shapez_solver",
        "django_apps.shapez_core",
        "asteroid_mining_layout_v2",
        "asteroid_mining_layout_v1",
    )
    for path in _iter_lab_py_files(lab_root):
        text = path.read_text(encoding="utf-8")
        for bad in forbidden_substrings:
            rel = path.relative_to(lab_root)
            assert bad not in text, f"{rel.as_posix()} must not mention {bad!r}"
