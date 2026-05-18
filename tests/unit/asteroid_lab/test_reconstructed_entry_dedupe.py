"""ReconstructedAsteroidEntry rows must survive duplicate cleanup evidence cells."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.adapters.normalization import normalize_decoded_blueprint
from django_apps.asteroid_lab.services.input_service import persist_decoded_snapshot_for_map_input
from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
    persist_reconstructed_asteroid_map,
    run_reconstruction_for_map_input,
)
from django_apps.asteroid_lab.services.reconstructed_map_persist_builder import (
    _dedupe_entry_instances,
    build_entry_instances,
    build_reconstructed_map_persist_payload,
)
from django_apps.asteroid_lab.services.replay_pipeline_service import (
    build_initial_replay_for_map_input,
)

_FIXTURE = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "asteroid_lab"
    / "miner_extension_column_dup_cleanup.txt"
)


@pytest.mark.django_db
def test_dedupe_entry_instances_collapses_identical_keys() -> None:
    ent = m.ReconstructedAsteroidEntry(
        server_x=8,
        server_y=0,
        kind=m.ReconstructedAsteroidEntry.EntryKind.MINER_EXTENSION,
        source=m.ReconstructedAsteroidEntry.EntrySource.CLEANUP_REMOVED,
    )
    rows = _dedupe_entry_instances([ent, ent, ent])
    assert len(rows) == 1


@pytest.mark.django_db
def test_pipeline_persists_map_when_cleanup_has_duplicate_evidence() -> None:
    """Regression: extension-column layouts duplicated cleanup cells → IntegrityError."""

    if not _FIXTURE.is_file():
        pytest.skip("fixture missing")

    copy_code = _FIXTURE.read_text(encoding="utf-8").strip()
    proj = m.AsteroidProject.objects.create(name="Dedupe", slug="recon-entry-dedupe-col")
    inp = m.AsteroidMapInput.objects.create(project=proj, copy_code=copy_code)
    norm = normalize_decoded_blueprint(decode_copy_string(copy_code.removesuffix("$")))
    persist_decoded_snapshot_for_map_input(inp.id, norm)
    inp.refresh_from_db()

    result = build_initial_replay_for_map_input(inp.id, overwrite=True)
    assert result.status == "ok"
    assert result.reconstructed_asteroid_map_id is not None
    row = m.ReconstructedAsteroidMap.objects.get(pk=result.reconstructed_asteroid_map_id)
    n_export = len(row.export_json.get("BP", {}).get("Entries", []))
    assert n_export >= 200
    assert row.entries.count() > 0
    assert len(row.rebuilt_copy_code) > 400
