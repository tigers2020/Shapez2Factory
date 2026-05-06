from unittest.mock import patch

import pytest
from django.test.utils import override_settings

from django_apps.shapez_solver.models import (
    MacroRecipe,
    MacroRecipeCompiledBoundary,
    MacroRecipeStep,
    PatternFamily,
)
from django_apps.shapez_solver.services.macro_recipe_staff_catalog import (
    apply_graph_derived_catalog_fields,
    create_draft_macro_recipe,
    create_recipe,
    delete_recipe,
    sync_macro_recipe_steps_from_graph_document,
    update_recipe,
)
from django_apps.web.services.graph_preview import PlaywrightPngGraphPreviewRenderer


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
def test_build_catalog_snapshot_default_skips_png_generation(tmp_path) -> None:
    """Catalog lists many recipes; sync Playwright would time out in production."""
    from django_apps.shapez_solver.services.macro_recipe_staff_catalog import (
        build_catalog_snapshot,
    )

    family = PatternFamily.objects.create(code="cat-fam", name="C", signature="ABCC")
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
        ],
        "edges": [],
    }
    MacroRecipe.objects.create(
        family=family,
        code="cat-mac",
        strategy_code="ABCC_BATCH",
        name="Cat",
        graph_document=graph_doc,
    )
    with override_settings(
        SOLVER_GRAPH_PREVIEW_RENDERER="playwright_png",
        SOLVER_GRAPH_PREVIEW_CACHE_DIR=str(tmp_path),
    ):
        with patch.object(
            PlaywrightPngGraphPreviewRenderer,
            "_generate_and_store",
            autospec=True,
        ) as mock_gen:
            snap = build_catalog_snapshot()
            mock_gen.assert_not_called()
    recipes = snap.get("recipes")
    assert isinstance(recipes, list)
    by_code = {r["code"]: r for r in recipes if isinstance(r, dict)}
    cat = by_code["cat-mac"]
    vg = cat.get("visual_graph")
    assert isinstance(vg, dict)
    shape_nodes = [n for n in vg["nodes"] if n.get("kind") == "shape" and n.get("shape_code")]
    assert shape_nodes and shape_nodes[0].get("needs_warm") is not True
    assert isinstance(shape_nodes[0].get("preview_scene"), dict)


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
    assert recipe.compiled_boundaries.count() == 0


@pytest.mark.django_db
def test_apply_graph_derived_catalog_fields_syncs_compiled_boundaries() -> None:
    family = PatternFamily.objects.create(code="cb-f", name="CB", signature="ABCC")
    macro = MacroRecipe.objects.create(
        family=family,
        code="cb-mac",
        strategy_code="ABCC_BATCH",
        name="CB",
    )
    doc = {
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
            {
                "id": "t1",
                "kind": "shape",
                "role": "target",
                "shape_code": "CuRuSuSu",
                "quantity": 1,
                "x": 100,
                "y": 0,
            },
        ],
        "edges": [],
    }
    apply_graph_derived_catalog_fields(macro, doc)
    rows = list(macro.compiled_boundaries.order_by("boundary", "graph_shape_id"))
    assert len(rows) == 2
    assert {(r.graph_shape_id, r.pattern_signature, r.boundary) for r in rows} == {
        ("s1", "AAAA", MacroRecipeCompiledBoundary.Boundary.START),
        ("t1", "ABCC", MacroRecipeCompiledBoundary.Boundary.END),
    }


@pytest.mark.django_db
def test_serialize_recipe_includes_compiled_boundaries() -> None:
    from django_apps.shapez_solver.services.macro_recipe_staff_catalog import serialize_recipe

    family = PatternFamily.objects.create(code="cb-ser", name="S", signature="ABCC")
    macro = MacroRecipe.objects.create(
        family=family,
        code="cb-ser-mac",
        strategy_code="ABCC_BATCH",
        name="S",
    )
    doc = {
        "schema_version": 1,
        "nodes": [
            {
                "id": "t1",
                "kind": "shape",
                "role": "target",
                "shape_code": "CuRuSuSu",
                "quantity": 1,
                "x": 0,
                "y": 0,
            },
        ],
        "edges": [],
    }
    apply_graph_derived_catalog_fields(macro, doc)
    macro.refresh_from_db()
    data = serialize_recipe(macro)
    assert len(data["compiled_boundaries"]) == 1
    assert data["compiled_boundaries"][0]["graph_shape_id"] == "t1"
    assert data["compiled_boundaries"][0]["pattern_signature"] == "ABCC"
    assert data["compiled_boundaries"][0]["boundary"] == MacroRecipeCompiledBoundary.Boundary.END


@pytest.mark.django_db
def test_compiled_boundaries_sink_intermediate_is_end_without_explicit_target() -> None:
    family = PatternFamily.objects.create(code="sink-f", name="Sink", signature="ABCC")
    macro = MacroRecipe.objects.create(
        family=family,
        code="sink-mac",
        strategy_code="ABCC_BATCH",
        name="Sink",
    )
    doc = {
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
                "id": "im1",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "CuRuSuSu",
                "quantity": 1,
                "x": 200,
                "y": 0,
            },
        ],
        "edges": [
            {"from": "s1", "to": "o1", "kind": "input"},
            {"from": "o1", "to": "im1", "kind": "output", "slot": "0"},
        ],
    }
    apply_graph_derived_catalog_fields(macro, doc)
    ends = list(macro.compiled_boundaries.filter(boundary=MacroRecipeCompiledBoundary.Boundary.END))
    assert len(ends) == 1
    assert ends[0].graph_shape_id == "im1"
    assert ends[0].pattern_signature == "ABCC"


@pytest.mark.django_db
def test_compiled_boundaries_sink_loses_end_when_wired_to_next_operation() -> None:
    family = PatternFamily.objects.create(code="chain-f", name="Chain", signature="ABCC")
    macro = MacroRecipe.objects.create(
        family=family,
        code="chain-mac",
        strategy_code="ABCC_BATCH",
        name="Chain",
    )
    doc = {
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
                "id": "im1",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "CuRuSuSu",
                "quantity": 1,
                "x": 200,
                "y": 0,
            },
            {"id": "o2", "kind": "operation", "operation": "rotate_ccw", "x": 300, "y": 0},
            {
                "id": "im2",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "CuRuSuSu",
                "quantity": 1,
                "x": 400,
                "y": 0,
            },
        ],
        "edges": [
            {"from": "s1", "to": "o1", "kind": "input"},
            {"from": "o1", "to": "im1", "kind": "output", "slot": "0"},
            {"from": "im1", "to": "o2", "kind": "input"},
            {"from": "o2", "to": "im2", "kind": "output", "slot": "0"},
        ],
    }
    apply_graph_derived_catalog_fields(macro, doc)
    ends = {r.graph_shape_id for r in macro.compiled_boundaries.filter(boundary="end")}
    assert "im1" not in ends
    assert "im2" in ends


@pytest.mark.django_db
def test_compiled_boundaries_delivery_source_intermediate_not_end_target_only() -> None:
    family = PatternFamily.objects.create(code="del-f", name="Del", signature="ABCC")
    macro = MacroRecipe.objects.create(
        family=family,
        code="del-mac",
        strategy_code="ABCC_BATCH",
        name="Del",
    )
    doc = {
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
                "id": "im1",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "CuRuSuSu",
                "quantity": 1,
                "x": 200,
                "y": 0,
            },
            {
                "id": "t1",
                "kind": "shape",
                "role": "target",
                "shape_code": "CuRuSuSu",
                "quantity": 1,
                "x": 300,
                "y": 0,
            },
        ],
        "edges": [
            {"from": "s1", "to": "o1", "kind": "input"},
            {"from": "o1", "to": "im1", "kind": "output", "slot": "0"},
            {"from": "im1", "to": "t1", "kind": "delivery"},
        ],
    }
    apply_graph_derived_catalog_fields(macro, doc)
    ends = list(macro.compiled_boundaries.filter(boundary=MacroRecipeCompiledBoundary.Boundary.END))
    assert len(ends) == 1
    assert ends[0].graph_shape_id == "t1"


@pytest.mark.django_db
def test_compiled_boundaries_end_rows_capped_at_four() -> None:
    from django_apps.shapez_solver.services.macro_recipe_compiled_boundary import (
        MAX_COMPILED_END_BOUNDARIES,
    )

    family = PatternFamily.objects.create(code="cap-f", name="Cap", signature="ABCC")
    macro = MacroRecipe.objects.create(
        family=family,
        code="cap-mac",
        strategy_code="ABCC_BATCH",
        name="Cap",
    )
    nodes = [
        {
            "id": "end-e",
            "kind": "shape",
            "role": "target",
            "shape_code": "CuRuSuSu",
            "quantity": 1,
            "x": 0,
            "y": 0,
        },
        {
            "id": "end-d",
            "kind": "shape",
            "role": "target",
            "shape_code": "CuRuSuSu",
            "quantity": 1,
            "x": 50,
            "y": 0,
        },
        {
            "id": "end-c",
            "kind": "shape",
            "role": "target",
            "shape_code": "CuRuSuSu",
            "quantity": 1,
            "x": 100,
            "y": 0,
        },
        {
            "id": "end-b",
            "kind": "shape",
            "role": "target",
            "shape_code": "CuRuSuSu",
            "quantity": 1,
            "x": 150,
            "y": 0,
        },
        {
            "id": "end-a",
            "kind": "shape",
            "role": "target",
            "shape_code": "CuRuSuSu",
            "quantity": 1,
            "x": 200,
            "y": 0,
        },
    ]
    doc = {"schema_version": 1, "nodes": nodes, "edges": []}
    apply_graph_derived_catalog_fields(macro, doc)
    ends = list(macro.compiled_boundaries.filter(boundary=MacroRecipeCompiledBoundary.Boundary.END))
    assert len(ends) == MAX_COMPILED_END_BOUNDARIES
    chosen = sorted(r.graph_shape_id for r in ends)
    assert chosen == ["end-a", "end-b", "end-c", "end-d"]


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
