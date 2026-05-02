from __future__ import annotations

import json
import subprocess
import tempfile
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Protocol

from django.conf import settings
from django.urls import reverse


@dataclass(frozen=True, slots=True)
class GraphPreview:
    alt_text: str
    image_url: str | None = None


class GraphPreviewRenderer(Protocol):
    def render(self, preview_scene: dict[str, Any]) -> GraphPreview: ...


def get_graph_preview_renderer() -> GraphPreviewRenderer:
    return PlaywrightPngGraphPreviewRenderer()


class PlaywrightPngGraphPreviewRenderer:
    VERSION = "v2"
    PRESET = "graph-tile-original"
    SIZE = "128x128"
    TIMEOUT_SECONDS = 45
    BROKEN_PNG_SHA256 = "06677fd90bc53a5f0de1cca18046d60cae5aa72e7515aa9b6df8deb7099af9d9"

    def __init__(self) -> None:
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
                alt_text=alt_text,
                image_url=reverse("web:graph_preview_cache", args=[f"{cache_key}.png"]),
            )

        if self._generation_disabled:
            return GraphPreview(alt_text=alt_text)

        if self._generate_png(preview_scene, cache_path) and self._is_valid_png(cache_path):
            return GraphPreview(
                alt_text=alt_text,
                image_url=reverse("web:graph_preview_cache", args=[f"{cache_key}.png"]),
            )

        self._generation_disabled = True
        return GraphPreview(alt_text=alt_text)

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
