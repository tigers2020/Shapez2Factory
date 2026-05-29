"""Rebuild persistent L2 exterior connector overlay rows from plan wire (SoT)."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from django_apps.asteroid_lab.services.lab_timeline_exterior_connector_enrichment import (
    _planned_connectors,
)


def persistent_connector_overlays_from_wire(
    plan_wire: Mapping[str, object],
) -> list[dict[str, Any]]:
    """SoT: ``exterior_connector_plan.planned_connectors[].void_coord`` — not L2 frame overlay."""

    return list(_planned_connectors(dict(plan_wire)))


__all__ = ["persistent_connector_overlays_from_wire"]
