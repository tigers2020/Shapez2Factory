"""Regression: integration autouse fixtures must enable DB before ORM writes."""

from __future__ import annotations

import pytest

from django_apps.asteroid_lab.genetic_sample.miner_seed_constants import MINER_SEED_SCHEMA_V2
from django_apps.asteroid_lab.models import GeneSeed


@pytest.mark.django_db
def test_seed_miner_patterns_autouse_populates_eighteen_seed_rows() -> None:
    """Fails if ``seed_miner_patterns_db`` omits the ``db`` fixture."""
    assert (
        GeneSeed.objects.filter(
            metadata_json__schema=MINER_SEED_SCHEMA_V2,
            metadata_json__is_seed=True,
        ).count()
        == 18
    )
