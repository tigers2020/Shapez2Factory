"""Guardrails: asteroid lab services must not depend on mining solver packages."""

from __future__ import annotations

from pathlib import Path


def test_services_python_files_avoid_mining_solver_paths() -> None:
    root = Path(__file__).resolve().parents[3] / "django_apps" / "asteroid_lab" / "services"
    forbidden_substrings = (
        "django_apps.shapez_asteroid",
        "asteroid_mining_layout_v2",
        "asteroid_mining_layout_v1",
    )
    for path in sorted(root.glob("*.py")):
        text = path.read_text(encoding="utf-8")
        for bad in forbidden_substrings:
            assert bad not in text, f"{path.name} must not mention {bad!r}"
