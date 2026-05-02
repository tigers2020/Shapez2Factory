import pytest

from django_apps.shapez_core.domain.shape import Shape
from django_apps.shapez_core.services.shape_code_parser import parse_shape_code_list
from django_apps.shapez_core.services.shape_codec import shape_from_pattern
from django_apps.shapez_solver.domain.factory_demand import (
    BaseDemand,
    UnsupportedFactoryDemandError,
    compute_base_demands,
)


def _shape(code: str) -> Shape:
    return shape_from_pattern(parse_shape_code_list(code)[0])


def test_compute_base_demands_for_cu_ru_su_su_auto_lcm() -> None:
    demands = compute_base_demands(_shape("CuRuSuSu"))

    assert demands == (
        BaseDemand(
            base_shape_code="CuCuCuCu",
            quadrants_per_target=1,
            total_quadrants=4,
            full_source_count=1,
        ),
        BaseDemand(
            base_shape_code="RuRuRuRu",
            quadrants_per_target=1,
            total_quadrants=4,
            full_source_count=1,
        ),
        BaseDemand(
            base_shape_code="SuSuSuSu",
            quadrants_per_target=2,
            total_quadrants=8,
            full_source_count=2,
        ),
    )


def test_compute_base_demands_ignores_color_and_uses_uncolored_skeleton() -> None:
    uncolored_demands = compute_base_demands(_shape("CuRuSuSu"))
    colored_demands = compute_base_demands(_shape("CrRgSbSy"))

    assert colored_demands == uncolored_demands


def test_compute_base_demands_rejects_multi_layer_target() -> None:
    with pytest.raises(UnsupportedFactoryDemandError, match="single-layer"):
        compute_base_demands(_shape("CuRuSuSu:WuWuWuWu"))


def test_compute_base_demands_rejects_pin_and_crystal_materials() -> None:
    with pytest.raises(UnsupportedFactoryDemandError, match="pin or crystal"):
        compute_base_demands(_shape("PuPuPuPu"))

    with pytest.raises(UnsupportedFactoryDemandError, match="pin or crystal"):
        compute_base_demands(_shape("cu----cu"))
