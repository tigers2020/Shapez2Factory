"""Graph preview PNG / alt text (injected from the web adapter)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from typing import Any, Protocol

__all__ = [
    "GraphPreviewResult",
    "GraphPreviewRenderer",
    "NoopGraphPreviewRenderer",
]


@dataclass(frozen=True, slots=True)
class GraphPreviewResult:
    """Minimal DTO for shape node preview fields (mirrors web ``GraphPreview``)."""

    alt_text: str
    image_url: str | None = None


class GraphPreviewRenderer(Protocol):
    """PNG/cache implementations live in the web app's ``graph_preview`` service."""

    def render(self, preview_scene: dict[str, Any]) -> Any: ...

    def render_cached_only(self, preview_scene: dict[str, Any]) -> Any: ...

    def cache_key(self, preview_scene: dict[str, Any]) -> str: ...


class NoopGraphPreviewRenderer:
    """No server-side PNG; for tests and hosts without Playwright. Not settings-coupled."""

    def render_cached_only(self, preview_scene: dict[str, Any]) -> GraphPreviewResult:
        alt = f"Graph preview for {preview_scene.get('normalized_code', 'shape preview')}"
        return GraphPreviewResult(alt_text=alt, image_url=None)

    def render(self, preview_scene: dict[str, Any]) -> GraphPreviewResult:
        return self.render_cached_only(preview_scene)

    def cache_key(self, preview_scene: dict[str, Any]) -> str:
        payload = json.dumps(preview_scene, sort_keys=True, separators=(",", ":"))
        return sha256(payload.encode()).hexdigest()[:24]
