from pathlib import Path

from django.conf import settings
from django.test import Client
from django.test.utils import override_settings
from django.urls import reverse


def test_home_page_renders() -> None:
    response = Client().get("/")

    assert response.status_code == 200
    assert b"Solve Shapez 2 production chains" in response.content
    assert b"Quick Solver" in response.content
    assert b"flowbite.min.js" in response.content
    assert b"quick_solver_preview.js" in response.content
    assert b"data-quick-preview-viewers" in response.content
    assert b"data-preview-api" in response.content
    assert b"Shape preview" in response.content
    assert b"data-shape-preview-panel" in response.content
    assert b"data-solver-page-link" in response.content
    assert b"/solver/" in response.content


def test_solver_page_renders() -> None:
    response = Client().get("/solver/", {"code": "SuSuSuSu"})

    assert response.status_code == 200
    assert b"/jsi18n/" in response.content
    assert b"Under construction" in response.content
    assert b"data-shape-preview-code-ref" in response.content
    assert b"SuSuSuSu" in response.content
    assert b"quick_solver_preview.js" in response.content
    assert b"data-shape-preview-panel" in response.content
    assert b"data-quick-preview-viewers" in response.content


def test_asteroid_page_renders() -> None:
    response = Client().get("/asteroid/")

    assert response.status_code == 200
    assert b"Asteroid mining" in response.content
    assert b"/asteroid/" in response.content
    assert b"/api/asteroid/health/" in response.content
    assert b"data-asteroid-copy-root" in response.content
    assert b"/api/asteroid/copy-preview/" in response.content
    assert b"data-asteroid-plot-svg" in response.content


def test_solve_alias_redirects_to_solver_page() -> None:
    response = Client().get("/solve/", {"code": "SuSuSuSu"})

    assert response.status_code == 302
    assert response["Location"] == "/solver/?code=SuSuSuSu"


def test_api_shape_preview_ok() -> None:
    response = Client().get("/api/shape-preview/", {"code": "SuSuSuSu"})

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["warnings"] == []
    assert len(data["patterns"]) == 1
    assert data["patterns"][0]["preview_scene"]["normalized_code"] == "SuSuSuSu"
    cells = data["patterns"][0]["preview_scene"]["cells"]
    assert len(cells) == 4
    assert all("mesh_key" in cell for cell in cells)


def test_api_shape_preview_parse_error() -> None:
    response = Client().get("/api/shape-preview/", {"code": "not_a_real_code!!!"})

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["patterns"] == []
    assert data["error"]


def test_api_shape_preview_empty_code() -> None:
    response = Client().get("/gallery/")

    assert response.status_code == 200
    assert b"Screenshots" in response.content
    assert b"Factory templates" in response.content
    assert b"Open original" in response.content
    assert b"gallery-viewer" in response.content
    assert b"gallery-viewer-prev" in response.content
    assert b"gallery-viewer-next" in response.content
    assert b"gallery-viewer.js" in response.content


def test_demo_page_renders() -> None:
    response = Client().get("/demo/")

    assert response.status_code == 200
    assert b"Core parser" in response.content
    assert b"parse_shape_code_list" in response.content
    assert b"shape_gltf_viewer.js" in response.content
    assert b"data-shape-gltf-viewer" in response.content
    assert b"data-shape-gltf-mode-controls" in response.content
    assert b'data-shape-gltf-mode="original"' in response.content
    assert b'data-shape-gltf-mode="layer"' in response.content
    assert b'data-shape-gltf-mode="quadrant"' in response.content
    assert b"Shape preview" in response.content
    assert b'"mesh_key": "default_rect"' in response.content
    assert b"shape-preview" not in response.content
    assert b"Example production plan" in response.content
    assert b"How it works" in response.content


def test_home_nav_links_to_split_pages() -> None:
    response = Client().get("/")

    assert response.status_code == 200
    assert b'href="/gallery/"' in response.content
    assert b'href="/demo/"' in response.content
    assert b'href="/solver/"' in response.content
    assert b'href="/support/"' in response.content


def test_support_page_renders() -> None:
    with override_settings(
        SUPPORT_KOFI_URL="",
        SUPPORT_GITHUB_SPONSORS_URL="",
        SUPPORT_PATREON_URL="",
    ):
        response = Client().get("/support/")

        assert response.status_code == 200
        assert b"Support" in response.content
        assert b"SUPPORT_KOFI_URL" in response.content
        assert b'href="/support/"' in response.content
        assert b"1CYVnLMkGq9u8u1JDnH4aCFWXLTTZ6be2j" in response.content
        assert b"0xa921081Bf8B548987188f3a87e7728F047301CfE" in response.content
        assert b"data-support-tabs" in response.content


def test_support_page_kofi_widget_from_profile_url() -> None:
    with override_settings(
        SUPPORT_KOFI_URL="https://ko-fi.com/shapez2factory/",
        SUPPORT_GITHUB_SPONSORS_URL="",
        SUPPORT_PATREON_URL="",
    ):
        response = Client().get("/support/")

        assert response.status_code == 200
        assert b'id="kofiframe"' in response.content
        assert b"ko-fi.com/shapez2factory/?hidefeed=true&amp;widget=true&amp;embed=true" in (
            response.content
        )
        assert b"In production, set the environment variables" not in response.content
        assert b"data-support-tabs" in response.content
        assert b"support-panel-bch" in response.content
        assert b"support-panel-ethereum" in response.content


def test_support_page_kofi_non_profile_still_shows_link() -> None:
    with override_settings(
        SUPPORT_KOFI_URL="https://example.com/kofi",
        SUPPORT_GITHUB_SPONSORS_URL="",
        SUPPORT_PATREON_URL="",
    ):
        response = Client().get("/support/")

        assert response.status_code == 200
        assert b'id="kofiframe"' not in response.content
        assert b"https://example.com/kofi" in response.content


def test_shape_gltf_vendor_assets_exist() -> None:
    static_root = Path(settings.BASE_DIR) / "django_apps" / "web" / "static" / "web"
    shape_root = static_root / "vendor" / "shapez-vortex" / "models" / "shapes"
    three_root = static_root / "vendor" / "three" / "0.184.0"

    for stem in (
        "ShapeDefaultR",
        "ShapeDefaultC",
        "ShapeDefaultS",
        "ShapeDefaultW",
        "ShapeDefaultP",
    ):
        assert (shape_root / f"{stem}.gltf").is_file()
        assert (shape_root / f"{stem}.bin").is_file()

    assert (three_root / "build" / "three.module.js").is_file()
    assert (three_root / "build" / "three.core.js").is_file()
    assert (three_root / "examples" / "jsm" / "controls" / "OrbitControls.js").is_file()
    assert (three_root / "examples" / "jsm" / "environments" / "RoomEnvironment.js").is_file()
    assert (three_root / "examples" / "jsm" / "loaders" / "GLTFLoader.js").is_file()
    assert (three_root / "examples" / "jsm" / "utils" / "BufferGeometryUtils.js").is_file()
    assert (three_root / "examples" / "jsm" / "utils" / "SkeletonUtils.js").is_file()


def test_solver_graph_viewport_has_explicit_runtime_layout_styles() -> None:
    static_root = Path(settings.BASE_DIR) / "django_apps" / "web" / "static" / "web"
    mount_script = (static_root / "js" / "solver_timeline" / "graph_mount.js").read_text(
        encoding="utf-8"
    )
    markup_script = (static_root / "js" / "solver_timeline" / "graph_markup.js").read_text(
        encoding="utf-8"
    )
    viewport_script = (static_root / "js" / "solver_timeline" / "graph_viewport.js").read_text(
        encoding="utf-8"
    )

    assert "data-graph-viewport" in mount_script
    assert 'style="height: 34rem; touch-action: none; cursor: grab;' in markup_script
    assert "transform-origin: 0 0;" in markup_script
    assert 'viewport.style.cursor = "grabbing"' in viewport_script
    assert "preview_image_url" in markup_script
    assert "No preview" in markup_script
    assert "data-graph-shape-preview" not in markup_script
    assert "./solver_graph_layout.js" in markup_script
    assert "overflow-y-auto" not in markup_script
    assert "L ${geometry.elbowX} ${geometry.y1}" in markup_script
    assert "data-graph-edge-label" in markup_script


def test_javascript_catalog_default_language() -> None:
    response = Client().get(reverse("javascript-catalog"))
    assert response.status_code == 200
    assert b"gettext" in response.content


def test_javascript_catalog_ko_prefixed_url() -> None:
    response = Client().get("/ko/jsi18n/")
    assert response.status_code == 200
    assert b"gettext" in response.content


def test_operation_icon_assets_exist() -> None:
    static_root = Path(settings.BASE_DIR) / "django_apps" / "web" / "static" / "web"
    operation_root = static_root / "images" / "operations"

    for filename in (
        "color-mixer.png",
        "crystal-generator.png",
        "crystal-generator2.png",
        "cutter.png",
        "half-destroyer.png",
        "merger.png",
        "painter.png",
        "pin-pusher.png",
        "pin-pusher2.png",
        "rotator-180.png",
        "rotator-ccw.png",
        "rotator-cw.png",
        "splitter.png",
        "stacker.png",
        "swapper.png",
    ):
        assert (operation_root / filename).is_file()
