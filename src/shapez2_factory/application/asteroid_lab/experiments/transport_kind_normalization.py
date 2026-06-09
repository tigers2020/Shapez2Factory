"""Normalize resource and transport layout kinds to a shared transport family."""

from __future__ import annotations

from enum import Enum

_SHAPE_FAMILIES = frozenset(
    {"shape", "shape_belt", "space_belt", "belt"},
)
_FLUID_FAMILIES = frozenset(
    {"fluid", "fluid_pipe", "space_pipe", "pipe"},
)


def _kind_token(kind: object) -> str:
    if isinstance(kind, Enum):
        return str(kind.value).lower()
    return str(kind).lower()


def normalize_transport_family(kind: object) -> str | None:
    """Map exterior resource kind or route transport kind to ``shape`` / ``fluid``."""
    value = _kind_token(kind)
    if value in _SHAPE_FAMILIES:
        return "shape"
    if value in _FLUID_FAMILIES:
        return "fluid"
    return None


def transport_families_compatible(
    *,
    exterior_transport_kind: object,
    route_transport_kind: object,
) -> bool:
    exterior_family = normalize_transport_family(exterior_transport_kind)
    route_family = normalize_transport_family(route_transport_kind)
    if exterior_family is None or route_family is None:
        return False
    return exterior_family == route_family


def format_transport_kind_mismatch_diagnostic(
    *,
    exterior_transport_kind: object,
    route_transport_kind: object,
) -> str:
    exterior_family = normalize_transport_family(exterior_transport_kind)
    route_family = normalize_transport_family(route_transport_kind)
    return (
        "transport_kind_mismatch:"
        f"exterior={exterior_transport_kind},"
        f"route={route_transport_kind},"
        f"exterior_family={exterior_family},"
        f"route_family={route_family}"
    )


__all__ = [
    "format_transport_kind_mismatch_diagnostic",
    "normalize_transport_family",
    "transport_families_compatible",
]
