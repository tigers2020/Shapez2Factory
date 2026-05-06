from __future__ import annotations

import json
import logging
import subprocess
import tempfile
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from typing import Any, Protocol

from django.conf import settings
from django.urls import reverse

from django_apps.web.constants import WEB_GRAPH_PREVIEW_TIMEOUT_SECONDS
from django_apps.web.models import GraphPreviewImage

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class GraphPreview:
    alt_text: str
    image_url: str | None = None


class GraphPreviewRenderer(Protocol):
    def render(self, preview_scene: dict[str, Any]) -> GraphPreview: ...


@dataclass(frozen=True, slots=True)
class _RenderTarget:
    cache_key: str
    cache_path: Path
    image_url: str
    alt_text: str


def png_bytes_are_valid(data: bytes, *, broken_sha256_hex: str) -> bool:
    try:
        digest = sha256(data).hexdigest().lower()
    except OSError:
        return False
    return digest != broken_sha256_hex.lower()


class _GraphPreviewCache:
    def __init__(self, cache_dir: Path, broken_png_sha256: str) -> None:
        self._cache_dir = cache_dir
        self._broken_png_sha256 = broken_png_sha256.lower()

    def build_target(
        self,
        preview_scene: dict[str, Any],
        *,
        version: str,
        preset: str,
        size: str,
    ) -> _RenderTarget:
        cache_key = self.cache_key(
            preview_scene,
            version=version,
            preset=preset,
            size=size,
        )
        return _RenderTarget(
            cache_key=cache_key,
            cache_path=self._cache_dir / f"{cache_key}.png",
            image_url=reverse("web:graph_preview_cache", args=[f"{cache_key}.png"]),
            alt_text=f"Graph preview for {preview_scene.get('normalized_code', 'shape preview')}",
        )

    def cache_key(
        self,
        preview_scene: dict[str, Any],
        *,
        version: str,
        preset: str,
        size: str,
    ) -> str:
        payload = json.dumps(preview_scene, sort_keys=True, separators=(",", ":"))
        digest = sha256(f"{version}|{preset}|{size}|{payload}".encode()).hexdigest()
        return digest[:24]

    def ensure_dir(self) -> None:
        self._cache_dir.mkdir(parents=True, exist_ok=True)

    def has_valid_png(self, cache_path: Path) -> bool:
        if not cache_path.is_file():
            return False
        try:
            data = cache_path.read_bytes()
        except OSError:
            return False
        return png_bytes_are_valid(data, broken_sha256_hex=self._broken_png_sha256)


class _PlaywrightPrerenderer:
    def __init__(self, script_path: Path, timeout_seconds: int, cache_dir: Path) -> None:
        self._script_path = script_path
        self._timeout_seconds = timeout_seconds
        self._cache_dir = cache_dir

    def render_png(
        self,
        preview_scene: dict[str, Any],
        cache_path: Path,
        *,
        json_parent: Path | None = None,
    ) -> bool:
        if not self._script_path.is_file():
            logger.warning("Graph preview renderer script missing: %s", self._script_path)
            return False

        parent = json_parent if json_parent is not None else self._cache_dir
        parent.mkdir(parents=True, exist_ok=True)

        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            suffix=".json",
            dir=parent,
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
                timeout=self._timeout_seconds,
                check=False,
            )
            if completed.returncode != 0 or not cache_path.is_file():
                logger.warning(
                    "Graph preview render failed: returncode=%s stderr=%s stdout=%s",
                    completed.returncode,
                    completed.stderr,
                    completed.stdout,
                )
                return False
            return True
        finally:
            scene_path.unlink(missing_ok=True)


def _graph_preview_storage_is_database() -> bool:
    raw = getattr(settings, "SOLVER_GRAPH_PREVIEW_STORAGE", "filesystem")
    return isinstance(raw, str) and raw.strip().lower() == "database"


class PlaywrightPngGraphPreviewRenderer:
    VERSION = "v3"
    PRESET = "graph-tile-original"
    SIZE = "128x128"
    BROKEN_PNG_SHA256 = "06677fd90bc53a5f0de1cca18046d60cae5aa72e7515aa9b6df8deb7099af9d9"

    def __init__(self) -> None:
        cache_dir = Path(settings.SOLVER_GRAPH_PREVIEW_CACHE_DIR)
        script_path = Path(settings.BASE_DIR) / "scripts" / "render_graph_preview.mjs"
        self._cache = _GraphPreviewCache(cache_dir, self.BROKEN_PNG_SHA256)
        self._prerenderer = _PlaywrightPrerenderer(
            script_path,
            WEB_GRAPH_PREVIEW_TIMEOUT_SECONDS,
            cache_dir,
        )
        self._generation_disabled = False

    def render(self, preview_scene: dict[str, Any]) -> GraphPreview:
        target = self._cache.build_target(
            preview_scene,
            version=self.VERSION,
            preset=self.PRESET,
            size=self.SIZE,
        )
        use_db = _graph_preview_storage_is_database()

        if use_db and self._has_valid_png_db(target.cache_key):
            return GraphPreview(alt_text=target.alt_text, image_url=target.image_url)

        if not use_db:
            self._cache.ensure_dir()
            if self._cache.has_valid_png(target.cache_path):
                return GraphPreview(alt_text=target.alt_text, image_url=target.image_url)

        if self._generation_disabled:
            return GraphPreview(alt_text=target.alt_text)

        if self._generate_and_store(preview_scene, target, use_db=use_db):
            return GraphPreview(alt_text=target.alt_text, image_url=target.image_url)

        self._generation_disabled = True
        return GraphPreview(alt_text=target.alt_text)

    def cache_key(self, preview_scene: dict[str, Any]) -> str:
        return self._cache.cache_key(
            preview_scene,
            version=self.VERSION,
            preset=self.PRESET,
            size=self.SIZE,
        )

    def _has_valid_png_db(self, cache_key: str) -> bool:
        row = GraphPreviewImage.objects.filter(pk=cache_key).first()
        if row is None or not row.png:
            return False
        return png_bytes_are_valid(bytes(row.png), broken_sha256_hex=self.BROKEN_PNG_SHA256)

    def _generate_and_store(
        self,
        preview_scene: dict[str, Any],
        target: _RenderTarget,
        *,
        use_db: bool,
    ) -> bool:
        try:
            if use_db:
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    tmp_out = Path(tmp.name)
                try:
                    ok = self._prerenderer.render_png(
                        preview_scene,
                        tmp_out,
                        json_parent=Path(tempfile.gettempdir()),
                    )
                    if not ok:
                        return False
                    data = tmp_out.read_bytes()
                    if not png_bytes_are_valid(data, broken_sha256_hex=self.BROKEN_PNG_SHA256):
                        return False
                    GraphPreviewImage.objects.update_or_create(
                        cache_key=target.cache_key,
                        defaults={"png": data},
                    )
                    return True
                finally:
                    tmp_out.unlink(missing_ok=True)

            self._cache.ensure_dir()
            ok = self._prerenderer.render_png(preview_scene, target.cache_path)
            return bool(ok and self._cache.has_valid_png(target.cache_path))
        except (OSError, subprocess.SubprocessError):
            return False


class NoopGraphPreviewRenderer:
    """Skip server-side PNG generation (Playwright). Use on hosts without node/Chromium."""

    def render(self, preview_scene: dict[str, Any]) -> GraphPreview:
        alt = f"Graph preview for {preview_scene.get('normalized_code', 'shape preview')}"
        return GraphPreview(alt_text=alt, image_url=None)

    def cache_key(self, preview_scene: dict[str, Any]) -> str:
        return _GraphPreviewCache(
            Path(settings.SOLVER_GRAPH_PREVIEW_CACHE_DIR),
            PlaywrightPngGraphPreviewRenderer.BROKEN_PNG_SHA256,
        ).cache_key(
            preview_scene,
            version=PlaywrightPngGraphPreviewRenderer.VERSION,
            preset=PlaywrightPngGraphPreviewRenderer.PRESET,
            size=PlaywrightPngGraphPreviewRenderer.SIZE,
        )


def get_graph_preview_renderer() -> GraphPreviewRenderer:
    mode = getattr(settings, "SOLVER_GRAPH_PREVIEW_RENDERER", "playwright_png")
    if isinstance(mode, str) and mode.strip().lower() == "noop":
        return NoopGraphPreviewRenderer()
    return PlaywrightPngGraphPreviewRenderer()
