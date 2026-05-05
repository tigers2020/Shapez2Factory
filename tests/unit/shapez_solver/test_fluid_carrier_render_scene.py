from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_solver.services.fluid_carrier_render_scene import (
    FLUID_CARRIER_MESH_KEY,
    build_fluid_carrier_preview_scene,
)
from django_apps.shapez_solver.view_graph_serialization import build_preview_scene


def test_build_preview_scene_fluid_carrier_single_tank_cell() -> None:
    out = build_preview_scene("CrCrCrCr", source_carrier="fluid")
    assert len(out["cells"]) == 1
    assert out["cells"][0]["mesh_key"] == FLUID_CARRIER_MESH_KEY
    assert out["cells"][0]["material_key"] == "r"


def test_build_preview_scene_without_carrier_uses_quadrants() -> None:
    out = build_preview_scene("CrCrCrCr")
    assert len(out["cells"]) == 4
    assert all(c["mesh_key"] == "default_circle" for c in out["cells"])


def test_build_fluid_carrier_preview_scene_mixed_ink_falls_back() -> None:
    pattern = parse_shape_code_list("CrCgCrCr")[0]
    scene = build_fluid_carrier_preview_scene(pattern)
    assert len(scene.cells) == 4
