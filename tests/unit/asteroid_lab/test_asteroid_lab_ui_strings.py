"""Lab template must not ship GA placeholder stat card copy."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
TEMPLATE = (
    REPO / "django_apps" / "web" / "templates" / "web" / "asteroid_miner_layout_solver.html"
)
STAT_PARTIAL = (
    REPO / "django_apps" / "web" / "templates" / "web" / "partials" / "lab_stat_cards.html"
)

FORBIDDEN = (
    "Best score",
    "fitness weighted",
    "5 miners each",
    "4 miners each",
    "Belt groups",
    "Fluid groups",
)


@pytest.mark.parametrize("needle", FORBIDDEN)
def test_lab_solver_template_forbids_placeholder_card_copy(needle: str) -> None:
    text = TEMPLATE.read_text(encoding="utf-8") + STAT_PARTIAL.read_text(encoding="utf-8")
    assert needle not in text, f"forbidden placeholder {needle!r} still in Lab templates"
