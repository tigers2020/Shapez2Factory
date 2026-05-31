"""PR-RENDER-1: DOM token-diff paint source contracts (Guard R1)."""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
JS = REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"


def test_token_helper_present() -> None:
    src = JS.read_text(encoding="utf-8")
    assert "function cellRenderToken(" in src
    assert "renderedTokenByKey" in src


def test_render_full_map_cells_skips_unchanged_token() -> None:
    src = JS.read_text(encoding="utf-8")
    idx = src.find("function renderFullMapCells(")
    assert idx >= 0
    body = src[idx : idx + 1500]
    assert "labPaintTokenForCell(" in body
    assert "renderedTokenByKey.get(" in body
    assert "continue" in body
    assert "let tone = toneForFullMapCell(cell, frame)" in body
    assert "el.className = tone ?" in body


def test_reset_clears_token() -> None:
    src = JS.read_text(encoding="utf-8")
    idx = src.find("function resetDomCellAtIndex(")
    assert idx >= 0
    body = src[idx : idx + 600]
    assert "renderedTokenByKey.delete(" in body


def test_incremental_reset_skips_unchanged_token() -> None:
    src = JS.read_text(encoding="utf-8")
    assert "function resetDomCellsAtIndicesForFrame(" in src
    idx = src.find("function resetDomCellsAtIndicesForFrame(")
    body = src[idx : idx + 900]
    assert "labPaintTokenForCell(" in body
    assert "renderedTokenByKey.get(idx) === token" in body
    assert "continue" in body


def test_sprite_src_write_is_guarded() -> None:
    src = JS.read_text(encoding="utf-8")
    idx = src.find("function applyLabCellSprite(")
    assert idx >= 0
    body = src[idx : idx + 900]
    assert 'getAttribute("src")' in body
