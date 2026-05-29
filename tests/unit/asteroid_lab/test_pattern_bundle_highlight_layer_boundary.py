"""pattern_bundle_highlight must stay off solver optimization import paths."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
STACK_RUNNER = REPO / "django_apps" / "asteroid_lab" / "layers" / "stack_runner.py"


def test_stack_runner_does_not_import_pattern_bundle_highlight() -> None:
    source = STACK_RUNNER.read_text(encoding="utf-8")
    assert "pattern_bundle_highlight" not in source
