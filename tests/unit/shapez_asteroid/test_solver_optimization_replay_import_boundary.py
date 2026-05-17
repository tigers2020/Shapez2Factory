"""12F — shapez_solver must not consume persisted optimization replay (output-only boundary)."""

from __future__ import annotations

from pathlib import Path


def test_solver_does_not_read_persisted_replay() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    solver_dir = repo_root / "django_apps" / "shapez_solver"
    needles = (
        "optimization_replay_frames",
        "deserialize_optimization_replay_frames_from_json",
        "validate_optimization_replay_frame_list_payload",
    )
    for path in solver_dir.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for n in needles:
            assert n not in text, f"{path} must not reference persisted replay guard ({n!r})"
