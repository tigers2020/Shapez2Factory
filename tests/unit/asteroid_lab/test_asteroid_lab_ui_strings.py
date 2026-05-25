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


def test_lab_footprint_subtitle_documents_field_cells() -> None:
    text = TEMPLATE.read_text(encoding="utf-8") + STAT_PARTIAL.read_text(encoding="utf-8")
    assert "field cells / map cells" in text


def test_lab_detail_panel_uses_asteroid_field_terminology() -> None:
    detail = (
        REPO
        / "django_apps"
        / "web"
        / "templates"
        / "web"
        / "partials"
        / "lab_run_detail_panels.html"
    ).read_text(encoding="utf-8")
    assert "Asteroid field cells" in detail
    assert "lab-detail-rec-field-total" in detail
    assert "Mineable cells" not in detail
    assert "Confirmed total" not in detail


def test_lab_terrain_rim_highlight_toggle_and_css_contract() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    js = (
        REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    ).read_text(encoding="utf-8")
    css = (REPO / "assets" / "css" / "input.css").read_text(encoding="utf-8")
    assert 'id="lab-terrain-rim-highlight-toggle"' in template
    assert "Rim highlight" in template
    assert "terrain_rim_highlight" in js
    assert "frozen_terrain_rim_highlight" in js
    assert "applyTerrainRimHighlight" in js
    assert "outer_outline_loops" in js
    assert "lab-terrain-rim-outline-path" in css
    assert "lab-terrain-rim-outline-svg" in css
    assert "lab-terrain-rim-highlight" in js


def test_lab_replay_description_has_fixed_scroll_viewport() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    idx = template.index('id="lab-replay-description"')
    chunk = template[idx : idx + 280]
    assert "overflow-y-auto" in chunk
    assert "max-h-48" in chunk
    footer_idx = template.index('id="lab-map-footer"')
    assert footer_idx < idx


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
