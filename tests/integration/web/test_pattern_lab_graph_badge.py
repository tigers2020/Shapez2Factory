"""Pattern Lab shows graph_document-derived step badge when applicable."""

from django.test import Client
from django.urls import reverse

from django_apps.shapez_solver.models import MacroRecipe, MacroRecipeStep, PatternFamily


def test_pattern_lab_shows_graph_step_badge_for_graph_document_recipe(db) -> None:
    family = PatternFamily.objects.create(
        code="abcc",
        name="ABCC",
        signature="ABCC",
    )
    graph_doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s_in",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {
                "id": "o_rot",
                "kind": "operation",
                "operation": "rotate_cw",
                "x": 200,
                "y": 0,
            },
            {
                "id": "s_out",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 400,
                "y": 0,
            },
        ],
        "edges": [
            {"from": "s_in", "to": "o_rot", "kind": "input"},
            {"from": "o_rot", "to": "s_out", "kind": "output", "slot": "0"},
        ],
    }
    MacroRecipe.objects.create(
        family=family,
        code="graph-only-lab",
        strategy_code="ABCC_BATCH",
        name="Graph badge",
        estimated_operation_cost=1,
        graph_document=graph_doc,
    )
    MacroRecipeStep.objects.create(
        macro=MacroRecipe.objects.get(code="graph-only-lab"),
        step_index=1,
        operation="stacker",
        input_slots=["x"],
        output_slots=["y"],
        note="db",
    )

    response = Client().get(reverse("web:pattern-lab"), {"code": "CuRuSuSu"})
    assert response.status_code == 200
    content = response.content.decode()
    assert "Steps from graph_document" in content
    assert "graph-only-lab" in content
