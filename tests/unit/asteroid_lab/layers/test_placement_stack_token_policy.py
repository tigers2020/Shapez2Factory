"""placement_stack forbidden token policy."""

from __future__ import annotations

from pathlib import Path

_TOKEN = "placement_stack"


def test_placement_stack_token_forbidden_in_runtime_code() -> None:
    root = Path("django_apps/asteroid_lab")
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert _TOKEN not in text, f"forbidden token in {path}"


def test_placement_stack_token_forbidden_in_current_plan() -> None:
    path = Path("documents/ai/current_plan.md")
    text = path.read_text(encoding="utf-8")
    assert _TOKEN not in text, "forbidden token in current_plan.md"
