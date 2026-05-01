from __future__ import annotations

import inspect

import django_apps.web.services.shape_svg_renderer as renderer_module
from django_apps.web.services.shape_svg_renderer import render_shape_pattern_svg
from shapez2_solver.application.shape_code_parser import parse_shape_code_list


def _render(code: str) -> str:
    pattern = parse_shape_code_list(code)[0]
    return render_shape_pattern_svg(pattern)


def test_render_shape_pattern_svg_emits_accessible_svg() -> None:
    svg = _render("SrSrSrSr")

    assert svg.startswith('<svg class="shape-preview"')
    assert 'xmlns="http://www.w3.org/2000/svg"' in svg
    assert 'aria-label="SrSrSrSr"' in svg


def test_render_shape_pattern_svg_supports_quadrant_path_shapes() -> None:
    for code in ("RrRrRrRr", "CrCrCrCr", "SrSrSrSr", "WrWrWrWr"):
        svg = _render(code)

        assert svg.count("<path ") == 4
        assert 'stroke="#2b242c"' in svg


def test_render_shape_pattern_svg_spikes_form_diagonal_x() -> None:
    svg = _render("SrSrSrSr")

    assert "L224 28" in svg
    assert "L232 220" in svg
    assert "L32 228" in svg
    assert "L24 36" in svg


def test_render_shape_pattern_svg_supports_crystals_and_pins() -> None:
    crystal_svg = _render("cccccccc")
    pin_svg = _render("PuPuPuPu")

    assert crystal_svg.count("<path ") == 4
    assert 'fill="#2ec4b6"' in crystal_svg
    assert 'fill-opacity="0.86"' in crystal_svg
    assert pin_svg.count("<circle ") == 6


def test_render_shape_pattern_svg_skips_empty_quadrants() -> None:
    svg = _render("Ru------")

    assert svg.count("<path ") == 1
    assert 'fill="transparent"' not in svg


def test_render_shape_pattern_svg_draws_layers_bottom_to_top() -> None:
    svg = _render("RuRuRuRu:WrCrRgSy")

    assert svg.count("<g ") == 2
    assert "scale(1.00)" in svg
    assert "scale(0.82)" in svg
    assert svg.index("scale(1.00)") < svg.index("scale(0.82)")


def test_shape_svg_renderer_does_not_import_parser() -> None:
    source = inspect.getsource(renderer_module)

    assert "parse_shape_code" not in source
