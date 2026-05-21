"""Detect simulation_parameters profile from dump row (simulation_parameters only)."""

from __future__ import annotations

from typing import Any

PROFILE_FACTORY = "factory"
PROFILE_CONNECTABLE = "connectable_graph"
PROFILE_CONVERTER = "converter_runtime"
PROFILE_BELT = "belt_policy"
PROFILE_OTHER = "other"


def detect_simulation_profile_key(
    params: dict[str, Any],
    *,
    source_type_name: str = "",
) -> str:
    if not isinstance(params, dict):
        return PROFILE_OTHER

    if params.get("ConnectableSimulations"):
        return PROFILE_CONNECTABLE

    if params.get("BeltSpeed") is not None:
        return PROFILE_BELT

    stype = source_type_name or ""
    if "SpaceConverterSystem" in stype or "Converters.SpaceConverter" in stype:
        return PROFILE_CONVERTER

    if "SimulationFactory" in params and len(params) <= 2:
        return PROFILE_FACTORY

    delegate_keys = [k for k in params if k.startswith("ISimulationSystem.")]
    if delegate_keys and len(params) > 3:
        return PROFILE_CONVERTER

    if params.get("SimulationFactory") is not None:
        return PROFILE_FACTORY

    return PROFILE_OTHER
