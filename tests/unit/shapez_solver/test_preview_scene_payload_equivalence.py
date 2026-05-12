"""``preview_scene`` JSON contract: core demo row vs graph preview builder."""

from __future__ import annotations

from django_apps.shapez_core.services.preview_service import build_demo_parse_row
from django_apps.shapez_solver.view_graph_serialization import build_preview_scene


def test_demo_parse_preview_scene_matches_graph_build_preview_scene() -> None:
    code = "RuCuSuWu:WrCrRgSy"
    row = build_demo_parse_row(code)
    assert row["ok"] is True
    from_demo = row["patterns"][0]["preview_scene"]
    from_graph = build_preview_scene(code, source_carrier=None)
    assert from_demo == from_graph
