"""Rebuild persistent L2 exterior connector overlay rows from plan wire (SoT)."""

from __future__ import annotations

from collections.abc import Mapping

from django_apps.asteroid_lab.replay.persistent_connector_overlay_wire import (
    PersistentConnectorOverlayWire,
)
from django_apps.asteroid_lab.services.lab_timeline_exterior_connector_enrichment import (
    planned_connector_overlays_from_wire,
)


def persistent_connector_overlays_from_wire(
    plan_wire: Mapping[str, object],
) -> list[PersistentConnectorOverlayWire]:
    """SoT: ``exterior_connector_plan.planned_connectors[].void_coord`` — not L2 frame overlay."""

    return planned_connector_overlays_from_wire(dict(plan_wire))


__all__ = ["persistent_connector_overlays_from_wire"]
