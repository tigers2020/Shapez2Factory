"""Game paste export: asteroid fields as Extension only; preserve game ``X`` columns."""

from __future__ import annotations

from pathlib import Path

import pytest

from django_apps.asteroid_lab import models as m
from django_apps.asteroid_lab.adapters.decode_adapter import decode_copy_string
from django_apps.asteroid_lab.adapters.normalization import normalize_decoded_blueprint
from django_apps.asteroid_lab.services.input_service import persist_decoded_snapshot_for_map_input
from django_apps.asteroid_lab.services.reconstructed_map_persist_builder import (
    build_reconstructed_map_persist_payload,
)
from django_apps.asteroid_lab.services.reconstructed_asteroid_service import (
    run_reconstruction_for_map_input,
)


def _entry_xs(entries: list[dict]) -> set[int]:
    return {int(e.get("X", 0)) for e in entries}


@pytest.mark.django_db
def test_miner_t_in_game_coords_exports_extension_and_keeps_x_columns() -> None:
    """Regression: ``Layout_FluidMiner`` field column was re-anchored to 0..N (X gap)."""

    fixture = (
        Path(__file__).resolve().parents[2]
        / "fixtures"
        / "asteroid_lab"
        / "miner_extension_column_dup_cleanup.txt"
    )
    if not fixture.is_file():
        pytest.skip("fixture missing")

    good_code = fixture.read_text(encoding="utf-8").strip()
    good_entries = decode_copy_string(good_code.removesuffix("$")).root["BP"]["Entries"]
    good_xs = _entry_xs(good_entries)

    # Same layout encoded with Miner T (row #3 DB) instead of Extension T.
    miner_entries = [
        {**dict(row), "T": "Layout_FluidMiner"} for row in good_entries if isinstance(row, dict)
    ]
    from django_apps.asteroid_lab.adapters.decode_adapter import encode_copy_string

    miner_code = encode_copy_string(
        {
            "V": 1137,
            "BP": {
                "$type": "Island",
                "Entries": miner_entries,
            },
        }
    )

    proj = m.AsteroidProject.objects.create(name="MinerT", slug="field-export-miner-t")
    inp = m.AsteroidMapInput.objects.create(project=proj, copy_code=miner_code)
    norm = normalize_decoded_blueprint(decode_copy_string(miner_code.removesuffix("$")))
    persist_decoded_snapshot_for_map_input(inp.id, norm)
    inp.refresh_from_db()

    cleanup, recon = run_reconstruction_for_map_input(inp.id)
    payload = build_reconstructed_map_persist_payload(
        map_input_id=inp.id,
        run_key="paste",
        recon=recon,
        cleanup=cleanup,
        source_decoded_json=dict(inp.decoded_json),
    )

    export_entries = payload.export_json["BP"]["Entries"]
    assert len(export_entries) == len(good_entries)
    assert all(str(e.get("T")) == "Layout_FluidMinerExtension" for e in export_entries)
    assert _entry_xs(export_entries) == good_xs

    roundtrip = decode_copy_string(payload.rebuilt_copy_code.removesuffix("$"))
    rt_entries = roundtrip.root["BP"]["Entries"]
    assert all(str(e.get("T")) == "Layout_FluidMinerExtension" for e in rt_entries)
    assert _entry_xs(rt_entries) == good_xs
