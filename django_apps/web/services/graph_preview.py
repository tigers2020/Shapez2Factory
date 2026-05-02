from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from hashlib import sha256
from html import escape
from pathlib import Path
from typing import Any, Literal, Protocol

from django.conf import settings
from django.urls import reverse

type GraphPreviewKind = Literal["markup", "image"]

_COLOR_HEX = {
    "u": "#cbd5e1",
    "r": "#ef4444",
    "g": "#22c55e",
    "b": "#3b82f6",
    "c": "#2ec4b6",
    "m": "#d946ef",
    "y": "#facc15",
    "w": "#ffffff",
}
_POSITION_OFFSETS = {
    "SW": (46.0, 82.0),
    "NW": (46.0, 46.0),
    "NE": (82.0, 46.0),
    "SE": (82.0, 82.0),
}
_POSITION_ROTATIONS = {
    "SW": 0.0,
    "NW": -90.0,
    "NE": 180.0,
    "SE": 90.0,
}


@dataclass(frozen=True, slots=True)
class GraphPreview:
    kind: GraphPreviewKind
    alt_text: str
    markup: str | None = None
    image_url: str | None = None


class GraphPreviewRenderer(Protocol):
    def render(self, preview_scene: dict[str, Any]) -> GraphPreview: ...


def get_graph_preview_renderer() -> GraphPreviewRenderer:
    mode = settings.SOLVER_GRAPH_PREVIEW_RENDERER
    if mode == "playwright_png":
        return PlaywrightPngGraphPreviewRenderer()
    return LightweightGraphPreviewRenderer()


class LightweightGraphPreviewRenderer:
    def render(self, preview_scene: dict[str, Any]) -> GraphPreview:
        normalized_code = str(preview_scene.get("normalized_code", "")).strip() or "shape preview"
        alt_text = f"Graph preview for {normalized_code}"
        return GraphPreview(
            kind="markup",
            alt_text=alt_text,
            markup=_render_scene_markup(preview_scene, alt_text),
        )


class PlaywrightPngGraphPreviewRenderer:
    VERSION = "v2"
    PRESET = "graph-tile-original"
    SIZE = "128x128"
    TIMEOUT_SECONDS = 45
    BROKEN_PNG_SHA256 = "06677fd90bc53a5f0de1cca18046d60cae5aa72e7515aa9b6df8deb7099af9d9"

    def __init__(self, fallback: GraphPreviewRenderer | None = None) -> None:
        self._fallback = fallback or LightweightGraphPreviewRenderer()
        self._cache_dir = Path(settings.SOLVER_GRAPH_PREVIEW_CACHE_DIR)
        self._script_path = Path(settings.BASE_DIR) / "scripts" / "render_graph_preview.mjs"
        self._generation_disabled = False

    def render(self, preview_scene: dict[str, Any]) -> GraphPreview:
        cache_key = self.cache_key(preview_scene)
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        cache_path = self._cache_dir / f"{cache_key}.png"
        alt_text = f"Graph preview for {preview_scene.get('normalized_code', 'shape preview')}"
        if cache_path.is_file() and self._is_valid_png(cache_path):
            return GraphPreview(
                kind="image",
                alt_text=alt_text,
                image_url=reverse("web:graph_preview_cache", args=[f"{cache_key}.png"]),
            )

        if self._generation_disabled:
            return self._fallback.render(preview_scene)

        if self._generate_png(preview_scene, cache_path) and self._is_valid_png(cache_path):
            return GraphPreview(
                kind="image",
                alt_text=alt_text,
                image_url=reverse("web:graph_preview_cache", args=[f"{cache_key}.png"]),
            )

        self._generation_disabled = True
        return self._fallback.render(preview_scene)

    def cache_key(self, preview_scene: dict[str, Any]) -> str:
        payload = json.dumps(preview_scene, sort_keys=True, separators=(",", ":"))
        digest = sha256(f"{self.VERSION}|{self.PRESET}|{self.SIZE}|{payload}".encode()).hexdigest()
        return digest[:24]

    def _generate_png(self, preview_scene: dict[str, Any], cache_path: Path) -> bool:
        try:
            return self._invoke_playwright_prerender(preview_scene, cache_path)
        except (OSError, subprocess.SubprocessError):
            return False

    def _invoke_playwright_prerender(
        self,
        preview_scene: dict[str, Any],
        cache_path: Path,
    ) -> bool:
        if not self._script_path.is_file():
            return False

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            dir=self._cache_dir,
            delete=False,
        ) as handle:
            json.dump(preview_scene, handle)
            scene_path = Path(handle.name)

        try:
            completed = subprocess.run(
                [
                    "node",
                    str(self._script_path),
                    "--scene-file",
                    str(scene_path),
                    "--out",
                    str(cache_path),
                ],
                capture_output=True,
                cwd=settings.BASE_DIR,
                text=True,
                timeout=self.TIMEOUT_SECONDS,
                check=False,
            )
            return completed.returncode == 0 and cache_path.is_file()
        finally:
            scene_path.unlink(missing_ok=True)

    def _is_valid_png(self, cache_path: Path) -> bool:
        try:
            digest = sha256(cache_path.read_bytes()).hexdigest().lower()
        except OSError:
            return False
        return digest != self.BROKEN_PNG_SHA256


def _render_scene_markup(preview_scene: dict[str, Any], alt_text: str) -> str:
    cells = preview_scene.get("cells", [])
    ordered_cells = sorted(
        cells,
        key=lambda cell: (
            int(cell.get("layer_index", 0)),
            int(cell.get("quadrant_index", 0)),
        ),
    )
    body = "".join(_render_cell(cell) for cell in ordered_cells if isinstance(cell, dict))
    return (
        f'<svg class="mx-auto h-full w-full" viewBox="0 0 128 128" role="img" '
        f'aria-label="{escape(alt_text)}" xmlns="http://www.w3.org/2000/svg">'
        "<defs>"
        '<radialGradient id="graph-preview-glow" cx="35%" cy="28%" r="70%">'
        '<stop offset="0%" stop-color="#3d3a44"/>'
        '<stop offset="100%" stop-color="#23212a"/>'
        "</radialGradient>"
        '<filter id="graph-preview-shadow" x="-30%" y="-30%" width="160%" height="160%">'
        '<feDropShadow dx="0" dy="5" stdDeviation="3" flood-color="#020617" flood-opacity="0.45"/>'
        "</filter>"
        "</defs>"
        '<circle cx="64" cy="64" r="54" fill="#2c2a31"/>'
        '<circle cx="64" cy="64" r="53" fill="url(#graph-preview-glow)"/>'
        f"{body}"
        "</svg>"
    )


def _render_cell(cell: dict[str, Any]) -> str:
    position = str(cell.get("position", "SW"))
    x, y = _POSITION_OFFSETS.get(position, (64.0, 64.0))
    rotation = _POSITION_ROTATIONS.get(position, 0.0)
    layer_index = int(cell.get("layer_index", 0))
    scale = max(0.72, 1.0 - layer_index * 0.18)
    fill = _COLOR_HEX.get(str(cell.get("material_key", "u")), "#cbd5e1")
    lift_y = layer_index * -7.0
    shape_markup = _shape_markup(str(cell.get("mesh_key", "default_rect")), fill)
    return (
        f'<g transform="translate({x:.1f} {y + lift_y:.1f}) '
        f'rotate({rotation:.1f}) scale({scale:.2f})" '
        'filter="url(#graph-preview-shadow)">'
        f"{shape_markup}</g>"
    )


def _shape_markup(mesh_key: str, fill: str) -> str:
    stroke = "#94a3b8"
    if mesh_key == "default_circle":
        shape = '<path d="M -20 -20 C -8 -20 8 -12 20 0 L 20 20 L -20 20 Z" />'
    elif mesh_key == "default_star":
        shape = '<path d="M -20 -20 L 10 -20 L 20 8 L -2 20 L -20 20 Z" />'
    elif mesh_key == "default_diamond":
        shape = '<path d="M 0 -20 L 22 0 L 0 22 L -20 0 Z" />'
    elif mesh_key == "default_pin":
        shape = '<path d="M -18 -20 L 18 -20 L 18 0 L 6 0 L 6 20 L -6 20 L -6 0 L -18 0 Z" />'
    elif mesh_key == "default_crystal":
        shape = '<path d="M -8 -22 L 16 -8 L 12 18 L -12 22 L -22 -2 Z" />'
    else:
        shape = '<rect x="-20" y="-20" width="40" height="40" rx="9" ry="9" />'

    return (
        f'<g fill="{fill}" stroke="{stroke}" stroke-opacity="0.28" stroke-width="1.2">'
        '<g opacity="0.22" transform="translate(3 3)" fill="#0f172a" stroke="none">'
        f"{shape}</g>"
        f"{shape}"
        '<path d="M -14 -12 Q -3 -18 8 -12" fill="none" stroke="#ffffff" '
        'stroke-opacity="0.32" stroke-width="3" />'
        "</g>"
    )
