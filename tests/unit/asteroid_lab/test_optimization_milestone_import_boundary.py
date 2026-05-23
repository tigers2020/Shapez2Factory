from __future__ import annotations

from pathlib import Path


def test_optimization_package_does_not_import_milestone_payload() -> None:
    root = Path(__file__).resolve().parents[3]
    opt_dir = root / "django_apps" / "asteroid_lab" / "optimization"
    needle = "lab_optimization_milestone_payload"
    for path in opt_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert needle not in text, f"{path} must not import milestone read adapter"
