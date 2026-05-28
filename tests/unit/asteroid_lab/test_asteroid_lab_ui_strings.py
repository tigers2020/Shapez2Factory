"""Lab template must not ship GA placeholder stat card copy."""

from __future__ import annotations

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[3]
TEMPLATE = REPO / "django_apps" / "web" / "templates" / "web" / "asteroid_miner_layout_solver.html"
LAYER_SUMMARIES_PARTIAL = (
    REPO / "django_apps" / "web" / "templates" / "web" / "partials" / "lab_layer_summaries.html"
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


def test_lab_template_ops_slug_badge_slot() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    assert 'id="lab-detail-ops-slug-badge"' in template


def test_lab_js_pass_capable_badge_contract() -> None:
    js = (
        REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    ).read_text(encoding="utf-8")
    css = (REPO / "assets" / "css" / "input.css").read_text(encoding="utf-8")
    assert "resolveRttpOpsSlugClass" in js
    assert 'getElementById("lab-detail-ops-slug-badge")' in js
    assert "Pass-capable" in js
    assert "pass_capable" in js
    assert "lab-ops-slug-badge--pass-capable" in css
    detail_fn = js[js.index("function runDetailStatusLabel") : js.index("function labUiDash")]
    diag_use = detail_fn.index("diagnosticT2ShortfallStatusText(run)")
    pc_use = detail_fn.index("passCapableReferenceStatusText(run)")
    assert diag_use < pc_use, "diagnostic shortfall copy must win over pass_capable status"


def test_lab_selected_run_detail_uses_layer_summaries_partial() -> None:
    template = TEMPLATE.read_text(encoding="utf-8")
    partial = LAYER_SUMMARIES_PARTIAL.read_text(encoding="utf-8")
    assert "lab_layer_summaries.html" in template
    assert 'id="lab-layer-summaries"' in partial
    assert "lab_stat_cards.html" not in template
    assert "lab_run_detail_panels.html" not in template
    assert 'id="lab-card-theoretical-max"' not in template


def test_lab_js_renders_layer_summaries_from_run_payload() -> None:
    js = (
        REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    ).read_text(encoding="utf-8")
    assert "renderLabLayerSummaries" in js
    assert "run.layer_summaries" in js
    assert "updateLabStatCards" not in js
    assert "updateLabDetailPanels" not in js


def test_lab_exterior_connector_overlay_contract() -> None:
    js = (
        REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"
    ).read_text(encoding="utf-8")
    css = (REPO / "assets" / "css" / "input.css").read_text(encoding="utf-8")
    assert "planned_exterior_connector" in js
    assert "exterior_connector_plan" in js
    assert "frozen_exterior_connector_plan" in js
    assert "lab-planned-exterior-connector" in css
    assert "lab-planned-exterior-connector" in js
    assert "applyPlannedExteriorConnectorWhiteHighlight" in js
    assert "renderPlannedExteriorConnectorHighlights" in js
    assert "plannedConnectorCellsFromWire" in js
    assert "plannedConnectorCoordKeys" in js
    assert "skipPlannedExteriorConnectors" in js
    assert "overlay_role" in js
    assert "row.overlay_role = String(c.overlay_role)" in js
    assert "sortOverlayCellsForPaint" in js
    assert "contain: layout paint" in css
    built_css = (REPO / "django_apps" / "web" / "static" / "web" / "css" / "app.css").read_text(
        encoding="utf-8",
    )
    assert (
        "lab-planned-exterior-connector" in built_css
    ), "run npm run build:css — Lab L2 marker styles missing from app.css"
    assert "inset" in built_css


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
    text = TEMPLATE.read_text(encoding="utf-8")
    assert needle not in text, f"forbidden placeholder {needle!r} still in Lab templates"
