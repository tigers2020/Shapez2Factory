"""Staff catalog helpers for MacroRecipe + steps (HTTP layer stays in web app)."""

from __future__ import annotations

import secrets
from typing import Any, cast

from django.db import transaction
from django.db.models import Prefetch
from django.templatetags.static import static

from django_apps.shapez_solver.domain.operation_catalog import OPERATION_CATALOG
from django_apps.shapez_solver.domain.operations import OperationType
from django_apps.shapez_solver.models import MacroRecipe, MacroRecipeStep, PatternFamily
from django_apps.shapez_solver.services.macro_recipe_graph_visual import (
    serialize_macro_recipe_visual,
)
from django_apps.shapez_solver.services.macro_strategy_registry import DEFAULT_MACRO_STRATEGIES
from django_apps.shapez_solver.services.recipe_graph_constants import RECIPE_GRAPH_ENGINE_OPERATIONS
from django_apps.shapez_solver.services.recipe_graph_cost_hints import graph_cost_hint_from_document
from django_apps.shapez_solver.services.recipe_graph_recompute import (
    default_empty_graph_document,
    try_pattern_macro_step_rows_from_graph_document,
    validate_graph_document,
)

GRAPH_DRAFT_FAMILY_CODE = "graph-draft"


def allowed_strategy_codes() -> tuple[str, ...]:
    return tuple(sorted({strategy.code for strategy in DEFAULT_MACRO_STRATEGIES}))


def operation_choices() -> tuple[tuple[str, str], ...]:
    return tuple((item.value, item.name) for item in OperationType)


def catalog_operations_payload() -> list[dict[str, str]]:
    """스태프 UI·팔레트용: 각 연산의 정적 아이콘 URL을 포함한다."""
    rows: list[dict[str, str]] = []
    for val, name in operation_choices():
        icon_url = ""
        try:
            ot = OperationType(val)
            icon_url = static(f"web/images/operations/{OPERATION_CATALOG[ot].icon}")
        except (ValueError, KeyError):
            icon_url = ""
        rows.append({"value": val, "label": name, "icon": icon_url})
    return rows


def default_strategy_code() -> str:
    codes = allowed_strategy_codes()
    if not codes:
        raise ValueError("no macro strategies registered")
    return min(codes)


def _generate_unique_macro_code() -> str:
    for _ in range(64):
        code = f"m-{secrets.token_hex(4)}"
        if not MacroRecipe.objects.filter(code=code).exists():
            return code
    raise RuntimeError("could not allocate unique macro code")


def apply_graph_derived_catalog_fields(
    macro: MacroRecipe, graph_document: dict[str, Any] | None
) -> None:
    """
    ``graph_document`` 구조(연산·shape 노드 수)로 예상 비용과 솔버 정렬용 priority를 맞춘다.

    ``order_by('priority')``에서 낮은 숫자가 먼저이므로, 연산이 많을수록 priority 값을 키워
    후순위로 둔다. graph-draft 패밀리는 스태프 목록 하단에 두기 위해 큰 바이어스를 더한다.
    """

    hint = graph_cost_hint_from_document(graph_document or {})
    op_n = int(hint["operation_node_count"])
    shape_n = int(hint["shape_node_count"])
    stage_n = max(1, int(hint["estimated_stage_count"]))
    macro.estimated_operation_cost = max(1, op_n)
    macro.estimated_stage_cost = stage_n
    macro.estimated_waste_cost = max(0, shape_n - 1)
    base = 100
    span = 8 * max(0, op_n) + 3 * max(0, shape_n - 1)
    rank = base + span
    fam = macro.family
    if fam.code == GRAPH_DRAFT_FAMILY_CODE:
        rank += 50_000
    macro.priority = min(max(rank, 1), 2_000_000)
    macro.save(
        update_fields=[
            "estimated_operation_cost",
            "estimated_stage_cost",
            "estimated_waste_cost",
            "priority",
        ]
    )


@transaction.atomic  # type: ignore[untyped-decorator]
def create_draft_macro_recipe(*, name: str) -> MacroRecipe:
    """
    그래프 우선 편집용 초안 행. ``graph-draft`` 패밀리(placeholder 시그니처)로 만들어
    실제 패턴 시그니처가 정해질 때까지 솔버 매크로 후보에 걸리지 않게 한다.
    """

    text = (name or "").strip() or "Untitled macro"
    if len(text) > 100:
        raise ValueError("name must be at most 100 characters")
    try:
        family = PatternFamily.objects.get(code=GRAPH_DRAFT_FAMILY_CODE)
    except PatternFamily.DoesNotExist as exc:
        raise ValueError("graph-draft pattern family is missing; run migrations") from exc
    recipe = MacroRecipe.objects.create(
        family=family,
        code=_generate_unique_macro_code(),
        strategy_code=default_strategy_code(),
        name=text,
        estimated_operation_cost=1,
        estimated_stage_cost=1,
        estimated_waste_cost=0,
        priority=50_000,
        is_active=True,
        schema_version=1,
    )
    recipe.graph_document = default_empty_graph_document()
    recipe.save(update_fields=["graph_document"])
    apply_graph_derived_catalog_fields(recipe, recipe.graph_document)
    return cast(
        MacroRecipe,
        MacroRecipe.objects.select_related("family")
        .prefetch_related(
            Prefetch("steps", queryset=MacroRecipeStep.objects.order_by("step_index")),
        )
        .get(pk=recipe.pk),
    )


def _serialize_step(step: MacroRecipeStep) -> dict[str, Any]:
    return {
        "id": step.id,
        "step_index": step.step_index,
        "operation": step.operation,
        "input_slots": step.input_slots,
        "output_slots": step.output_slots,
        "note": step.note,
    }


def serialize_recipe(recipe: MacroRecipe, *, sync_png: bool = True) -> dict[str, Any]:
    steps = sorted(recipe.steps.all(), key=lambda s: s.step_index)
    visual_graph = None
    if recipe.graph_document:
        try:
            visual_graph = serialize_macro_recipe_visual(recipe.graph_document, sync_png=sync_png)
        except (ValueError, TypeError, KeyError):
            visual_graph = None
    lab_rows = try_pattern_macro_step_rows_from_graph_document(recipe.graph_document)
    return {
        "id": recipe.id,
        "family_id": recipe.family_id,
        "family_code": recipe.family.code,
        "family_signature": recipe.family.signature,
        "code": recipe.code,
        "strategy_code": recipe.strategy_code,
        "name": recipe.name,
        "estimated_operation_cost": recipe.estimated_operation_cost,
        "estimated_stage_cost": recipe.estimated_stage_cost,
        "estimated_waste_cost": recipe.estimated_waste_cost,
        "priority": recipe.priority,
        "is_active": recipe.is_active,
        "schema_version": recipe.schema_version,
        "graph_document": recipe.graph_document,
        "visual_graph": visual_graph,
        "pattern_lab_steps": lab_rows,
        "steps": [_serialize_step(s) for s in steps],
    }


def build_catalog_snapshot() -> dict[str, Any]:
    families = PatternFamily.objects.order_by("priority", "code").values(
        "id",
        "code",
        "name",
        "signature",
        "is_active",
    )
    recipes = MacroRecipe.objects.select_related("family").prefetch_related(
        Prefetch("steps", queryset=MacroRecipeStep.objects.order_by("step_index"))
    )
    return {
        "families": list(families),
        "recipes": [serialize_recipe(r) for r in recipes.order_by("priority", "code")],
        "strategy_codes": list(allowed_strategy_codes()),
        "operations": catalog_operations_payload(),
        "recipe_graph_engine_operations": sorted(RECIPE_GRAPH_ENGINE_OPERATIONS),
    }


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


@transaction.atomic  # type: ignore[untyped-decorator]
def create_recipe(payload: dict[str, Any]) -> MacroRecipe:
    family_id = _require_family_id(payload.get("family_id"))
    code = _require_short_text(payload.get("code"), "code", max_length=50)
    strategy_code = _require_strategy_code(payload.get("strategy_code"))
    name = _require_short_text(payload.get("name"), "name", max_length=100)
    if MacroRecipe.objects.filter(code=code).exists():
        raise ValueError("code already exists")

    estimated_operation_cost = _non_negative_int(
        payload.get("estimated_operation_cost", 1), "estimated_operation_cost"
    )
    estimated_stage_cost = _non_negative_int(
        payload.get("estimated_stage_cost", 1), "estimated_stage_cost"
    )
    estimated_waste_cost = _non_negative_int(
        payload.get("estimated_waste_cost", 0), "estimated_waste_cost"
    )
    priority = _as_int(payload.get("priority", 100), label="priority")
    is_active = bool(payload.get("is_active", True))
    schema_version = _non_negative_int(payload.get("schema_version", 1), "schema_version")

    recipe = MacroRecipe.objects.create(
        family_id=family_id,
        code=code,
        strategy_code=strategy_code,
        name=name,
        estimated_operation_cost=estimated_operation_cost,
        estimated_stage_cost=estimated_stage_cost,
        estimated_waste_cost=estimated_waste_cost,
        priority=priority,
        is_active=is_active,
        schema_version=schema_version,
    )
    steps = _parse_steps(payload.get("steps"))
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
    if "graph_document" in payload and payload.get("graph_document") is not None:
        recipe.graph_document = validate_graph_document(payload["graph_document"])
    else:
        recipe.graph_document = default_empty_graph_document()
    recipe.save(update_fields=["graph_document"])
    apply_graph_derived_catalog_fields(recipe, recipe.graph_document)
    return cast(
        MacroRecipe,
        MacroRecipe.objects.select_related("family")
        .prefetch_related(
            Prefetch("steps", queryset=MacroRecipeStep.objects.order_by("step_index")),
        )
        .get(pk=recipe.pk),
    )


def _apply_recipe_update_fields(
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


def _replace_recipe_steps_from_payload(recipe: MacroRecipe, payload: dict[str, Any]) -> None:
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


@transaction.atomic  # type: ignore[untyped-decorator]
def update_recipe(recipe_id: int, payload: dict[str, Any]) -> MacroRecipe:
    try:
        recipe = MacroRecipe.objects.select_for_update().get(pk=recipe_id)
    except MacroRecipe.DoesNotExist as exc:
        raise ValueError("recipe not found") from exc

    _apply_recipe_update_fields(recipe, recipe_id, payload)

    if "graph_document" in payload:
        raw = payload.get("graph_document")
        recipe.graph_document = None if raw is None else validate_graph_document(raw)

    recipe.save()

    if "graph_document" in payload:
        apply_graph_derived_catalog_fields(
            recipe, recipe.graph_document if recipe.graph_document is not None else None
        )

    if "steps" in payload:
        _replace_recipe_steps_from_payload(recipe, payload)

    return cast(
        MacroRecipe,
        MacroRecipe.objects.select_related("family")
        .prefetch_related(
            Prefetch("steps", queryset=MacroRecipeStep.objects.order_by("step_index")),
        )
        .get(pk=recipe.pk),
    )


def delete_recipe(recipe_id: int) -> None:
    deleted, _ = MacroRecipe.objects.filter(pk=recipe_id).delete()
    if deleted == 0:
        raise ValueError("recipe not found")


def sync_macro_recipe_steps_from_graph_document(
    macro: MacroRecipe, graph_document: dict[str, Any]
) -> bool:
    """
    ``graph_document``에서 스텝 행을 파생할 수 있으면 ``MacroRecipeStep``을 그 순서로 교체한다.

    파생 불가(``try_pattern_macro_step_rows_from_graph_document``가 ``None``)이면 DB 스텝을
    건드리지 않고 ``False``를 반환한다.
    """

    rows = try_pattern_macro_step_rows_from_graph_document(graph_document)
    if rows is None:
        return False
    MacroRecipeStep.objects.filter(macro=macro).delete()
    if not rows:
        return True
    MacroRecipeStep.objects.bulk_create(
        [
            MacroRecipeStep(
                macro=macro,
                step_index=int(r["step_index"]),
                operation=str(r["operation"]),
                input_slots=list(r.get("input_slots") or []),
                output_slots=list(r.get("output_slots") or []),
                note=str(r.get("note") or ""),
            )
            for r in rows
        ]
    )
    return True


__all__ = [
    "GRAPH_DRAFT_FAMILY_CODE",
    "allowed_strategy_codes",
    "apply_graph_derived_catalog_fields",
    "build_catalog_snapshot",
    "create_draft_macro_recipe",
    "create_recipe",
    "default_strategy_code",
    "delete_recipe",
    "operation_choices",
    "sync_macro_recipe_steps_from_graph_document",
    "serialize_recipe",
    "update_recipe",
]
