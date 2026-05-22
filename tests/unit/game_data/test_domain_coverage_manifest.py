"""Coverage manifest registry smoke tests."""

from __future__ import annotations

import pytest

from django_apps.game_data.coverage.manifest import MANIFEST, Disposition


@pytest.mark.parametrize("key", list(MANIFEST.keys()))
def test_manifest_entry_has_disposition_and_note(key: str) -> None:
    disposition, note = MANIFEST[key]
    assert disposition in Disposition
    assert note.strip()
