"""Regression: integration autouse fixtures must enable DB before ORM writes."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.models import GeneticSample


@pytest.mark.django_db
def test_seed_gene_templates_autouse_populates_genetic_sample_rows() -> None:
    """Fails if ``seed_gene_templates_from_exhaustive`` omits the ``db`` fixture."""
    assert GeneticSample.objects.exists()
