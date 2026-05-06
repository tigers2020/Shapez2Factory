"""Parse and validate staff/API payloads for MacroRecipe CRUD."""

from __future__ import annotations

from typing import Any

from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.models import MacroRecipe, MacroRecipeStep, PatternFamily
from django_apps.shapez_solver.services.macro_recipe_serialization import allowed_strategy_codes


def _parse_one_step_dict(item: dict[str, Any]) -> dict[str, Any]:
    try:
        step_index = int(item["step_index"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError("step_index must be a positive integer") from exc
    if step_index < 1:
        raise ValueError("step_index must be >= 1")
    operation = item.get("operation")
    if not isinstance(operation, str) or not operation.strip():
        raise ValueError("operation is required")
    operation = operation.strip()
    valid_ops = {op.value for op in OperationType}
    if operation not in valid_ops:
        raise ValueError(f"unknown operation: {operation}")
    input_slots = item.get("input_slots", [])
    output_slots = item.get("output_slots", [])
    if not isinstance(input_slots, list):
        raise ValueError("input_slots must be a list")
    if not isinstance(output_slots, list):
        raise ValueError("output_slots must be a list")
    note = item.get("note", "")
    if note is not None and not isinstance(note, str):
        raise ValueError("note must be a string")
    return {
        "step_index": step_index,
        "operation": operation,
        "input_slots": input_slots,
        "output_slots": output_slots,
        "note": note or "",
    }


def _parse_steps(raw: object) -> list[dict[str, Any]]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise ValueError("steps must be a list")
    out: list[dict[str, Any]] = []
    for item in raw:
        if not isinstance(item, dict):
            raise ValueError("each step must be an object")
        out.append(_parse_one_step_dict(item))
    indices = [s["step_index"] for s in out]
    if len(set(indices)) != len(indices):
        raise ValueError("duplicate step_index")
    return sorted(out, key=lambda s: s["step_index"])


def _as_int(value: object, *, label: str) -> int:
    if isinstance(value, bool):
        raise ValueError(f"{label} must be an integer")
    if isinstance(value, int):
        return value
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError as exc:
            raise ValueError(f"{label} must be an integer") from exc
    raise ValueError(f"{label} must be an integer")


def _require_family_id(raw: object) -> int:
    if raw is None:
        raise ValueError("family_id is required")
    family_id_int = _as_int(raw, label="family_id")
    if not PatternFamily.objects.filter(pk=family_id_int).exists():
        raise ValueError("unknown family_id")
    return family_id_int


def _require_slug_text(raw: object, label: str) -> str:
    if not isinstance(raw, str) or not raw.strip():
        raise ValueError(f"{label} is required")
    return raw.strip()


def _require_short_text(raw: object, label: str, *, max_length: int) -> str:
    text = _require_slug_text(raw, label)
    if len(text) > max_length:
        raise ValueError(f"{label} must be at most {max_length} characters")
    return text


def _require_strategy_code(raw: object) -> str:
    code = _require_slug_text(raw, "strategy_code")
    allowed = allowed_strategy_codes()
    if code not in allowed:
        raise ValueError(f"strategy_code must be one of: {', '.join(allowed)}")
    return code


def _non_negative_int(raw: object, label: str) -> int:
    v = _as_int(raw, label=label)
    if v < 0:
        raise ValueError(f"{label} must be a non-negative integer")
    return v


def apply_recipe_update_fields_from_payload(
    recipe: MacroRecipe, recipe_id: int, payload: dict[str, Any]
) -> None:
    if "family_id" in payload:
        recipe.family_id = _require_family_id(payload.get("family_id"))
    if "code" in payload:
        code = _require_short_text(payload.get("code"), "code", max_length=50)
        if MacroRecipe.objects.filter(code=code).exclude(pk=recipe_id).exists():
            raise ValueError("code already exists")
        recipe.code = code
    if "strategy_code" in payload:
        recipe.strategy_code = _require_strategy_code(payload.get("strategy_code"))
    if "name" in payload:
        recipe.name = _require_short_text(payload.get("name"), "name", max_length=100)
    if "estimated_operation_cost" in payload:
        recipe.estimated_operation_cost = _non_negative_int(
            payload.get("estimated_operation_cost"), "estimated_operation_cost"
        )
    if "estimated_stage_cost" in payload:
        recipe.estimated_stage_cost = _non_negative_int(
            payload.get("estimated_stage_cost"), "estimated_stage_cost"
        )
    if "estimated_waste_cost" in payload:
        recipe.estimated_waste_cost = _non_negative_int(
            payload.get("estimated_waste_cost"), "estimated_waste_cost"
        )
    if "priority" in payload:
        recipe.priority = _as_int(payload["priority"], label="priority")
    if "is_active" in payload:
        recipe.is_active = bool(payload["is_active"])
    if "schema_version" in payload:
        recipe.schema_version = _non_negative_int(payload.get("schema_version"), "schema_version")


def replace_recipe_steps_from_payload(recipe: MacroRecipe, payload: dict[str, Any]) -> None:
    steps = _parse_steps(payload.get("steps"))
    recipe.steps.all().delete()
    MacroRecipeStep.objects.bulk_create(
        [
            MacroRecipeStep(
                macro=recipe,
                step_index=s["step_index"],
                operation=s["operation"],
                input_slots=s["input_slots"],
                output_slots=s["output_slots"],
                note=s["note"],
            )
            for s in steps
        ]
    )
