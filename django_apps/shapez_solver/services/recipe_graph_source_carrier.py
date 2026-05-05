"""Recipe graph: ``source_carrier=fluid`` and primary-only ink rules."""

from __future__ import annotations

from django_apps.shapez_core.domain.shape_catalog import FLUID_SOURCE_PRIMARY_COLORS
from django_apps.shapez_solver.services.fluid_semantics import pure_fluid_color
from django_apps.shapez_solver.services.operation_semantics import parse_shape


def assert_source_fluid_shape_valid(shape_code: str, *, index: int, node_id: str) -> None:
    """``source_carrier`` 유체 소스의 ``shape_code``는 순수 유체이며 색은 r|g|b만."""

    try:
        shape = parse_shape(shape_code)
        letter = pure_fluid_color(shape)
    except ValueError as exc:
        raise ValueError(
            f"nodes[{index}] ({node_id}): fluid source must be pure fluid shape_code: {exc}",
        ) from exc
    if letter not in FLUID_SOURCE_PRIMARY_COLORS:
        raise ValueError(
            f"nodes[{index}] ({node_id}): fluid source allows only primary ink "
            f"r|g|b, got {letter!r}",
        )


def assert_intermediate_fluid_shape_valid(shape_code: str, *, index: int, node_id: str) -> None:
    """유체 intermediate: 순수 유체(보조색 허용)."""

    try:
        shape = parse_shape(shape_code)
        pure_fluid_color(shape)
    except ValueError as exc:
        raise ValueError(
            f"nodes[{index}] ({node_id}): fluid intermediate must be pure fluid shape_code: {exc}",
        ) from exc


def assert_fluid_carrier_shape_for_role(
    role: str,
    shape_code: str,
    *,
    index: int,
    node_id: str,
) -> None:
    if role == "intermediate" and not str(shape_code).strip():
        return
    if role == "source":
        assert_source_fluid_shape_valid(shape_code, index=index, node_id=node_id)
    elif role == "intermediate":
        assert_intermediate_fluid_shape_valid(shape_code, index=index, node_id=node_id)


__all__ = [
    "assert_fluid_carrier_shape_for_role",
    "assert_intermediate_fluid_shape_valid",
    "assert_source_fluid_shape_valid",
]
