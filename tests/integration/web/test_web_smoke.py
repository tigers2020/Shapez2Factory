from pathlib import Path

from django.conf import settings
from django.test import Client


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
    assert b"Construction sequence" in response.content
    assert b"data-shape-preview-code-ref" in response.content
    assert b"SuSuSuSu" in response.content
    assert b"quick_solver_preview.js" in response.content


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
    response = Client().get("/api/shape-preview/", {"code": ""})

    assert response.status_code == 400
    data = response.json()
    assert data["ok"] is False


def test_gallery_page_renders() -> None:
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
    assert (three_root / "examples" / "jsm" / "loaders" / "GLTFLoader.js").is_file()
    assert (three_root / "examples" / "jsm" / "utils" / "BufferGeometryUtils.js").is_file()
    assert (three_root / "examples" / "jsm" / "utils" / "SkeletonUtils.js").is_file()
