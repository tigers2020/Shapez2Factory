"""Classify simulation_parameters top-level keys (registry only; no values)."""

from __future__ import annotations

from django.db import models

_DOMAIN_CONFIG_KEYS = frozenset(
    {
        "SimulationFactory",
        "ConnectableSimulations",
        "ConveyorSpeed",
        "SpaceConveyorSpeed",
        "JumpSpeed",
        "BeltSpeed",
        "MaxUnlockedLayer",
        "BeltPortSenderBuildingId",
        "FluidWagonType",
        "ShapeWagonType",
        "FluidTrainExchangerDefinitionIds",
        "ShapeTransferDefinitionIds",
    }
)

_EVENT_DELEGATE_KEYS = frozenset(
    {
        "OnSimulationCreated",
        "OnBeforeSimulationDestroyed",
    }
)

_RUNTIME_STATE_KEYS = frozenset(
    {
        "Simulations",
        "ConnectableSimulationsByPosition",
        "ReceivedShapes",
    }
)

_CACHE_SNAPSHOT_KEYS = frozenset({"ShapeRegistry"})

_REFLECTION_EXACT_KEYS = frozenset(
    {
        "Logger",
        "Method",
        "MethodHandle",
        "RuntimeMethodInfo",
        "Module",
        "ReflectedTypeInternal",
        "ReturnParameter",
        "Listeners",
    }
)

_REFLECTION_PREFIXES = (
    "ISimulationSystem.",
    "ISpecializedIslandTenantSimulationSystem.",
    "IShapeCollectorSystem.",
)


class ParameterClassification(models.TextChoices):
    DOMAIN_CONFIG = "domain_config", "Domain config"
    RUNTIME_STATE = "runtime_state", "Runtime state"
    EVENT_DELEGATE = "event_delegate", "Event delegate"
    REFLECTION_DUMP = "reflection_dump", "Reflection dump"
    CACHE_SNAPSHOT = "cache_snapshot", "Cache snapshot"
    IGNORED_RUNTIME = "ignored_runtime", "Ignored runtime"
    UNKNOWN = "unknown", "Unknown"


def classify_simulation_parameter_key(name: str) -> str:
    key = (name or "").strip()
    if not key:
        return ParameterClassification.UNKNOWN

    if key in _DOMAIN_CONFIG_KEYS:
        return ParameterClassification.DOMAIN_CONFIG
    if key in _EVENT_DELEGATE_KEYS:
        return ParameterClassification.EVENT_DELEGATE
    if key in _RUNTIME_STATE_KEYS:
        return ParameterClassification.RUNTIME_STATE
    if key in _CACHE_SNAPSHOT_KEYS:
        return ParameterClassification.CACHE_SNAPSHOT
    if key in _REFLECTION_EXACT_KEYS:
        return ParameterClassification.REFLECTION_DUMP
    if key.startswith("$"):
        return ParameterClassification.IGNORED_RUNTIME
    if any(key.startswith(prefix) for prefix in _REFLECTION_PREFIXES):
        return ParameterClassification.REFLECTION_DUMP

    return ParameterClassification.UNKNOWN


# reason_code values stored on UnknownProperty (simulation_parameters ignores)
REASON_SIM_PARAM_EVENT_DELEGATE = "sim_param_event_delegate"
REASON_SIM_PARAM_REFLECTION_DUMP = "sim_param_reflection_dump"
REASON_SIM_PARAM_RUNTIME_STATE = "sim_param_runtime_state"
REASON_SIM_PARAM_CACHE_SNAPSHOT = "sim_param_cache_snapshot"
REASON_SIM_PARAM_IGNORED_RUNTIME = "sim_param_ignored_runtime"

_SIM_PARAM_REASON_BY_CLASSIFICATION: dict[str, str] = {
    ParameterClassification.EVENT_DELEGATE: REASON_SIM_PARAM_EVENT_DELEGATE,
    ParameterClassification.REFLECTION_DUMP: REASON_SIM_PARAM_REFLECTION_DUMP,
    ParameterClassification.RUNTIME_STATE: REASON_SIM_PARAM_RUNTIME_STATE,
    ParameterClassification.CACHE_SNAPSHOT: REASON_SIM_PARAM_CACHE_SNAPSHOT,
    ParameterClassification.IGNORED_RUNTIME: REASON_SIM_PARAM_IGNORED_RUNTIME,
}

NON_DOMAIN_SIM_PARAM_CLASSIFICATIONS = frozenset(_SIM_PARAM_REASON_BY_CLASSIFICATION.keys())

SIM_PARAM_IGNORE_REASON_PREFIX = "sim_param_"


def is_non_domain_simulation_parameter(classification: str) -> bool:
    return classification in NON_DOMAIN_SIM_PARAM_CLASSIFICATIONS


def reason_code_for_simulation_parameter(classification: str) -> str:
    return _SIM_PARAM_REASON_BY_CLASSIFICATION.get(classification, "")
