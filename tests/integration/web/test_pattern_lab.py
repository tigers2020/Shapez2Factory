from django.test import Client
from django.urls import reverse

from django_apps.shapez_solver.models import MacroRecipe, MacroRecipeStep, PatternFamily


def test_pattern_lab_page_renders_empty_state() -> None:
    response = Client().get(reverse("web:pattern-lab"))

    assert response.status_code == 200
    content = response.content.decode()
    assert "Pattern Lab" in content
    assert "Enter a shape code" in content


def test_pattern_lab_page_shows_ready_macro_candidate(db) -> None:
    family = PatternFamily.objects.create(
        code="abcc",
        name="ABCC",
        signature="ABCC",
    )
    macro = MacroRecipe.objects.create(
        family=family,
        code="abcc-batch",
        strategy_code="ABCC_BATCH",
        name="ABCC Batch",
        estimated_operation_cost=21,
    )
    MacroRecipeStep.objects.create(
        macro=macro,
        step_index=1,
        operation="stacker",
        input_slots=["AB_half", "CC_half"],
        output_slots=["ABCC"],
        note="표시용 step",
    )

    response = Client().get(reverse("web:pattern-lab"), {"code": "CuRuSuSu"})

    assert response.status_code == 200
    content = response.content.decode()
    assert "CuRuSuSu" in content
    assert "ABCC_BATCH" in content
    assert "ready" in content
    assert "stacker" in content
    assert "AB_half" in content
