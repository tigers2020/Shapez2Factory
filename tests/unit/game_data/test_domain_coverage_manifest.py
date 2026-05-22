"""Coverage manifest registry smoke tests."""

from __future__ import annotations

import pytest

from django_apps.game_data.coverage.disposition import Disposition
from django_apps.game_data.coverage.manifest import MANIFEST


@pytest.mark.parametrize("key", list(MANIFEST.keys()))
def test_manifest_entry_has_disposition_and_note(key: str) -> None:
    disposition, note = MANIFEST[key]
    assert disposition in Disposition
    assert note.strip()


def test_manifest_simulation_rules_have_unique_suffix() -> None:
    sim_keys = [k for k in MANIFEST if k.startswith("simulation_systems.json:")]
    suffixes = [k.split(":", 1)[1] for k in sim_keys]
    assert len(suffixes) == len(set(suffixes))
