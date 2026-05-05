import json

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from django_apps.shapez_solver.models import MacroRecipe, PatternFamily
from django_apps.shapez_solver.services.recipe_graph_react_flow_adapter import (
    domain_graph_to_react_flow,
)
from django_apps.shapez_solver.services.recipe_graph_recompute import validate_graph_document


@pytest.mark.django_db
def test_macro_pattern_staff_redirects_anonymous() -> None:
    client = Client()
    response = client.get(reverse("web:macro-pattern-staff"))
    assert response.status_code == 302
    assert "/accounts/login/" in response["Location"]


@pytest.mark.django_db
def test_macro_pattern_staff_forbidden_non_staff() -> None:
    User = get_user_model()
    user = User.objects.create_user("u1", "u1@example.com", "pw", is_staff=False)
    client = Client()
    client.force_login(user)
    response = client.get(reverse("web:macro-pattern-staff"))
    assert response.status_code == 403


@pytest.mark.django_db
def test_macro_pattern_new_post_creates_draft_and_redirects_to_graph() -> None:
    User = get_user_model()
    user = User.objects.create_user("staff_new", "sn@example.com", "pw", is_staff=True)
    client = Client()
    client.force_login(user)
    response = client.post(
        reverse("web:macro-pattern-new"),
        data={"name": "My draft"},
    )
    assert response.status_code == 302
    recipe = MacroRecipe.objects.get(name="My draft")
    assert recipe.family.code == "graph-draft"
    assert str(recipe.pk) in response["Location"]


@pytest.mark.django_db
def test_macro_pattern_list_page_staff_ok() -> None:
    User = get_user_model()
    user = User.objects.create_user("admin", "a@example.com", "pw", is_staff=True)
    client = Client()
    client.force_login(user)
    response = client.get(reverse("web:macro-pattern-staff"))
    assert response.status_code == 200
    body = response.content.decode()
    assert "Macro pattern catalog" in body
    assert "macro_pattern_list.js?v=" in body
    assert "Macro catalog" in body or "macro" in body.lower()


@pytest.mark.django_db
def test_macro_pattern_graph_page_staff_ok() -> None:
    User = get_user_model()
    user = User.objects.create_user("gstaff", "gs@example.com", "pw", is_staff=True)
    family = PatternFamily.objects.create(code="fam-gp", name="GP", signature="ABCC")
    recipe = MacroRecipe.objects.create(
        family=family,
        code="graph-page",
        strategy_code="ABCC_BATCH",
        name="Graph page",
    )
    client = Client()
    client.force_login(user)
    response = client.get(reverse("web:macro-pattern-graph", kwargs={"pk": recipe.pk}))
    assert response.status_code == 200
    body = response.content.decode()
    assert "macro-graph-bootstrap" in body
    assert "recipe-graph-editor.js?v=" in body
    assert "recipe-graph-editor.css?v=" in body
    assert "macro-graph-editor-root" in body
    assert "staff_catalog_url" in body
    assert "react_flow_initial" in body
    assert "react_flow_initial_status" in body
    assert "macro_step_count" in body


@pytest.mark.django_db
def test_macro_pattern_staff_api_crud() -> None:
    User = get_user_model()
    user = User.objects.create_user("staff", "s@example.com", "pw", is_staff=True)
    family = PatternFamily.objects.create(code="fam-x", name="Fam", signature="ABCC")
    client = Client()
    client.force_login(user)

    catalog = client.get(reverse("web:macro-pattern-staff-api-catalog"))
    assert catalog.status_code == 200
    assert "strategy_codes" in catalog.json()

    create_payload = {
        "family_id": family.id,
        "code": "api-test-macro",
        "strategy_code": "ABCC_BATCH",
        "name": "API test",
        "estimated_operation_cost": 2,
        "estimated_stage_cost": 2,
        "estimated_waste_cost": 0,
        "priority": 77,
        "is_active": True,
        "schema_version": 1,
        "steps": [
            {
                "step_index": 1,
                "operation": "stacker",
                "input_slots": ["i"],
                "output_slots": ["o"],
                "note": "",
            }
        ],
    }
    created = client.post(
        reverse("web:macro-pattern-staff-api-recipes-create"),
        data=json.dumps(create_payload),
        content_type="application/json",
    )
    assert created.status_code == 200
    rid = created.json()["recipe"]["id"]

    detail_get = client.get(
        reverse("web:macro-pattern-staff-api-recipe-detail", kwargs={"pk": rid}),
    )
    assert detail_get.status_code == 200
    assert detail_get.json()["recipe"]["code"] == "api-test-macro"

    patch = client.patch(
        reverse("web:macro-pattern-staff-api-recipe-detail", kwargs={"pk": rid}),
        data=json.dumps({"name": "Renamed"}),
        content_type="application/json",
    )
    assert patch.status_code == 200
    assert patch.json()["recipe"]["name"] == "Renamed"

    deleted = client.delete(
        reverse("web:macro-pattern-staff-api-recipe-detail", kwargs={"pk": rid}),
    )
    assert deleted.status_code == 200
    assert MacroRecipe.objects.filter(pk=rid).count() == 0


@pytest.mark.django_db
def test_macro_pattern_staff_graph_recompute_api() -> None:
    User = get_user_model()
    user = User.objects.create_user("staff2", "s2@example.com", "pw", is_staff=True)
    family = PatternFamily.objects.create(code="fam-g", name="G", signature="ABCC")
    recipe = MacroRecipe.objects.create(
        family=family,
        code="graph-api",
        strategy_code="ABCC_BATCH",
        name="Graph API",
    )
    client = Client()
    client.force_login(user)
    graph = {
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
            {"from": "o1", "to": "s2", "kind": "output"},
        ],
    }
    url = reverse(
        "web:macro-pattern-staff-api-recipe-graph-recompute",
        kwargs={"pk": recipe.id},
    )
    dry = client.post(
        url,
        data=json.dumps({"graph_document": graph}),
        content_type="application/json",
    )
    assert dry.status_code == 200
    data = dry.json()
    assert data["ok"] is True
    assert data.get("react_flow") is not None
    assert data["react_flow"].get("version") == 1
    assert len(data["react_flow"].get("nodes", [])) == 3
    assert data.get("steps_synced") is False
    assert data.get("graph_cost_hint", {}).get("operation_node_count") == 1
    assert data.get("graph_linear_operation_sequence") == ["rotate_cw"]
    assert "validation" in data
    assert "issues" in data["validation"]
    assert "ok" in data["validation"]
    assert data.get("visual_graph") is not None
    assert len(data["visual_graph"]["nodes"]) >= 3
    s2_node = next(n for n in data["graph_document"]["nodes"] if n["id"] == "s2")
    assert s2_node.get("shape_code")

    rf_payload = domain_graph_to_react_flow(validate_graph_document(graph))
    dry_rf = client.post(
        url,
        data=json.dumps({"react_flow": rf_payload}),
        content_type="application/json",
    )
    assert dry_rf.status_code == 200
    rf_data = dry_rf.json()
    assert rf_data["ok"] is True
    assert validate_graph_document(rf_data["graph_document"]) == validate_graph_document(
        data["graph_document"]
    )
    assert rf_data.get("react_flow") is not None

    committed = client.post(
        url,
        data=json.dumps({"graph_document": graph, "commit": True}),
        content_type="application/json",
    )
    assert committed.status_code == 200
    cdata = committed.json()
    assert cdata.get("react_flow") is not None
    assert cdata.get("steps_synced") is True
    recipe.refresh_from_db()
    assert recipe.graph_document is not None
    assert recipe.graph_document["schema_version"] == 1
    assert recipe.steps.count() == 1
    assert recipe.steps.get().operation == "rotate_cw"
    assert recipe.estimated_operation_cost == 1
    assert recipe.estimated_stage_cost >= 1
    assert recipe.priority > 100

    cat2 = client.get(reverse("web:macro-pattern-staff-api-catalog"))
    assert cat2.status_code == 200
    recipes = cat2.json()["recipes"]
    row = next(r for r in recipes if r["id"] == recipe.id)
    assert row.get("visual_graph") is not None
    assert len(row["visual_graph"]["nodes"]) >= 3
    assert row["steps"][0]["operation"] == "rotate_cw"


@pytest.mark.django_db
def test_macro_pattern_staff_graph_recompute_rejects_both_payloads() -> None:
    User = get_user_model()
    user = User.objects.create_user("staffboth", "sb@example.com", "pw", is_staff=True)
    family = PatternFamily.objects.create(code="fam-both", name="Both", signature="ABCC")
    recipe = MacroRecipe.objects.create(
        family=family,
        code="both-payload",
        strategy_code="ABCC_BATCH",
        name="Both payload",
    )
    graph = {
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
            {"id": "o1", "kind": "operation", "operation": "rotate_cw", "x": 1, "y": 0},
            {
                "id": "s2",
                "kind": "shape",
                "role": "intermediate",
                "shape_code": "",
                "quantity": 1,
                "x": 2,
                "y": 0,
            },
        ],
        "edges": [
            {"from": "s1", "to": "o1", "kind": "input"},
            {"from": "o1", "to": "s2", "kind": "output"},
        ],
    }
    rf_payload = domain_graph_to_react_flow(validate_graph_document(graph))
    client = Client()
    client.force_login(user)
    url = reverse(
        "web:macro-pattern-staff-api-recipe-graph-recompute",
        kwargs={"pk": recipe.id},
    )
    res = client.post(
        url,
        data=json.dumps({"graph_document": graph, "react_flow": rf_payload}),
        content_type="application/json",
    )
    assert res.status_code == 400
    body = res.json()
    assert body.get("ok") is False
    assert "only one" in (body.get("error") or "").lower()
