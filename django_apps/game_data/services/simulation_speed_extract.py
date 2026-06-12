"""Extract typed fields from simulation_parameters speed blobs (dump-verified shapes)."""

from __future__ import annotations

from enum import StrEnum

DUMP_TYPE_KEY = "$type"
DUMP_TYPE_BUFFABLE = "BuffableBeltSpeed"
DUMP_TYPE_MULTIPLE = "MultipleBeltSpeed"

BUFFABLE_PARAMETER_NAMES = frozenset({"BeltSpeed", "ConveyorSpeed", "SpaceConveyorSpeed"})
MULTIPLE_PARAMETER_NAMES = frozenset({"JumpSpeed"})
SPEED_PARAMETER_NAMES = BUFFABLE_PARAMETER_NAMES | MULTIPLE_PARAMETER_NAMES

REASON_SIM_PARAM_SPEED_SHAPE_MISMATCH = "sim_param_speed_shape_mismatch"
REASON_SIM_PARAM_SPEED_SHAPE_INVALID = "sim_param_speed_shape_invalid"

# Verified on documents/game_data/simulation_systems.json (180 rows, 10 speed blobs).
BUFFABLE_SHAPE = frozenset({"BaseSpeed", "ResearchId", "StepsPerTick", DUMP_TYPE_KEY})
MULTIPLE_SHAPE = frozenset({"BaseSpeed", "Multiplier", "StepsPerTick", DUMP_TYPE_KEY})


class SpeedRoute(StrEnum):
    BUFFABLE = "buffable"
    MULTIPLE = "multiple"
    SKIP = "skip"


class SpeedShapeError(ValueError):
    pass


def dump_type_name(blob: dict[str, object]) -> str:
    return str(blob.get(DUMP_TYPE_KEY, "") or "").strip()


def classify_speed_entry(parameter_name: str, blob: dict[str, object]) -> tuple[SpeedRoute, str]:
    """Route by ``$type`` first, then parameter_name (dump has no cross-type rows)."""
    dtype = dump_type_name(blob)
    if dtype == DUMP_TYPE_MULTIPLE:
        return SpeedRoute.MULTIPLE, dtype
    if dtype == DUMP_TYPE_BUFFABLE:
        return SpeedRoute.BUFFABLE, dtype
    if parameter_name in MULTIPLE_PARAMETER_NAMES:
        return SpeedRoute.MULTIPLE, DUMP_TYPE_MULTIPLE
    if parameter_name in BUFFABLE_PARAMETER_NAMES:
        return SpeedRoute.BUFFABLE, DUMP_TYPE_BUFFABLE
    return SpeedRoute.SKIP, dtype


def parameter_matches_route(parameter_name: str, route: SpeedRoute) -> bool:
    if route == SpeedRoute.BUFFABLE:
        return parameter_name in BUFFABLE_PARAMETER_NAMES
    if route == SpeedRoute.MULTIPLE:
        return parameter_name in MULTIPLE_PARAMETER_NAMES
    return False


def validate_buffable_shape(blob: dict[str, object]) -> list[str]:
    issues: list[str] = []
    extra = set(blob) - BUFFABLE_SHAPE
    if extra:
        issues.append(f"extra_keys:{sorted(extra)}")
    base = blob.get("BaseSpeed")
    if not isinstance(base, str) or not base:
        issues.append("BaseSpeed_not_nonempty_string")
    steps = blob.get("StepsPerTick")
    if steps is not None and not isinstance(steps, (dict, int)) and not isinstance(steps, float):
        issues.append("StepsPerTick_unexpected_type")
    rid = blob.get("ResearchId")
    if rid is not None and not isinstance(rid, dict):
        issues.append("ResearchId_not_object")
    return issues


def validate_multiple_shape(blob: dict[str, object]) -> list[str]:
    issues: list[str] = []
    extra = set(blob) - MULTIPLE_SHAPE
    if extra:
        issues.append(f"extra_keys:{sorted(extra)}")
    base = blob.get("BaseSpeed")
    if not isinstance(base, dict) or "$cycle" not in base:
        issues.append("BaseSpeed_missing_cycle_ref")
    elif not str(base.get("$cycle", "")).strip():
        issues.append("BaseSpeed_empty_cycle_ref")
    if blob.get("Multiplier") is None:
        issues.append("Multiplier_missing")
    steps = blob.get("StepsPerTick")
    if steps is not None and not isinstance(steps, (dict, int)) and not isinstance(steps, float):
        issues.append("StepsPerTick_unexpected_type")
    return issues


def steps_per_tick_value(raw: object) -> int:
    if isinstance(raw, dict):
        val = raw.get("Value", 0)
        return int(val or 0)
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        return int(raw)
    return 0


def research_upgrade_key(blob: dict[str, object]) -> str:
    rid = blob.get("ResearchId")
    if not isinstance(rid, dict):
        return ""
    key = rid.get("Id", "")
    if isinstance(key, dict):
        return str(key.get("Name", "") or key.get("Id", "") or "")[:255]
    return str(key or "")[:255]


def parse_buffable_speed_blob(parameter_name: str, blob: dict[str, object]) -> dict[str, object]:
    issues = validate_buffable_shape(blob)
    if issues:
        raise SpeedShapeError(f"{parameter_name}: {issues}")
    return {
        "parameter_name": parameter_name[:100],
        "dump_type": dump_type_name(blob) or DUMP_TYPE_BUFFABLE,
        "base_speed": str(blob.get("BaseSpeed", ""))[:64],
        "research_upgrade_key": research_upgrade_key(blob),
        "steps_per_tick": steps_per_tick_value(blob.get("StepsPerTick")),
    }


def parse_multiple_speed_blob(parameter_name: str, blob: dict[str, object]) -> dict[str, object]:
    issues = validate_multiple_shape(blob)
    if issues:
        raise SpeedShapeError(f"{parameter_name}: {issues}")
    cycle_ref = ""
    base = blob.get("BaseSpeed")
    if isinstance(base, dict):
        cycle_ref = str(base.get("$cycle", "") or "")[:64]
    return {
        "parameter_name": parameter_name[:100],
        "dump_type": dump_type_name(blob) or DUMP_TYPE_MULTIPLE,
        "cycle_ref_type": cycle_ref,
        "multiplier": int(blob.get("Multiplier", 0) or 0),
        "steps_per_tick": steps_per_tick_value(blob.get("StepsPerTick")),
    }
