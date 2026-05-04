import pytest

from django_apps.shapez_solver.models import MacroRecipe, MacroRecipeStep, PatternFamily
from django_apps.shapez_solver.services.pattern_lab_service import analyze_pattern_lab_shape


@pytest.mark.django_db
def test_pattern_lab_analyzes_signature_without_db_candidates() -> None:
    analysis = analyze_pattern_lab_shape("CuRuSuSu")

    assert analysis.error == ""
    assert analysis.canonical_code == "CuRuSuSu"
    assert analysis.signature == "ABCC"
    assert analysis.inventory_goal_code == "CuRuSuSu"
    assert analysis.inventory_signature == "ABCC"
    assert analysis.target_count == 4
    assert analysis.source_counts == {"CuCuCuCu": 1, "RuRuRuRu": 1, "SuSuSuSu": 2}
    assert analysis.db_candidates == ()
    assert analysis.macro_results == ()


@pytest.mark.django_db
def test_pattern_lab_marks_db_macro_candidate_as_ready_when_strategy_generates() -> None:
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

    analysis = analyze_pattern_lab_shape("CuRuSuSu")

    assert len(analysis.macro_results) == 1
    macro_result = analysis.macro_results[0]
    assert macro_result.candidate.macro_code == "abcc-batch"
    assert macro_result.candidate.steps[0].operation == "stacker"
    assert macro_result.can_generate is True
    assert macro_result.primitive_step_count == 21


@pytest.mark.django_db
def test_pattern_lab_reports_parse_error() -> None:
    analysis = analyze_pattern_lab_shape("bad-code")

    assert analysis.error
    assert analysis.signature == ""
