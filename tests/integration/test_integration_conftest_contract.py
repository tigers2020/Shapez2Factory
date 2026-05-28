"""Regression: integration autouse fixtures must enable DB before ORM writes."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import MINER_SEED_SCHEMA
from django_apps.asteroid_lab.models import GeneticSample


@pytest.mark.django_db
def test_seed_miner_patterns_autouse_populates_fourteen_seed_rows() -> None:
    """Fails if ``seed_miner_patterns_db`` omits the ``db`` fixture."""
    assert (
        GeneticSample.objects.filter(
            metadata_json__schema=MINER_SEED_SCHEMA,
            metadata_json__is_seed=True,
        ).count()
        == 14
    )
