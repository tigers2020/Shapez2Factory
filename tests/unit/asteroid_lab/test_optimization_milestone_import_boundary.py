from __future__ import annotations

from pathlib import Path


def test_optimization_package_does_not_import_replay_read_adapters() -> None:
    root = Path(__file__).resolve().parents[3]
    opt_dir = root / "django_apps" / "asteroid_lab" / "optimization"
    forbidden = (
        "lab_optimization_milestone_payload",
        "lab_unified_replay_append",
        "lab_replay_timeline_payload",
    )
    for path in opt_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for needle in forbidden:
            assert needle not in text, f"{path} must not import replay read adapter {needle!r}"
