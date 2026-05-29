"""Layer 03 resource_kind derivation at the L2 plan boundary."""

from __future__ import annotations

from django_apps.asteroid_lab.layers.contracts.exterior_connection import ExteriorConnectionPlan
from django_apps.asteroid_lab.layers.contracts.transport_kind import (
    ResourceKind,
    resource_kind_from_plan_string,
)


def derive_layer03_resource_kind(
    exterior_plan: ExteriorConnectionPlan,
    explicit: ResourceKind | None = None,
) -> ResourceKind:
    if explicit is not None:
        return explicit
    return resource_kind_from_plan_string(exterior_plan.transport_kind)


__all__ = ["derive_layer03_resource_kind"]
