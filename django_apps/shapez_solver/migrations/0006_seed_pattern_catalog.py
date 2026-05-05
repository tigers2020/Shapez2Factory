"""Seed PatternFamily / MacroRecipe / MacroRecipeStep catalog (canonical defaults).

Reverse is intentionally noop — rolling back would require CASCADE-safe teardown.
"""

from django.db import migrations


def _noop_reverse(apps, schema_editor) -> None:
    """Keep seeded catalog rows on migration rollback."""
    del apps, schema_editor


def _ensure_pattern_families(pattern_family_model, macro_recipe_model) -> None:
    """Upsert six canonical families; migrate legacy ``abcc-batch`` family code."""
    has_legacy = pattern_family_model.objects.filter(code="abcc-batch").exists()
    has_pair = pattern_family_model.objects.filter(code="pair-plus-singles").exists()
    if has_legacy and has_pair:
        legacy = pattern_family_model.objects.get(code="abcc-batch")
        canonical = pattern_family_model.objects.get(code="pair-plus-singles")
        macro_recipe_model.objects.filter(family_id=legacy.pk).update(family_id=canonical.pk)
        legacy.delete()
    elif has_legacy:
        pattern_family_model.objects.filter(code="abcc-batch").update(code="pair-plus-singles")

    families = (
        {
            "code": "full-source",
            "name": "Full Source",
            "signature": "AAAA",
            "description": "단일 full source 패턴 (4사분면 동일)",
            "allow_rotation": True,
            "allow_reflection": True,
            "priority": 10,
            "is_active": True,
            "schema_version": 1,
        },
        {
            "code": "half-split",
            "name": "Half Split",
            "signature": "AABB",
            "description": "인접 2+2 (두 종류가 반쪽씩)",
            "allow_rotation": True,
            "allow_reflection": True,
            "priority": 20,
            "is_active": True,
            "schema_version": 1,
        },
        {
            "code": "checker",
            "name": "Checker",
            "signature": "ABAB",
            "description": "교차 2+2 (체커)",
            "allow_rotation": True,
            "allow_reflection": True,
            "priority": 30,
            "is_active": True,
            "schema_version": 1,
        },
        {
            "code": "pair-plus-singles",
            "name": "Pair Plus Singles",
            "signature": "ABCC",
            "description": (
                "2+1+1 Bell 클래스. 대표 문자열은 사분면 순서에 따라 ABCC·AABC 등이 될 수 있으나, "
                "매크로·pattern_signature 연동은 ABCC 기준(문서 참조)"
            ),
            "allow_rotation": True,
            "allow_reflection": True,
            "priority": 40,
            "is_active": True,
            "schema_version": 1,
        },
        {
            "code": "single-different",
            "name": "Single Different",
            "signature": "AAAB",
            "description": "3개 동일 + 1개 다른 사분면 (3+1)",
            "allow_rotation": True,
            "allow_reflection": True,
            "priority": 15,
            "is_active": True,
            "schema_version": 1,
        },
        {
            "code": "full-mixed",
            "name": "Full Mixed",
            "signature": "ABCD",
            "description": "네 사분면이 모두 다른 토큰 (4-way)",
            "allow_rotation": True,
            "allow_reflection": True,
            "priority": 50,
            "is_active": True,
            "schema_version": 1,
        },
    )
    for row in families:
        code = row.pop("code")
        pattern_family_model.objects.update_or_create(code=code, defaults=row)


def _replace_macro_steps(step_model, macro, steps: tuple[dict, ...]) -> None:
    step_model.objects.filter(macro_id=macro.pk).delete()
    step_model.objects.bulk_create(
        [
            step_model(
                macro_id=macro.pk,
                step_index=s["step_index"],
                operation=s["operation"],
                input_slots=list(s["input_slots"]),
                output_slots=list(s["output_slots"]),
                note=s["note"],
            )
            for s in steps
        ]
    )


def forwards_seed_pattern_catalog(apps, schema_editor) -> None:
    PatternFamily = apps.get_model("shapez_solver", "PatternFamily")
    MacroRecipe = apps.get_model("shapez_solver", "MacroRecipe")
    MacroRecipeStep = apps.get_model("shapez_solver", "MacroRecipeStep")

    _ensure_pattern_families(PatternFamily, MacroRecipe)

    checker = PatternFamily.objects.get(code="checker")
    pair_family = PatternFamily.objects.get(code="pair-plus-singles")

    checker_macro, _ = MacroRecipe.objects.update_or_create(
        code="swap-rotate-swap-checker",
        defaults={
            "family_id": checker.pk,
            "strategy_code": "CHECKER_PAIR",
            "name": "Swap Rotate Swap Checker",
            "estimated_operation_cost": 5,
            "estimated_stage_cost": 5,
            "estimated_waste_cost": 0,
            "priority": 10,
            "is_active": True,
            "schema_version": 1,
            "graph_document": None,
        },
    )
    abcc_macro, _ = MacroRecipe.objects.update_or_create(
        code="abcc-batch",
        defaults={
            "family_id": pair_family.pk,
            "strategy_code": "ABCC_BATCH",
            "name": "ABCC Batch",
            "estimated_operation_cost": 21,
            "estimated_stage_cost": 21,
            "estimated_waste_cost": 0,
            "priority": 10,
            "is_active": True,
            "schema_version": 1,
            "graph_document": None,
        },
    )

    checker_steps = (
        {
            "step_index": 1,
            "operation": "swapper",
            "input_slots": ["A_full", "B_full"],
            "output_slots": ["mixed_0", "mixed_1"],
            "note": "서로 다른 full source 두 개를 교차 배치 후보로 나눈다.",
        },
        {
            "step_index": 2,
            "operation": "rotate_cw",
            "input_slots": ["mixed_0", "mixed_1"],
            "output_slots": ["rotated_0", "rotated_1"],
            "note": "두 swapper output을 같은 방향으로 회전한다.",
        },
        {
            "step_index": 3,
            "operation": "swapper",
            "input_slots": ["rotated_0", "rotated_1"],
            "output_slots": ["checker_0", "checker_1"],
            "note": "회전된 반쪽을 다시 교차해 ABAB target 후보를 만든다.",
        },
    )
    abcc_steps = (
        {
            "step_index": 1,
            "operation": "swapper",
            "input_slots": ["A_full", "B_full"],
            "output_slots": ["AABB", "BBAA"],
            "note": "A/B full source에서 AB half 후보를 만든다.",
        },
        {
            "step_index": 2,
            "operation": "cutter",
            "input_slots": ["AABB", "BBAA"],
            "output_slots": ["AB_half", "leftovers"],
            "note": "회전과 절단으로 AB---- half 네 개를 만든다.",
        },
        {
            "step_index": 3,
            "operation": "cutter",
            "input_slots": ["C_full", "C_full"],
            "output_slots": ["CC_half"],
            "note": "C full source 두 개를 ----CC half 네 개로 변환한다.",
        },
        {
            "step_index": 4,
            "operation": "stacker",
            "input_slots": ["AB_half", "CC_half"],
            "output_slots": ["ABCC"],
            "note": "AB half와 CC half를 합쳐 ABCC target 네 개를 만든다.",
        },
    )

    _replace_macro_steps(MacroRecipeStep, checker_macro, checker_steps)
    _replace_macro_steps(MacroRecipeStep, abcc_macro, abcc_steps)


class Migration(migrations.Migration):

    dependencies = [
        ("shapez_solver", "0005_remove_cutter_full_operation"),
    ]

    operations = [
        migrations.RunPython(forwards_seed_pattern_catalog, _noop_reverse),
    ]
