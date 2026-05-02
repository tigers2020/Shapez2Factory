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
    assert b"Recipe graph" in response.content
    assert b"data-shape-preview-code-ref" in response.content
    assert b"SuSuSuSu" in response.content
    assert b"quick_solver_preview.js" in response.content
    assert b"solver_timeline.js" in response.content
    assert b"data-solver-timeline" in response.content
    assert b"data-solver-graph-canvas" in response.content
    assert b"data-solver-graph-empty" in response.content
    assert b"data-solver-node-detail" in response.content
    assert b"data-graph-quantity-toggle" in response.content
    assert b"Materialized graph" in response.content
    assert b'data-graph-quantity-replicas="on"' in response.content
    assert b"/api/solver/solve/" in response.content
    assert b"data-asset-base" in response.content
    assert b"Base inputs stay on the left, target outputs stay on the right" in response.content
    assert b"right-aligned layout style" in response.content
    assert b"wheel to zoom" in response.content


def test_solve_alias_redirects_to_solver_page() -> None:
    response = Client().get("/solve/", {"code": "SuSuSuSu"})

    assert response.status_code == 302
    assert response["Location"] == "/solver/?code=SuSuSuSu"


def test_api_solver_solve_returns_graph_first_result() -> None:
    response = Client().post(
        "/api/solver/solve/",
        data={"code": "CuRuSuWu"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert data["found"] is True
    assert data["target_shape"] == "CuRuSuWu"
    assert isinstance(data["steps"], list)

    graph = data["graph"]
    assert graph["layout"]["direction"] == "left-to-right"
    assert graph["nodes"]
    assert graph["edges"]

    shape_nodes = [node for node in graph["nodes"] if node["kind"] == "shape"]
    operation_nodes = [node for node in graph["nodes"] if node["kind"] == "operation"]
    target_nodes = [node for node in shape_nodes if node["role"] == "target"]
    source_nodes = [node for node in shape_nodes if node["role"] == "source"]
    intermediate_nodes = [node for node in shape_nodes if node["role"] == "intermediate"]
    assert shape_nodes
    assert source_nodes
    assert intermediate_nodes
    assert operation_nodes
    assert len(target_nodes) == 1
    assert target_nodes[0]["shape_code"] == "CuRuSuWu"
    assert target_nodes[0]["preview_scene"]["normalized_code"] == "CuRuSuWu"
    assert target_nodes[0]["preview_alt"] == "Graph preview for CuRuSuWu"
    assert target_nodes[0]["preview_image_url"] is None or target_nodes[0][
        "preview_image_url"
    ].endswith(".png")
    assert operation_nodes[0]["operation"]["icon"].startswith("/static/web/images/operations/")
    assert any(edge["label"] == "Output B (unused)" for edge in graph["edges"])


def test_api_solver_solve_rejects_empty_code() -> None:
    response = Client().post(
        "/api/solver/solve/",
        data={"code": ""},
    )

    assert response.status_code == 400
    data = response.json()
    assert data["ok"] is False
    assert data["steps"] == []
    assert data["error"]["code"] == "EMPTY_SHAPE_CODE"
    assert "graph" not in data


def test_api_solver_solve_returns_structured_unsupported_error() -> None:
    response = Client().post(
        "/api/solver/solve/",
        data={"code": "PuPuPuPu"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["error"]["code"] == "UNSUPPORTED_TARGET"
    assert data["error"]["details"]["target_shape_code"] == "PuPuPuPu"


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


def test_api_solver_parse_error_is_structured() -> None:
    response = Client().post("/api/solver/solve/", data={"code": "not_a_real_code!!!"})

    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is False
    assert data["error"]["code"] == "SHAPE_CODE_PARSE_ERROR"


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


def test_solver_graph_viewport_has_explicit_runtime_layout_styles() -> None:
    static_root = Path(settings.BASE_DIR) / "django_apps" / "web" / "static" / "web"
    script = (static_root / "js" / "solver_timeline.js").read_text(encoding="utf-8")
    markup_script = (static_root / "js" / "solver_timeline" / "graph_markup.js").read_text(
        encoding="utf-8"
    )

    assert "data-graph-viewport" in script
    assert 'style="height: 34rem; touch-action: none; cursor: grab;' in script
    assert "transform-origin: 0 0;" in script
    assert 'viewport.style.cursor = "grabbing"' in script
    assert "preview_image_url" in script
    assert "No preview" in script
    assert "data-graph-shape-preview" not in script
    assert "./solver_graph_layout.js" in script
    assert "panel._materializedSolverGraph" in script
    assert "overflow-y-auto" not in markup_script
    assert "L ${geometry.elbowX} ${geometry.y1}" in markup_script
    assert "data-graph-edge-label" in markup_script


def test_operation_icon_assets_exist() -> None:
    static_root = Path(settings.BASE_DIR) / "django_apps" / "web" / "static" / "web"
    operation_root = static_root / "images" / "operations"

    for filename in (
        "color-mixer.png",
        "crystal-generator.png",
        "crystal-generator2.png",
        "cutter.png",
        "cutter2.png",
        "half-destroyer.png",
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
