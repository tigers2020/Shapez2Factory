"""Persistent L2 exterior connector overlay rows from plan wire (SoT)."""

from __future__ import annotations

from django_apps.asteroid_lab.replay.persistent_connector_overlay_wire import (
    PersistentConnectorOverlayWire,
)
from django_apps.asteroid_lab.replay.persistent_exterior_overlay import (
    persistent_connector_overlays_from_wire,
)
from tests.unit.asteroid_lab.replay.fixtures.replay_assembler_fixtures import (
    exterior_plan_wire_for_golden,
)


def test_persistent_connector_overlay_wire_exports() -> None:
    assert PersistentConnectorOverlayWire.__name__ == "PersistentConnectorOverlayWire"


def test_persistent_overlay_from_wire_has_planned_role() -> None:
    wire = exterior_plan_wire_for_golden()
    rows = persistent_connector_overlays_from_wire(wire)
    assert rows
    assert all(r["overlay_role"] == "planned_exterior_connector" for r in rows)
    assert all("x" in r and "y" in r for r in rows)
    assert all(r["connector_role"] in {"required", "spare"} for r in rows)
