"""Layer 03 resource vs transport kind enums and L2 plan string mapping."""

from __future__ import annotations

from enum import StrEnum


class ResourceKind(StrEnum):
    SHAPE = "shape"
    FLUID = "fluid"


class TransportKind(StrEnum):
    SPACE_BELT = "space_belt"
    SPACE_PIPE = "space_pipe"


def map_resource_kind_to_transport_kind(resource_kind: ResourceKind) -> TransportKind:
    if resource_kind == ResourceKind.SHAPE:
        return TransportKind.SPACE_BELT
    if resource_kind == ResourceKind.FLUID:
        return TransportKind.SPACE_PIPE
    msg = f"unknown resource_kind: {resource_kind!r}"
    raise ValueError(msg)


def resource_kind_from_plan_string(value: str) -> ResourceKind:
    normalized = value.strip().lower()
    if normalized == ResourceKind.SHAPE.value:
        return ResourceKind.SHAPE
    if normalized == ResourceKind.FLUID.value:
        return ResourceKind.FLUID
    msg = f"unknown plan transport_kind string: {value!r}"
    raise ValueError(msg)


__all__ = [
    "ResourceKind",
    "TransportKind",
    "map_resource_kind_to_transport_kind",
    "resource_kind_from_plan_string",
]
