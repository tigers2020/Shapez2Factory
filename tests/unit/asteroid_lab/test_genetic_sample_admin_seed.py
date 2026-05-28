"""GeneticSample admin changelist: seed_miner_patterns button."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import MINER_SEED_SCHEMA
from django_apps.asteroid_lab.models import GeneticSample

User = get_user_model()


@pytest.fixture
def staff_client(db) -> Client:
    user = User.objects.create_user(
        username="gs_admin_staff",
        password="pass-word-123",
        is_staff=True,
        is_superuser=True,
    )
    client = Client()
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_genetic_sample_changelist_shows_seed_form(staff_client: Client) -> None:
    url = reverse("admin:asteroid_lab_geneticsample_changelist")
    response = staff_client.get(url)
    assert response.status_code == 200
    html = response.content.decode()
    assert "Miner seed pattern ingest" in html


@pytest.mark.django_db
def test_genetic_sample_admin_seed_button_runs_command(staff_client: Client) -> None:
    GeneticSample.objects.filter(metadata_json__schema=MINER_SEED_SCHEMA).delete()
    assert not GeneticSample.objects.filter(
        metadata_json__schema=MINER_SEED_SCHEMA,
        metadata_json__is_seed=True,
    ).exists()

    url = reverse("admin:asteroid_lab_geneticsample_seed_miner_patterns")
    response = staff_client.post(url, follow=True)
    assert response.status_code == 200
    assert (
        GeneticSample.objects.filter(
            metadata_json__schema=MINER_SEED_SCHEMA,
            metadata_json__is_seed=True,
        ).count()
        == 14
    )


@pytest.mark.django_db
def test_genetic_sample_admin_seed_dry_run_no_write(staff_client: Client) -> None:
    before = GeneticSample.objects.count()
    url = reverse("admin:asteroid_lab_geneticsample_seed_miner_patterns")
    response = staff_client.post(url, {"dry_run": "on"}, follow=True)
    assert response.status_code == 200
    assert GeneticSample.objects.count() == before
    messages = [str(m) for m in response.context["messages"]]
    assert any("dry-run" in m for m in messages)


@pytest.mark.django_db
def test_genetic_sample_admin_seed_requires_staff(db) -> None:
    user = User.objects.create_user("plain", password="pass-word-123")
    client = Client()
    client.force_login(user)
    url = reverse("admin:asteroid_lab_geneticsample_seed_miner_patterns")
    response = client.post(url)
    assert response.status_code in (302, 403)
