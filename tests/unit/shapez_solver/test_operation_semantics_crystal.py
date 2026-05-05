"""Crystal generator branch of ``apply_operation``."""

import pytest

from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.services.operation_semantics import (
    apply_operation,
    infer_uniform_shape_color,
)


def test_apply_crystal_generator_with_crystal_color_kwarg() -> None:
    out = apply_operation(
        OperationType.CRYSTAL_GENERATOR,
        ("Ru--Ru--", "CuCuCuCu"),
        crystal_color="c",
    )[0]
    assert out == "RuccRucc"


def test_apply_crystal_generator_two_inputs_fluid_then_shape() -> None:
    """Graph order: slot ``1`` (fluid) then bare ``in`` (target shape)."""
    out = apply_operation(
        OperationType.CRYSTAL_GENERATOR,
        ("CrCrCrCr", "Ru--Ru--"),
    )[0]
    assert out == "RucrRucr"


def test_infer_uniform_shape_color_mixed_returns_none() -> None:
    assert infer_uniform_shape_color("CrCgCrCg") is None


def test_apply_crystal_generator_raises_without_color_or_fluid_shape_pair() -> None:
    with pytest.raises(ValueError, match="crystal_generator requires"):
        apply_operation(OperationType.CRYSTAL_GENERATOR, ("Ru--Ru--",))
