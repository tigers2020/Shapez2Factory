"""GeneSeed admin changelist: seed_miner_patterns button."""

from __future__ import annotations

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import MINER_SEED_SCHEMA_V2
from django_apps.asteroid_lab.models import GeneSeed

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
    url = reverse("admin:asteroid_lab_GeneSeed_changelist")
    response = staff_client.get(url)
    assert response.status_code == 200
    html = response.content.decode()
    assert "Miner seed pattern ingest" in html
    assert "purge_non_seed" in html


@pytest.mark.django_db
def test_genetic_sample_admin_seed_button_runs_command(staff_client: Client) -> None:
    GeneSeed.objects.filter(metadata_json__schema=MINER_SEED_SCHEMA_V2).delete()
    assert not GeneSeed.objects.filter(
        metadata_json__schema=MINER_SEED_SCHEMA_V2,
        metadata_json__is_seed=True,
    ).exists()

    valid_code = open("var/default_miner_pattern.txt", encoding="utf-8").readline().strip()
    GeneSeed.objects.create(
        gene_key="legacy_manual_for_admin",
        name="legacy",
        code=valid_code,
        metadata_json={"note": "manual"},
    )

    url = reverse("admin:asteroid_lab_GeneSeed_seed_miner_patterns")
    response = staff_client.post(
        url,
        {"purge_non_seed": "on", "replace_stale": "on"},
        follow=True,
    )
    assert response.status_code == 200
    html = response.content.decode()
    assert "genetic-sample-mini-map" in html
    assert (
        GeneSeed.objects.filter(
            metadata_json__schema=MINER_SEED_SCHEMA_V2,
            metadata_json__is_seed=True,
        ).count()
        == 18
    )
    assert GeneSeed.objects.filter(gene_key="legacy_manual_for_admin").exists()


@pytest.mark.django_db
def test_genetic_sample_admin_seed_dry_run_no_write(staff_client: Client) -> None:
    before = GeneSeed.objects.count()
    url = reverse("admin:asteroid_lab_GeneSeed_seed_miner_patterns")
    response = staff_client.post(url, {"dry_run": "on"}, follow=True)
    assert response.status_code == 200
    assert GeneSeed.objects.count() == before
    messages = [str(m) for m in response.context["messages"]]
    assert any("dry-run" in m for m in messages)


@pytest.mark.django_db
def test_genetic_sample_changelist_shows_difficulty_columns(staff_client: Client) -> None:
    call_command("seed_miner_patterns")
    url = reverse("admin:asteroid_lab_GeneSeed_changelist")
    response = staff_client.get(url)
    assert response.status_code == 200
    html = response.content.decode()
    assert "Catalog rank" in html
    assert "Intrinsic priority" in html
    assert "Intrinsic difficulty" in html
    assert "Difficulty score" in html


@pytest.mark.django_db
def test_genetic_sample_admin_seed_requires_staff(db) -> None:
    user = User.objects.create_user("plain", password="pass-word-123")
    client = Client()
    client.force_login(user)
    url = reverse("admin:asteroid_lab_GeneSeed_seed_miner_patterns")
    response = client.post(url)
    assert response.status_code in (302, 403)
