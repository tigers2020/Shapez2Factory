"""Guardrails: asteroid lab services must not depend on mining solver packages."""

from __future__ import annotations

from pathlib import Path


def test_services_python_files_avoid_mining_solver_paths() -> None:
    lab_root = Path(__file__).resolve().parents[3] / "django_apps" / "asteroid_lab"
    roots = (
        lab_root / "services",
        lab_root / "adapters",
    )
    forbidden_substrings = (
        "django_apps.shapez_asteroid",
        "django_apps.shapez_solver",
        "django_apps.shapez_core",
        "asteroid_mining_layout_v2",
        "asteroid_mining_layout_v1",
    )
    for root in roots:
        for path in sorted(root.glob("*.py")):
            text = path.read_text(encoding="utf-8")
            for bad in forbidden_substrings:
                rel = path.relative_to(lab_root)
                assert bad not in text, f"{rel.as_posix()} must not mention {bad!r}"
