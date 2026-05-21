"""Bounded-context browse dashboard and aggregate-root admin contracts."""

from __future__ import annotations

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from django_apps.game_data.browse.registry import (
    AGGREGATE_ROOT_SPECS,
    admin_inline_class_names,
    build_browse_groups,
    validate_aggregate_root_inlines,
    validate_section_admin_targets,
)
from django_apps.game_data.models.taxonomy import GameDataNamespace, GameDataSection

User = get_user_model()


@pytest.fixture
def staff_client(db) -> Client:
    user = User.objects.create_user(
        username="gd_staff",
        password="pass-word-123",
        is_staff=True,
        is_superuser=True,
    )
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_game_data_browse_groups_sections_by_namespace(staff_client: Client) -> None:
    if not GameDataNamespace.objects.exists():
        pytest.skip("taxonomy not seeded (run game_data migrations)")

    url = reverse("game_data_browse:index")
    response = staff_client.get(url)
    assert response.status_code == 200
    groups = build_browse_groups()
    assert groups, "expected seeded namespaces"
    assert response.context["groups"]
    first = groups[0]
    assert first.sections, "namespace must expose sections"
    assert all(s.namespace_code == first.code for s in first.sections)
    html = response.content.decode()
    assert first.label in html
    assert first.sections[0].section_label in html


@pytest.mark.django_db
def test_every_game_data_section_has_admin_target() -> None:
    if not GameDataSection.objects.exists():
        pytest.skip("taxonomy not seeded")
    errors = validate_section_admin_targets()
    assert errors == [], "\n".join(errors)


@pytest.mark.django_db
@pytest.mark.parametrize("spec", AGGREGATE_ROOT_SPECS, ids=lambda s: s.model_label)
def test_aggregate_root_admin_exposes_expected_subtables(spec) -> None:
    errors = validate_aggregate_root_inlines()
    model_errors = [e for e in errors if e.startswith(spec.model_label)]
    assert model_errors == [], "\n".join(model_errors)

    app_label, model_name = spec.model_label.split(".", 1)
    from django.apps import apps

    model = apps.get_model(app_label, model_name)
    model_admin = admin.site._registry[model]
    present = admin_inline_class_names(model_admin)
    assert spec.inline_class_names <= present
    assert hasattr(model_admin, "game_data_related_changelists")


@pytest.mark.django_db
def test_build_browse_marks_aggregate_roots() -> None:
    if not GameDataNamespace.objects.exists():
        pytest.skip("taxonomy not seeded")
    labels = {
        row.model_label
        for group in build_browse_groups()
        for row in group.sections
        if row.is_aggregate_root
    }
    assert "game_data.BuildingGroup" in labels
    assert "game_data.SimulationSystem" in labels
