import pytest

from django_apps.shapez_solver.models import MacroRecipe, MacroRecipeStep, PatternFamily
from django_apps.shapez_solver.services.macro_recipe_staff_catalog import (
    apply_graph_derived_catalog_fields,
    create_draft_macro_recipe,
    create_recipe,
    delete_recipe,
    sync_macro_recipe_steps_from_graph_document,
    update_recipe,
)


@pytest.mark.django_db
def test_build_catalog_snapshot_includes_operation_icon_urls() -> None:
    from django_apps.shapez_solver.services.macro_recipe_staff_catalog import (
        build_catalog_snapshot,
    )

    snap = build_catalog_snapshot()
    ops = snap.get("operations")
    assert isinstance(ops, list) and len(ops) >= 1
    by_val = {o["value"]: o for o in ops if isinstance(o, dict)}
    assert "cutter" in by_val
    assert by_val["cutter"].get("icon", "").endswith("cutter.png")
    assert by_val["cutter"]["icon"].startswith("/static/")


@pytest.mark.django_db
def test_create_recipe_with_steps() -> None:
    family = PatternFamily.objects.create(
        code="test-fam",
        name="Test",
        signature="ABCC",
    )
    recipe = create_recipe(
        {
            "family_id": family.id,
            "code": "test-macro",
            "strategy_code": "ABCC_BATCH",
            "name": "Test macro",
            "estimated_operation_cost": 3,
            "estimated_stage_cost": 3,
            "estimated_waste_cost": 0,
            "priority": 50,
            "is_active": True,
            "schema_version": 1,
            "steps": [
                {
                    "step_index": 1,
                    "operation": "stacker",
                    "input_slots": ["a"],
                    "output_slots": ["b"],
                    "note": "n",
                }
            ],
        }
    )
    assert recipe.code == "test-macro"
    assert recipe.steps.count() == 1
    step = recipe.steps.get()
    assert step.operation == "stacker"
    assert recipe.graph_document is not None
    assert recipe.graph_document["nodes"] == []
    assert recipe.graph_document["edges"] == []


@pytest.mark.django_db
def test_update_recipe_replaces_steps() -> None:
    family = PatternFamily.objects.create(code="f", name="F", signature="ABCC")
    recipe = MacroRecipe.objects.create(
        family=family,
        code="r1",
        strategy_code="ABCC_BATCH",
        name="R1",
    )
    MacroRecipeStep.objects.create(
        macro=recipe,
        step_index=1,
        operation="cutter",
        input_slots=[],
        output_slots=[],
        note="",
    )
    updated = update_recipe(
        recipe.id,
        {
            "steps": [
                {
                    "step_index": 1,
                    "operation": "splitter",
                    "input_slots": ["x"],
                    "output_slots": ["y"],
                    "note": "",
                }
            ]
        },
    )
    assert updated.steps.count() == 1
    assert updated.steps.get().operation == "splitter"


@pytest.mark.django_db
def test_delete_recipe() -> None:
    family = PatternFamily.objects.create(code="f2", name="F2", signature="ABCC")
    recipe = MacroRecipe.objects.create(
        family=family,
        code="to-del",
        strategy_code="ABCC_BATCH",
        name="Del",
    )
    delete_recipe(recipe.id)
    assert MacroRecipe.objects.filter(pk=recipe.id).count() == 0


@pytest.mark.django_db
def test_serialize_recipe_includes_pattern_lab_steps_from_graph_document() -> None:
    from django_apps.shapez_solver.services.macro_recipe_staff_catalog import serialize_recipe

    family = PatternFamily.objects.create(code="fam-pl", name="PL", signature="PLSIG")
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
    recipe = MacroRecipe.objects.create(
        family=family,
        code="pl-steps",
        strategy_code="ABCC_BATCH",
        name="PL steps",
        graph_document=graph_doc,
    )
    MacroRecipeStep.objects.create(
        macro=recipe,
        step_index=1,
        operation="stacker",
        input_slots=["a"],
        output_slots=["b"],
        note="db",
    )
    data = serialize_recipe(recipe)
    assert data["pattern_lab_steps"] is not None
    assert data["pattern_lab_steps"][0]["operation"] == "rotate_cw"
    assert data["steps"][0]["operation"] == "stacker"


@pytest.mark.django_db
def test_sync_macro_recipe_steps_from_graph_document_replaces_db_steps() -> None:
    family = PatternFamily.objects.create(code="sync-fam", name="S", signature="ABCC")
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
    recipe = MacroRecipe.objects.create(
        family=family,
        code="sync-graph",
        strategy_code="ABCC_BATCH",
        name="Sync",
    )
    MacroRecipeStep.objects.create(
        macro=recipe,
        step_index=1,
        operation="stacker",
        input_slots=["a"],
        output_slots=["b"],
        note="old",
    )
    assert sync_macro_recipe_steps_from_graph_document(recipe, graph_doc) is True
    recipe.refresh_from_db()
    assert recipe.steps.count() == 1
    step = recipe.steps.get()
    assert step.operation == "rotate_cw"
    assert step.note.startswith("graph:o_rot")


@pytest.mark.django_db
def test_sync_macro_recipe_steps_from_graph_document_noop_when_underivable() -> None:
    family = PatternFamily.objects.create(code="noderive", name="N", signature="ABCC")
    recipe = MacroRecipe.objects.create(
        family=family,
        code="no-derive",
        strategy_code="ABCC_BATCH",
        name="N",
    )
    MacroRecipeStep.objects.create(
        macro=recipe,
        step_index=1,
        operation="cutter",
        input_slots=[],
        output_slots=[],
        note="keep",
    )
    graph_only_shape = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s1",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
        ],
        "edges": [],
    }
    assert sync_macro_recipe_steps_from_graph_document(recipe, graph_only_shape) is False
    assert recipe.steps.count() == 1
    assert recipe.steps.get().operation == "cutter"


@pytest.mark.django_db
def test_create_draft_macro_recipe_assigns_graph_draft_family() -> None:
    draft = create_draft_macro_recipe(name="Hello")
    assert draft.family.code == "graph-draft"
    assert draft.code.startswith("m-")
    assert draft.name == "Hello"
    assert draft.graph_document is not None
    assert draft.graph_document["nodes"] == []
    assert draft.graph_document["edges"] == []


@pytest.mark.django_db
def test_apply_graph_derived_catalog_fields_scales_with_operations() -> None:
    family = PatternFamily.objects.create(code="pf-pri", name="P", signature="SIG")
    macro = MacroRecipe.objects.create(
        family=family,
        code="pri-mac",
        strategy_code="ABCC_BATCH",
        name="P",
        priority=10,
    )
    empty_doc: dict[str, object] = {"schema_version": 1, "nodes": [], "edges": []}
    apply_graph_derived_catalog_fields(macro, empty_doc)
    macro.refresh_from_db()
    base_pri = macro.priority
    one_op = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {"id": "o", "kind": "operation", "operation": "rotate_cw", "x": 1, "y": 0},
        ],
        "edges": [],
    }
    apply_graph_derived_catalog_fields(macro, one_op)
    macro.refresh_from_db()
    assert macro.estimated_operation_cost == 1
    assert macro.priority > base_pri


@pytest.mark.django_db
def test_update_recipe_applies_derivation_when_graph_document_in_payload() -> None:
    family = PatternFamily.objects.create(code="up-g", name="U", signature="ABCC")
    graph_doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "s1",
                "kind": "shape",
                "role": "source",
                "shape_code": "CuCuCuCu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
            {"id": "o1", "kind": "operation", "operation": "rotate_cw", "x": 100, "y": 0},
            {
                "id": "s2",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 200,
                "y": 0,
            },
        ],
        "edges": [
            {"from": "s1", "to": "o1", "kind": "input"},
            {"from": "o1", "to": "s2", "kind": "output", "slot": "0"},
        ],
    }
    recipe = MacroRecipe.objects.create(
        family=family,
        code="up-g",
        strategy_code="ABCC_BATCH",
        name="U",
        estimated_operation_cost=99,
        priority=1,
    )
    update_recipe(recipe.id, {"graph_document": graph_doc})
    recipe.refresh_from_db()
    assert recipe.estimated_operation_cost == 1
    assert recipe.priority > 1
