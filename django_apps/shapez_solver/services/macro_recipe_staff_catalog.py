"""Staff catalog helpers for MacroRecipe + steps (HTTP layer stays in web app)."""

from __future__ import annotations

import secrets
from typing import Any, cast

from django.db import transaction

from django_apps.shapez_solver.models import (
    MacroRecipe,
    MacroRecipeStep,
    PatternFamily,
)
from django_apps.shapez_solver.services.macro_recipe_compiled_boundary import (
    sync_macro_recipe_compiled_boundaries,
)
from django_apps.shapez_solver.services.macro_recipe_payloads import (
    _as_int,
    _non_negative_int,
    _parse_steps,
    _require_family_id,
    _require_short_text,
    _require_strategy_code,
    apply_recipe_update_fields_from_payload,
    replace_recipe_steps_from_payload,
)
from django_apps.shapez_solver.services.macro_recipe_serialization import (
    MACRO_RECIPE_DETAIL_PREFETCHES,
    allowed_strategy_codes,
    build_catalog_snapshot,
    operation_choices,
    serialize_recipe,
)
from django_apps.shapez_solver.services.recipe_graph_cost_hints import graph_cost_hint_from_document
from django_apps.shapez_solver.services.recipe_graph_recompute import (
    default_empty_graph_document,
    try_pattern_macro_step_rows_from_graph_document,
    validate_graph_document,
)

GRAPH_DRAFT_FAMILY_CODE = "graph-draft"


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
    sync_macro_recipe_compiled_boundaries(
        macro, graph_document if isinstance(graph_document, dict) else None
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
        .prefetch_related(*MACRO_RECIPE_DETAIL_PREFETCHES)
        .get(pk=recipe.pk),
    )


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
        .prefetch_related(*MACRO_RECIPE_DETAIL_PREFETCHES)
        .get(pk=recipe.pk),
    )


@transaction.atomic  # type: ignore[untyped-decorator]
def update_recipe(recipe_id: int, payload: dict[str, Any]) -> MacroRecipe:
    try:
        recipe = MacroRecipe.objects.select_for_update().get(pk=recipe_id)
    except MacroRecipe.DoesNotExist as exc:
        raise ValueError("recipe not found") from exc

    apply_recipe_update_fields_from_payload(recipe, recipe_id, payload)

    if "graph_document" in payload:
        raw = payload.get("graph_document")
        recipe.graph_document = None if raw is None else validate_graph_document(raw)

    recipe.save()

    if "graph_document" in payload:
        apply_graph_derived_catalog_fields(
            recipe, recipe.graph_document if recipe.graph_document is not None else None
        )

    if "steps" in payload:
        replace_recipe_steps_from_payload(recipe, payload)

    return cast(
        MacroRecipe,
        MacroRecipe.objects.select_related("family")
        .prefetch_related(*MACRO_RECIPE_DETAIL_PREFETCHES)
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
    "MACRO_RECIPE_DETAIL_PREFETCHES",
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
