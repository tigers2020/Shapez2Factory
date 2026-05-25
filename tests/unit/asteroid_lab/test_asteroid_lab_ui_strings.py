"""Lab template must not ship GA placeholder stat card copy."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
TEMPLATE = REPO / "django_apps" / "web" / "templates" / "web" / "asteroid_miner_layout_solver.html"
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


def test_lab_js_maps_throughput_target_shortfall_to_gettext_msgid() -> None:
    js = (
        REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    ).read_text(encoding="utf-8")
    assert "formatLabIssueCodeLabel" in js
    assert 'throughput_target_shortfall: "throughput target shortfall"' in js


def test_throughput_target_slider_in_extractor_constraints_not_header() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    assert 'id="lab-throughput-target-percent"' in template
    assert template.index("Extractor Constraints") < template.index("lab-throughput-target-percent")
    header_end = template.index("</div>", template.index("lab-header-run"))
    assert template.index("lab-throughput-target-percent") > header_end


@pytest.mark.parametrize("needle", FORBIDDEN)
def test_lab_solver_template_forbids_placeholder_card_copy(needle: str) -> None:
    text = TEMPLATE.read_text(encoding="utf-8") + STAT_PARTIAL.read_text(encoding="utf-8")
    assert needle not in text, f"forbidden placeholder {needle!r} still in Lab templates"
