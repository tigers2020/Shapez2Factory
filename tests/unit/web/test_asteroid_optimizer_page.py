"""Smoke: asteroid optimizer page exposes wired API URLs from view context."""

from pathlib import Path

from django.test import Client
from django.urls import reverse


def test_asteroid_optimizer_page_get_includes_copy_preview_url() -> None:
    url = reverse("web:asteroid")
    expected_preview = reverse("shapez_asteroid:copy_preview")
    response = Client().get(url)

    assert response.status_code == 200
    assert expected_preview.encode() in response.content
    assert b"data-am-solver-replay-meta" in response.content


def test_asteroid_optimizer_recovery_overlay_meta_smoke() -> None:
    """STEP10 replay SVG overlay group class is wired in the optimizer template."""

    response = Client().get(reverse("web:asteroid"))
    assert response.status_code == 200
    assert b"am-step10-replay-overlay" in response.content
    assert b"data-msg-route-replay-removed" in response.content
    assert b"am-route-replay-cells-overlay" in response.content
    assert b"normalizeReplayTransportKind" in response.content


def test_asteroid_optimizer_map_cells_fetch_cache_smoke() -> None:
    """Map-cells GET is memoized per bbox in inline script (replay must not spam server)."""

    response = Client().get(reverse("web:asteroid"))
    assert response.status_code == 200
    assert b"fetchMapCellsBboxOnce" in response.content
    assert b"clearMapCellsFetchCache" in response.content


def test_asteroid_optimizer_pass1_extension_overlay_outline_smoke() -> None:
    """Pass1 replay outline branches: extension vs extractor vs probe vs scan cursor."""

    response = Client().get(reverse("web:asteroid"))
    assert response.status_code == 200
    assert b"pass1_extension_" in response.content
    assert b"pass1_extractor_" in response.content
    assert b"pass1_probe_stub_ok" in response.content
    assert b"pass1_scan_cursor" in response.content


def test_asteroid_optimizer_map_sprite_atlas_smoke() -> None:
    """Sprite atlas wires static PNG/JSON, resolver, renderer, and canvas drawImage path."""

    response = Client().get(reverse("web:asteroid"))
    assert response.status_code == 200
    assert b"web/asteroid_optimizer/sprites/asteroid_map_atlas.png" in response.content
    assert b"web/asteroid_optimizer/sprites/asteroid_map_atlas.json" in response.content
    assert b"map_sprite_atlas.js" in response.content
    assert b"map_sprite_resolver.js" in response.content
    assert b"map_sprite_renderer.js" in response.content
    assert b"AM_AsteroidMapSpriteAtlas" in response.content
    assert b"AM_AsteroidMapSpriteResolver" in response.content
    assert b"AM_AsteroidMapSpriteRenderer" in response.content
    assert b"createFallbackSpriteAtlas" in response.content
    assert b"appendSvgSpriteTile" in response.content
    assert b"appendSvgSpriteOverlays" in response.content
    assert b"cellIsOutputStubTransport" in response.content
    assert b"resolveMiningCellSpriteDrawSpec" in response.content

    repo = Path(__file__).resolve().parents[3]
    js_dir = repo / "django_apps" / "web" / "static" / "web" / "asteroid_optimizer" / "js"
    assert (js_dir / "map_sprite_atlas.js").is_file()
    assert (js_dir / "map_sprite_resolver.js").is_file()
    assert (js_dir / "map_sprite_renderer.js").is_file()

    atlas_js = (js_dir / "map_sprite_atlas.js").read_bytes()
    assert b"loadSpriteAtlas" in atlas_js
    assert b"loadImage" in atlas_js

    resolver_js = (js_dir / "map_sprite_resolver.js").read_bytes()
    assert b"SpaceBelt_" in resolver_js
    assert b"SpacePipe_" in resolver_js
    assert b"+ fullType" in resolver_js
    assert b"resolveSpaceTransportComposedKey" in resolver_js
    assert b"suffixCategoryFallback" in resolver_js
    assert b"resolveAsteroidSpriteKey" in resolver_js
    assert b"equipment_Layout_ShapeMiner" in resolver_js
    assert b"equipment_Layout_FluidMiner" in resolver_js
    assert b'_stub"' in resolver_js

    renderer_js = (js_dir / "map_sprite_renderer.js").read_bytes()
    assert b"drawSpriteTile" in renderer_js
    assert b"imageSmoothingEnabled = false" in renderer_js

    sprites_dir = repo / "django_apps" / "web" / "static" / "web" / "asteroid_optimizer" / "sprites"
    assert (sprites_dir / "asteroid_map_atlas.png").is_file()
    assert (sprites_dir / "asteroid_map_atlas.json").is_file()
